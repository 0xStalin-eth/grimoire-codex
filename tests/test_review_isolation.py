"""Exercise real review helpers in synthetic checkouts; no model or live Forge execution."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'skills/peer-review/scripts/isolated-workspace.sh'
CLAUDE_HELPER = ROOT / 'vendor/upstream/skills/peer-review/scripts/isolated-workspace.sh'


def snapshot(path):
    return {str(p.relative_to(path)): (('link', os.readlink(p)) if p.is_symlink() else
            ('file', hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mode & 0o777))
            for p in path.rglob('*') if p.is_file() or p.is_symlink()}


class ReviewIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='grimoire-isolation-')
        self.addCleanup(self.temp.cleanup)
        self.outer = Path(self.temp.name).resolve()
        self.repo = self.outer / 'audit'
        self.repo.mkdir()
        self.env = dict(os.environ, GRIMOIRE_SESSION_ID='shared-session-1234',
                        CLAUDE_CODE_SESSION_ID='shared-session-1234',
                        GRIMOIRE_AUDIT_ROOT=str(self.repo), GIT_OPTIONAL_LOCKS='0')
        self.git('init', '-q')
        (self.repo/'target.txt').write_text('original\n')
        self.git('add', 'target.txt'); self.commit()
        self.first_sha = self.git('rev-parse', 'HEAD').stdout.strip()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], env=self.env,
                              text=True, capture_output=True, check=True)

    def commit(self):
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')

    def helper(self, *args, env=None, claude=False, cwd=None):
        return subprocess.run(['bash', str(CLAUDE_HELPER if claude else HELPER), *args],
                              cwd=cwd or self.repo, env=env or self.env, text=True, capture_output=True)

    def success(self, result):
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result.stdout.strip()

    def test_claude_and_codex_same_id_and_name_have_separate_copies(self):
        self.success(self.helper('create', 'i12', claude=True))
        claude = self.repo/'.isolated'
        before = snapshot(claude)
        self.success(self.helper('create', 'i12'))
        copy = Path(self.success(self.helper('path', 'i12')))
        self.assertEqual(self.repo/'.isolated-codex/shared-session-1234/i12', copy)
        owner = json.loads((copy.parent/'.owner').read_text())
        self.assertEqual('codex', owner['runtime'])
        self.assertEqual(str(self.repo), owner['audit_root'])
        self.assertFalse((copy/'.isolated').exists())
        self.assertFalse((copy/'.isolated-codex').exists())
        (copy/'target.txt').write_text('temporary Codex patch\n')
        self.success(self.helper('sync', 'i12'))
        self.success(self.helper('verify', 'i12'))
        self.success(self.helper('remove', 'i12'))
        self.assertEqual(before, snapshot(claude))
        self.success(self.helper('verify', 'i12', claude=True))
        self.assertEqual('original\n', (self.repo/'target.txt').read_text())

    def test_parallel_codex_runs_same_name_do_not_modify_each_other(self):
        envs = [dict(self.env, GRIMOIRE_SESSION_ID=f'codex-session-{n:04}') for n in [1, 2]]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda env: self.helper('create', 'i12', env=env), envs))
        for result in results: self.success(result)
        paths = [Path(self.success(self.helper('path', 'i12', env=env))) for env in envs]
        self.assertNotEqual(paths[0], paths[1])
        before = snapshot(paths[1].parent)
        self.success(self.helper('remove', 'i12', env=envs[0]))
        self.assertEqual(before, snapshot(paths[1].parent))
        self.success(self.helper('verify', 'i12', env=envs[1]))

    def test_unignored_claude_tree_is_excluded_from_head_and_pinned_ref(self):
        legacy = self.repo/'.isolated/foreign-session'
        legacy.mkdir(parents=True)
        (legacy/'private-report.md').write_text('Other runtime output, not audit source.\n')
        outside = self.outer/'outside'
        outside.mkdir();(outside/'sentinel').write_text('untouched')
        (legacy/'outside-link').symlink_to(outside, target_is_directory=True)
        before = snapshot(self.repo/'.isolated')
        self.success(self.helper('create', 'head-copy'))
        (self.repo/'target.txt').write_text('updated source\n')
        self.git('add', 'target.txt');self.commit()
        self.success(self.helper('create', 'baseline', '--ref', self.first_sha))
        for name in ['head-copy', 'baseline']:
            copy = Path(self.success(self.helper('path', name)))
            self.assertFalse((copy/'.isolated').exists())
            self.assertFalse((copy/'.isolated-codex').exists())
            self.assertEqual('original\n', (copy/'target.txt').read_text())
        self.assertEqual(before, snapshot(self.repo/'.isolated'))
        self.assertEqual('untouched', (outside/'sentinel').read_text())

    def test_foreign_runtime_or_launch_owner_is_never_adopted(self):
        session = self.repo/'.isolated-codex/shared-session-1234'
        copy = session/'i12';copy.mkdir(parents=True)
        (copy/'.isolated-state.json').write_text('{}')
        owner={'runtime':'claude','session':'shared-session-1234','workspace':str(self.repo),'audit_root':str(self.repo)}
        for change in [{'runtime':'claude'}, {'runtime':'codex','audit_root':str(self.outer)}, {'runtime':'codex','workspace':str(self.outer)}]:
            marker=owner | change
            (session/'.owner').write_text(json.dumps(marker))
            before=snapshot(self.repo/'.isolated-codex')
            for args in [('session',),('work','i12'),('path','i12'),('sync','i12'),('verify','i12'),('remove','i12'),('create','other')]:
                self.assertNotEqual(0,self.helper(*args).returncode,args)
            self.assertEqual(before,snapshot(self.repo/'.isolated-codex'))

    def test_symlinked_codex_base_cannot_reach_claude_workspace(self):
        self.success(self.helper('create','i12',claude=True))
        before=snapshot(self.repo/'.isolated')
        (self.repo/'.isolated-codex').symlink_to('.isolated',target_is_directory=True)
        for args in [('list',),('session',),('work','i12'),('path','i12'),('create','other'),('sync','i12'),('remove','i12')]:
            self.assertNotEqual(0,self.helper(*args).returncode,args)
        self.assertEqual(before,snapshot(self.repo/'.isolated'))

    def test_symlinked_owner_or_work_folder_is_refused(self):
        self.success(self.helper('create','i12',claude=True))
        claude_before=snapshot(self.repo/'.isolated')
        self.success(self.helper('session'))
        session=self.repo/'.isolated-codex/shared-session-1234'
        owner=(session/'.owner').read_bytes()
        (session/'.owner').unlink()
        (session/'.owner').symlink_to(self.repo/'.isolated/shared-session-1234/.owner')
        self.assertNotEqual(0,self.helper('work','i12').returncode)
        self.assertEqual(claude_before,snapshot(self.repo/'.isolated'))
        (session/'.owner').unlink();(session/'.owner').write_bytes(owner)
        (session/'work').symlink_to(self.repo/'.isolated/shared-session-1234',target_is_directory=True)
        self.assertNotEqual(0,self.helper('work','i12').returncode)
        self.assertEqual(claude_before,snapshot(self.repo/'.isolated'))

    def test_missing_or_relative_launch_root_fails_before_creating_copies(self):
        for launch in ['', '.', 'missing-folder']:
            env=dict(self.env,GRIMOIRE_AUDIT_ROOT=launch)
            for args in [('create','i12'),('work','i12'),('session',)]:
                self.assertNotEqual(0,self.helper(*args,env=env).returncode)
        self.assertFalse((self.repo/'.isolated-codex').exists())

    def test_git_root_above_session_launch_directory_is_refused(self):
        launch=self.repo/'subdirectory';launch.mkdir()
        env=dict(self.env,GRIMOIRE_AUDIT_ROOT=str(launch))
        before=snapshot(self.repo)
        result=self.helper('create','i12',env=env,cwd=launch)
        self.assertNotEqual(0,result.returncode)
        self.assertIn('above or outside',result.stderr)
        guard=ROOT/'skills/mitigation-review/scripts/_workspace-guard.sh'
        result=subprocess.run(['bash','-c','set -e; source "$1"; mkdir should-not-exist','_',str(guard)],
                              cwd=launch,env=env,capture_output=True,text=True)
        self.assertNotEqual(0,result.returncode)
        self.assertFalse((launch/'should-not-exist').exists())
        self.assertEqual(before,snapshot(self.repo))

    def test_git_root_inside_launch_directory_remains_inside_it(self):
        env=dict(self.env,GRIMOIRE_AUDIT_ROOT=str(self.outer))
        self.success(self.helper('create','i12',env=env))
        path=Path(self.success(self.helper('path','i12',env=env)))
        self.assertTrue(path.is_relative_to(self.outer))

    def test_linked_checkout_does_not_refresh_shared_git_metadata(self):
        linked=self.outer/'linked-audit'
        self.git('worktree','add','--detach',str(linked),'HEAD')
        metadata=self.repo/'.git'
        before=snapshot(metadata)
        mtimes={str(p.relative_to(metadata)):p.stat().st_mtime_ns for p in metadata.rglob('*') if p.is_file()}
        env=dict(self.env,GRIMOIRE_AUDIT_ROOT=str(linked))
        env.pop('GIT_OPTIONAL_LOCKS',None)  # The port itself must disable optional Git writes.
        self.success(self.helper('create','i12',env=env,cwd=linked))
        self.success(self.helper('verify','i12',env=env,cwd=linked))
        self.assertEqual(before,snapshot(metadata))
        self.assertEqual(mtimes,{str(p.relative_to(metadata)):p.stat().st_mtime_ns for p in metadata.rglob('*') if p.is_file()})

    def test_status_log_outside_launch_directory_is_refused(self):
        outside=self.outer/'outside-log.md'
        helper=ROOT/'skills/summon/scripts/session-status.sh'
        result=subprocess.run(['bash',str(helper),str(outside),'finding.md','WIP'],cwd=self.repo,env=self.env,
                              capture_output=True,text=True)
        self.assertNotEqual(0,result.returncode)
        self.assertFalse(outside.exists())
        self.assertFalse(Path(str(outside)+'.lock').exists())

    def test_verify_fix_scratch_and_copy_stay_in_codex_namespace(self):
        # A small fake Forge process tests orchestration only, not Solidity or vulnerability validity.
        tools=self.repo/'tools';tools.mkdir()
        forge=tools/'forge'
        forge.write_text(f'#!{sys.executable}\n'+'''import json, os
from pathlib import Path
cwd=Path.cwd()
assert '.isolated-codex' in cwd.parts
assert cwd.is_relative_to(Path(os.environ['GRIMOIRE_AUDIT_ROOT']))
status='Success' if Path('target.txt').read_text()=='fixed\\n' else 'Failure'
print(json.dumps({'Fixture':{'test_results':{'test_issue()':{'status':status,'reason':'synthetic test'}}}}))
''')
        forge.chmod(0o755)
        self.git('add','tools/forge');self.commit()
        self.success(self.helper('create','i12',claude=True))
        before=snapshot(self.repo/'.isolated')
        work=Path(self.success(self.helper('work','i12')))
        patched=work/'fixed.txt';patched.write_text('fixed\n')
        env=dict(self.env,PATH=str(tools)+os.pathsep+self.env['PATH'])
        verify=ROOT/'skills/peer-review/scripts/verify-fix.sh'
        result=subprocess.run(['bash',str(verify),'--patch',f'target.txt={patched}','--suite','fixture','--name','i12'],
                              cwd=self.repo,env=env,capture_output=True,text=True)
        self.success(result)
        self.assertIn('failing before: 1',result.stdout)
        self.assertIn('the workspace did not change during the run',result.stdout)
        self.assertNotIn('COMPILE-OR-RUN-ERROR',result.stdout)
        self.assertEqual('original\n',(self.repo/'target.txt').read_text())
        self.assertFalse((work.parent.parent/'.verify-i12').exists())
        self.assertEqual(before,snapshot(self.repo/'.isolated'))
