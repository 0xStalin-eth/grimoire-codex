import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from bootstrap import bootstrap


class HelperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='grimoire-helper-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.env = dict(os.environ, GRIMOIRE_SESSION_ID='test-session-1234', GRIMOIRE_AUDIT_ROOT=str(self.root))

    def shell(self, script, *args, **kwargs):
        return subprocess.run(['bash', str(ROOT / 'skills' / script), *map(str, args)], cwd=self.root,
                              env=kwargs.get('env', self.env), text=True, capture_output=True)

    def report_log(self):
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        tool=ROOT/'scripts/review_artifacts.py'
        result=subprocess.run([sys.executable,str(tool),'init'],cwd=self.root,env=self.env,
                              capture_output=True,text=True,check=True)
        return Path(json.loads(result.stdout)['reports'])/'SESSIONS.md'

    def test_bootstrap_is_idempotent_and_preserves_registry(self):
        store = self.root / 'personal'
        bootstrap(store)
        registry = store / 'librarian/library/libraries.yaml'
        registry.write_text('libraries: {example: {type: local}}\n')
        bootstrap(store)
        self.assertEqual('libraries: {example: {type: local}}\n', registry.read_text())

    def test_session_logging_concurrent_updates(self):
        log = self.report_log()
        def update(n):
            return self.shell('summon/scripts/session-status.sh', log, f'hyp-{n}.md', 'WIP', 'fixture')
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(update, range(12)))
        self.assertTrue(all(r.returncode == 0 for r in results), [r.stderr for r in results])
        text = log.read_text()
        self.assertEqual(14, len(text.splitlines()))
        self.assertFalse(log.with_suffix('.md.lock').exists())

    def test_session_logging_missing_or_malformed_id_refuses(self):
        log=self.report_log()
        for sid in ['', '../escape', 'bad\nrow']:
            result = self.shell('summon/scripts/session-status.sh', log, 'a.md', 'WIP', env=dict(self.env, GRIMOIRE_SESSION_ID=sid))
            self.assertNotEqual(0, result.returncode)
        self.assertFalse(log.exists())

    def test_existing_log_lock_is_not_stolen(self):
        log = self.report_log()
        lock = Path(str(log)+'.lock')
        lock.mkdir(); log.write_text('unchanged\n')
        result = self.shell('summon/scripts/session-status.sh', log, 'a.md', 'WIP')
        self.assertNotEqual(0, result.returncode)
        self.assertEqual('unchanged\n', log.read_text())
        self.assertTrue(lock.exists())

    def test_isolated_copy_verification_and_session_separation(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / 'target.sol').write_text('contract Fixture {}\n')
        subprocess.run(['git', '-C', str(self.root), 'add', 'target.sol'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'], check=True)
        script = 'peer-review/scripts/isolated-workspace.sh'
        created = self.shell(script, 'create', 'proof')
        self.assertEqual(0, created.returncode, created.stderr)
        verified = self.shell(script, 'verify', 'proof')
        self.assertEqual(0, verified.returncode, verified.stderr)
        path = self.shell(script, 'path', 'proof').stdout.strip()
        self.assertTrue(Path(path).is_relative_to(self.root / '.isolated-codex/test-session-1234'))
        (Path(path) / 'target.sol').write_text('contract Changed {}\n')
        self.assertNotEqual(0, self.shell(script, 'verify', 'proof').returncode)
        other = dict(self.env, GRIMOIRE_SESSION_ID='other-session-1234')
        self.assertNotEqual(0, self.shell(script, 'remove', 'proof', env=other).returncode)
        self.assertEqual('contract Fixture {}\n', (self.root / 'target.sol').read_text())

    def test_finding_and_check_examples_validate(self):
        for example in ['reentrancy-finding.md', 'access-control-finding.md']:
            result = self.shell('finding/scripts/validate-finding.sh', ROOT / 'skills/finding/examples' / example)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        for example in (ROOT / 'skills/checks/examples').glob('*.md'):
            result = self.shell('checks/scripts/validate-check.sh', example)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_installer_is_idempotent_and_refuses_collisions(self):
        from install import install
        self.assertEqual(40, install(self.root))
        self.assertEqual(40, install(self.root))
        link = self.root / '.agents/skills/annotation'
        self.assertEqual((ROOT/'skills/annotation').resolve(),link.resolve())
        link.unlink();link.mkdir()
        with self.assertRaisesRegex(ValueError,'collision'):
            install(self.root)
        self.assertTrue(link.is_dir())

    def test_installer_refuses_claude_toolkit_destination(self):
        from install import install
        marker=self.root/'.claude-plugin/plugin.json'
        marker.parent.mkdir();marker.write_text('{}')
        with self.assertRaisesRegex(ValueError,'Claude toolkit'):
            install(self.root)
        self.assertFalse((self.root/'.agents').exists())
