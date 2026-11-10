"""Artifact separation and guarded helper integration on synthetic, audit-local fixtures."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from test_review_isolation import snapshot

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT/'scripts/review_artifacts.py'
ISOLATE = ROOT/'skills/peer-review/scripts/isolated-workspace.sh'


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='grimoire-artifacts-')
        self.addCleanup(self.temp.cleanup)
        self.outer=Path(self.temp.name).resolve();self.repo=self.outer/'audit';self.repo.mkdir()
        self.sid='codex-artifact-1234'
        self.env=dict(os.environ,GRIMOIRE_SESSION_ID=self.sid,GRIMOIRE_AUDIT_ROOT=str(self.repo),GIT_OPTIONAL_LOCKS='0')
        self.git('init','-q')
        (self.repo/'src').mkdir()
        self.source=self.repo/'src/Fixture.sol'
        self.source.write_text('pragma solidity ^0.8.0;\ncontract Fixture { uint value = 1; }\n')
        (self.repo/'foundry.toml').write_text('[profile.default]\nsrc = "src"\ntest = "test"\n')
        (self.repo/'.gitignore').write_text('grimoire-codex/\n')
        self.git('add','src/Fixture.sol','foundry.toml','.gitignore');self.commit()
        self.baseline=self.git('rev-parse','HEAD').stdout.strip()
        self.source.write_text('pragma solidity ^0.8.0;\ncontract Fixture { uint value = 2; }\n')
        self.git('add','src/Fixture.sol');self.commit()
        self.claude=[self.repo/'GRIMOIRE.md',self.repo/'grimoire/mitigation-review/WIP/M-1.md',
                     self.repo/'grimoire/mitigation-review/SESSIONS.md',self.repo/'test/mitigation/M1.t.sol']
        for path in self.claude:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text('Claude-owned sentinel: '+path.name+'\n')
        self.before={str(p):p.read_bytes() for p in self.claude}
        self.paths=json.loads(self.success(self.tool('init')))
        self.reports=Path(self.paths['reports']);self.pocs=Path(self.paths['pocs'])
        self.finding=self.repo/'scope/finding.md';self.finding.parent.mkdir()
        self.finding.write_text('forge test --match-path test/PoC/Issue12.t.sol\n```solidity\n'
                                'import "../../src/Fixture.sol";\ncontract Issue12 {}\n```\n')

    def git(self,*args):
        return subprocess.run(['git','-C',str(self.repo),*args],env=self.env,capture_output=True,text=True,check=True)

    def commit(self):
        self.git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture')

    def tool(self,*args,input=None,env=None):
        return subprocess.run([sys.executable,str(TOOL),*map(str,args)],cwd=self.repo,env=env or self.env,
                              input=input,capture_output=True,text=True)

    def shell(self,relative,*args,env=None):
        return subprocess.run(['bash',str(ROOT/'skills'/relative),*map(str,args)],cwd=self.repo,
                              env=env or self.env,capture_output=True,text=True)

    def success(self,result):
        self.assertEqual(0,result.returncode,result.stdout+result.stderr)
        return result.stdout.strip()

    def unchanged(self):
        self.assertEqual(self.before,{str(p):p.read_bytes() for p in self.claude})

    def write(self,path,text):
        return self.tool('write',path,input=text)

    def install_fake_forge(self):
        tools=self.repo/'.test-bin';tools.mkdir(exist_ok=True)
        forge=tools/'forge'
        forge.write_text(f'#!{sys.executable}\n'+'''import json, os, sys
from pathlib import Path
cwd=Path.cwd();args=sys.argv[1:]
assert '.isolated-codex' in cwd.parts
assert Path(args[args.index('--root')+1])==cwd
private='grimoire-codex/'+os.environ['GRIMOIRE_SESSION_ID']+'/pocs'
is_private='--match-path' not in args or args[args.index('--match-path')+1].startswith(private+'/')
if is_private: assert os.environ['FOUNDRY_TEST']==private
else: assert 'FOUNDRY_TEST' not in os.environ
for flag in ['--out','--cache-path']:
    assert Path(args[args.index(flag)+1]).is_relative_to(Path(os.environ['GRIMOIRE_AUDIT_ROOT'])/'.isolated-codex')
assert Path(os.environ['TMPDIR']).is_relative_to(Path(os.environ['GRIMOIRE_AUDIT_ROOT']))
assert '--offline' in args
if args[0]=='test': assert '--no-storage-caching' in args
for setting in ['BUILD_INFO_PATH','SNAPSHOTS','FUZZ_FAILURE_PERSIST_DIR','INVARIANT_FAILURE_PERSIST_DIR',
                'FUZZ_CORPUS_DIR','INVARIANT_CORPUS_DIR']:
    assert Path(os.environ['FOUNDRY_'+setting]).is_relative_to(Path(os.environ['GRIMOIRE_AUDIT_ROOT'])/'.isolated-codex')
assert 'test = "test"' in Path('foundry.toml').read_text()
if args[0]=='test':
    if is_private: assert list((cwd/private).rglob('*.t.sol'))
    status='Failure' if os.environ.get('FAKE_FAILURE') or (os.environ.get('FIX_MODE') and is_private and 'value = 2' in Path('src/Fixture.sol').read_text()) else 'Success'
    print('{}' if os.environ.get('FAKE_ZERO') else json.dumps({'Fixture':{'test_results':{'test_issue()':{'status':status}}}}))
else:
    assert Path(args[-1]).is_file()
    print('synthetic compiler success; no Solidity compiler was executed')
''')
        forge.chmod(0o755)
        return dict(self.env,PATH=str(tools)+os.pathsep+self.env['PATH'])

    def test_reports_and_pocs_are_per_run_and_claude_is_untouched(self):
        self.success(self.write(self.reports/'mitigation-review/WIP/M-1.md','Codex review\n'))
        self.success(self.write(self.pocs/'mitigation-review/M1.t.sol','Codex PoC\n'))
        self.assertEqual(self.repo/'grimoire-codex'/self.sid,self.reports)
        self.assertFalse((self.repo/'test/codex').exists())
        self.assertEqual(self.paths,json.loads(self.success(self.tool('init'))))
        self.unchanged()

    def test_writer_refuses_claude_other_runs_escape_and_symlinks(self):
        env=dict(self.env,GRIMOIRE_SESSION_ID='other-codex-1234')
        other=json.loads(self.success(self.tool('init',env=env)))
        target=Path(other['reports'])/'same.md'
        self.success(self.tool('write',target,input='other run',env=env))
        (self.reports/'claude-link').symlink_to(self.repo/'grimoire',target_is_directory=True)
        paths=[*self.claude,target,self.outer/'escape.md',self.reports/'../../grimoire/report.md',
               self.reports/'claude-link/mitigation-review/WIP/M-1.md',self.reports/'.owner']
        for path in paths:
            result=self.tool('write',path,'--replace',input='must not overwrite')
            self.assertNotEqual(0,result.returncode,str(path))
        self.assertEqual('other run',target.read_text())
        self.assertFalse((self.outer/'escape.md').exists())
        self.unchanged()

    def test_existing_file_is_exclusive_unless_own_update_is_explicit(self):
        target=self.reports/'same.md'
        self.success(self.write(target,'first'))
        self.assertNotEqual(0,self.write(target,'second').returncode)
        self.assertEqual('first',target.read_text())
        self.success(self.tool('write',target,'--replace',input='intentional own update'))
        self.assertEqual('intentional own update',target.read_text())

    def test_move_cannot_remove_or_replace_claude_files(self):
        own=self.reports/'peer-review/WIP/M-1.md'
        self.success(self.write(own,'ours'))
        self.assertNotEqual(0,self.tool('move',own,self.claude[1]).returncode)
        self.assertNotEqual(0,self.tool('move',self.claude[1],self.reports/'stolen.md').returncode)
        destination=self.reports/'peer-review/done/M-1.md'
        self.success(self.tool('move',own,destination))
        self.assertFalse(own.exists());self.assertEqual('ours',destination.read_text())
        self.unchanged()

    def test_unknown_directory_is_not_adopted(self):
        env=dict(self.env,GRIMOIRE_SESSION_ID='legacy-artifacts-1234')
        path=self.repo/'grimoire-codex/legacy-artifacts-1234'
        path.mkdir();(path/'unknown.md').write_text('preserve')
        before=snapshot(path)
        self.assertNotEqual(0,self.tool('init',env=env).returncode)
        self.assertEqual(before,snapshot(path))

    def test_extract_poc_rejects_shared_tests_and_reroots_private_imports(self):
        script='peer-review/scripts/extract-poc.sh'
        self.assertNotEqual(0,self.shell(script,self.finding,self.claude[-1]).returncode)
        dest=self.pocs/'peer-review/Issue12.t.sol'
        self.success(self.shell(script,self.finding,dest))
        self.assertIn('../../../../src/Fixture.sol',dest.read_text())
        self.assertNotEqual(0,self.shell(script,self.finding,dest).returncode)
        self.unchanged()

    def test_prefix_snapshot_and_status_logs_refuse_claude_destinations(self):
        prefix='mitigation-review/scripts/prefix-snapshot.sh'
        self.assertNotEqual(0,self.shell(prefix,'src/Fixture.sol','HEAD',self.repo/'test/mitigation','M-1','--no-check').returncode)
        self.success(self.shell(prefix,'src/Fixture.sol','HEAD',self.pocs/'mitigation-review','M-1','--no-check'))
        result=self.pocs/'mitigation-review/FixturePreFixM1.sol'
        self.assertIn('value = 1',result.read_text())
        self.assertIn('contract FixturePreFixM1',result.read_text())
        log='summon/scripts/session-status.sh'
        self.assertNotEqual(0,self.shell(log,self.claude[2],'M-1.md','WIP').returncode)
        own=self.reports/'mitigation-review/SESSIONS.md'
        self.success(self.shell(log,own,'M-1.md','WIP'))
        self.assertIn(self.sid,own.read_text());self.unchanged()

    def test_only_this_runs_pocs_are_copied_even_when_git_ignored(self):
        own=self.pocs/'peer-review/Issue12.t.sol'
        self.success(self.write(own,'our proof\n'))
        self.success(self.write(self.reports/'private-report.md','not source code\n'))
        other=self.repo/'grimoire-codex/another-run/pocs/peer-review/Issue12.t.sol'
        other.parent.mkdir(parents=True);other.write_text('foreign proof\n')
        result=subprocess.run(['bash',str(ISOLATE),'create','i12'],cwd=self.repo,env=self.env,capture_output=True,text=True)
        self.success(result)
        copy=self.repo/'.isolated-codex'/self.sid/'i12'
        self.assertEqual('our proof\n',(copy/own.relative_to(self.repo)).read_text())
        self.assertFalse((copy/other.relative_to(self.repo)).exists())
        self.assertFalse((copy/(self.reports/'private-report.md').relative_to(self.repo)).exists())
        self.success(self.tool('move',own,self.reports/'archived-poc.sol'))
        result=subprocess.run(['bash',str(ISOLATE),'sync','i12'],cwd=self.repo,env=self.env,capture_output=True,text=True)
        self.success(result)
        self.assertFalse((copy/own.relative_to(self.repo)).exists());self.unchanged()

    def test_forge_runner_uses_private_test_root_and_saves_raw_evidence(self):
        env=self.install_fake_forge()
        self.success(self.write(self.pocs/'peer-review/Issue12.t.sol','synthetic proof\n'))
        suite=self.paths['poc-relative']+'/peer-review/Issue12*.t.sol'
        self.success(self.tool('test','--name','i12','--suite',suite,env=env))
        self.assertTrue(list((self.reports/'runs/i12').rglob('*.stdout')))
        self.assertFalse((self.repo/'out').exists());self.assertFalse((self.repo/'cache').exists())
        self.assertEqual('[profile.default]\nsrc = "src"\ntest = "test"\n',(self.repo/'foundry.toml').read_text())
        self.unchanged()

    def test_empty_test_evidence_and_foreign_suites_are_not_success(self):
        env=self.install_fake_forge()
        self.success(self.write(self.pocs/'peer-review/Issue12.t.sol','synthetic proof\n'))
        suite=self.paths['poc-relative']+'/peer-review/Issue12*.t.sol'
        result=self.tool('test','--name','empty','--suite',suite,env=dict(env,FAKE_ZERO='1'))
        self.assertNotEqual(0,result.returncode)
        self.assertIn('zero tests',result.stderr)
        self.assertNotEqual(0,self.tool('test','--name','failed','--suite',suite,env=dict(env,FAKE_FAILURE='1')).returncode)
        self.assertNotEqual(0,self.tool('test','--name','foreign','--suite','test/mitigation/*.sol',env=env).returncode)
        self.unchanged()

    def test_parallel_runs_can_use_identical_report_and_poc_names(self):
        envs=[self.env,dict(self.env,GRIMOIRE_SESSION_ID='another-codex-1234')]
        def produce(env):
            paths=json.loads(self.success(self.tool('init',env=env)))
            report=Path(paths['reports'])/'mitigation-review/WIP/M-1.md'
            poc=Path(paths['mitigation-pocs'])/'M1.t.sol'
            for file in [report,poc]:
                self.success(self.tool('write',file,input=env['GRIMOIRE_SESSION_ID'],env=env))
            return report,poc
        with ThreadPoolExecutor(max_workers=2) as pool:
            outputs=list(pool.map(produce,envs))
        for files,env in zip(outputs,envs):
            self.assertTrue(all(p.read_text()==env['GRIMOIRE_SESSION_ID'] for p in files))
        self.assertNotEqual(outputs[0],outputs[1]);self.unchanged()

    def test_canonical_repository_is_refused_before_artifact_or_copy_writes(self):
        self.git('remote','add','canonical','https://github.com/0xStalin-eth/grimoire.git')
        before=snapshot(self.repo)
        self.assertNotEqual(0,self.write(self.reports/'blocked.md','no').returncode)
        result=subprocess.run(['bash',str(ISOLATE),'create','blocked'],cwd=self.repo,env=self.env,capture_output=True,text=True)
        self.assertNotEqual(0,result.returncode)
        self.assertIn('read-only',result.stderr)
        self.assertEqual(before,snapshot(self.repo))

    def test_fix_verification_keeps_private_poc_and_regression_discovery_separate(self):
        env=self.install_fake_forge()
        self.success(self.write(self.pocs/'mitigation-review/M1.t.sol','synthetic proof'))
        work=self.success(self.shell('peer-review/scripts/isolated-workspace.sh','work','m1'))
        patch=Path(work)/'Fixture.sol'
        self.success(self.write(patch,self.source.read_text().replace('value = 2','value = 3')))
        result=self.shell('peer-review/scripts/verify-fix.sh','--name','m1','--patch',f'src/Fixture.sol={patch}',
                          '--suite',self.paths['poc-relative']+'/mitigation-review/*','--suite','test/*',
                          env=dict(env,FIX_MODE='1',FOUNDRY_TEST='inherited-private-directory'))
        self.success(result)
        self.assertIn('failing before: 1',result.stdout)
        self.assertIn('the workspace did not change',result.stdout)
        raw=list((self.reports/'runs/verify-fix-m1').rglob('before.1.json'))
        self.assertEqual(1,len(raw))
        self.assertIn('Failure',raw[0].read_text())
        self.assertIn('value = 2',self.source.read_text());self.unchanged()

    def test_snapshot_build_is_also_confined_to_an_owned_copy(self):
        env=self.install_fake_forge()
        self.success(self.shell('mitigation-review/scripts/prefix-snapshot.sh','src/Fixture.sol','HEAD',
                                self.pocs/'mitigation-review','M-1',env=env))
        copy=self.repo/'.isolated-codex'/self.sid/'snapshot-M1'
        self.assertTrue(copy.is_dir());self.assertTrue(list((self.reports/'runs/snapshot-M1').rglob('*.stdout')))
        self.unchanged()

    def test_mirror_defaults_and_versions_are_private_to_codex(self):
        tools=self.repo/'.test-bin';tools.mkdir()
        gh=tools/'gh'
        gh.write_text(f'#!{sys.executable}\n'+'''import json, os
from pathlib import Path
with open(Path(__file__).parent/'calls.log','a') as f:f.write('called\\n')
v=os.environ.get('ISSUE_VERSION','1')
print(json.dumps({'number':12,'title':'Synthetic issue','body':'version '+v,'url':'https://example.invalid/issues/12',
    'author':{'login':'fixture'},'labels':[],'state':'OPEN','createdAt':'2026-11-10T00:00:00Z',
    'updatedAt':'2026-11-10T00:00:0'+v+'Z','closedAt':None,'comments':[]}))
''');gh.chmod(0o755)
        env=dict(self.env,PATH=str(tools)+os.pathsep+self.env['PATH'])
        script=ROOT/'skills/findings-sync/scripts/findings_sync.py'
        def sync(*args,version='1'):
            return subprocess.run([sys.executable,str(script),'--repo','fixture/issues',*map(str,args)],
                                  cwd=self.repo,env=dict(env,ISSUE_VERSION=version),capture_output=True,text=True)
        self.success(sync('pull','12'))
        mirror=Path(self.paths['mirror']);file=next(mirror.glob('issue12-*.md'))
        self.assertIn('version 1',file.read_text())
        self.success(sync('update','12',version='2'))
        self.assertIn('version 2',file.read_text())
        self.assertIn('version 1',(mirror/'originals'/file.name).read_text())
        calls=(tools/'calls.log').read_text()
        self.assertNotEqual(0,sync('--mirror',self.repo/'grimoire/original-findings','pull','12').returncode)
        self.assertEqual(calls,(tools/'calls.log').read_text())
        self.unchanged()
