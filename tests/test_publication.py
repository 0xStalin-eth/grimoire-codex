"""Exercise real local Git branch publication against a temporary bare remote; stub only GitHub API."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import open_sync_pr as publish
import sync


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *map(str, args)], stderr=subprocess.PIPE).decode().strip()


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='grimoire-pr-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.remote = self.base / 'bare.git'
        self.root = self.base / 'downstream'
        self.root.mkdir()
        git(self.base, 'init', '--bare', '-q', self.remote)
        git(self.root, 'init', '-q', '-b', 'main')
        for name, text in {
            'codex/project.json': (sync.ROOT / 'codex/project.json').read_text(),
            'skills/alpha/SKILL.md': 'fixture baseline\n',
            'agents/role.md': 'fixture role\n',
            'vendor/upstream/a file.md': 'upstream baseline\n',
            '.agents/skills/alpha': 'discovery fixture\n',
            'sync-state.json': json.dumps({'upstream_sha': 'a'*40}),
        }.items():
            p = self.root / name;p.parent.mkdir(parents=True, exist_ok=True);p.write_text(text)
        git(self.root, 'add', '.')
        git(self.root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'baseline')
        git(self.root, 'remote', 'add', 'origin', self.remote)
        git(self.root, 'push', '-q', 'origin', 'main')
        self.gh_calls = []
        self.existing_prs = []
        self.real_call = publish.call

    def bridge(self, *args, **kwargs):
        if args[:4] == ('git', 'remote', 'get-url', 'origin'):
            return SimpleNamespace(stdout=f'https://github.com/{publish.REPO}.git\n', returncode=0)
        if args[0] == 'gh':
            self.gh_calls.append(args)
            if args[1] == 'api':
                return SimpleNamespace(stdout='{"default_branch":"main"}', returncode=0)
            if args[1:3] == ('pr', 'list'):
                return SimpleNamespace(stdout=json.dumps(self.existing_prs), returncode=0)
            if args[1:3] in [('pr','create'), ('pr','edit')]:
                body = Path(args[args.index('--body-file')+1]).read_text()
                self.assertIn('b'*40, body)
                self.assertIn('No automatic merge', body)
            return SimpleNamespace(stdout='', returncode=0)
        # All Git remotes are temporary local directories. No network or original repo access.
        return self.real_call(*args, **kwargs)

    def invoke(self):
        with patch.object(publish, 'ROOT', self.root), patch.object(publish, 'call', self.bridge), patch.dict(os.environ, {'GITHUB_REPOSITORY': publish.REPO}):
            return publish.main()

    def updates(self):
        (self.root/'skills/alpha/SKILL.md').write_text('updated generated skill\n')
        (self.root/'vendor/upstream/a file.md').write_text('updated asset with spaces\n')
        (self.root/'sync-state.json').write_text(json.dumps({'upstream_sha':'b'*40}))

    def test_local_git_publication_creates_reviewable_bot_branch(self):
        self.updates();self.assertEqual(0,self.invoke())
        branch = git(self.remote,'rev-parse','refs/heads/'+publish.BRANCH)
        self.assertIn(publish.MARKER,git(self.remote,'show','-s','--format=%B',branch))
        self.assertEqual('updated asset with spaces',git(self.remote,'show',branch+':vendor/upstream/a file.md'))
        self.assertTrue(any(c[1:3]==('pr','create') for c in self.gh_calls))
        self.assertEqual('fixture baseline',git(self.remote,'show','main:skills/alpha/SKILL.md'))

    def test_no_changes_creates_no_branch_or_pr(self):
        self.assertEqual(0,self.invoke())
        self.assertFalse(any(c[1:3] in [('pr','create'),('pr','edit')] for c in self.gh_calls))
        result = subprocess.run(['git','-C',str(self.remote),'show-ref','--verify','refs/heads/'+publish.BRANCH],capture_output=True)
        self.assertNotEqual(0,result.returncode)

    def test_existing_pr_is_updated(self):
        self.existing_prs=[{'number':7}];self.updates();self.invoke()
        self.assertTrue(any(c[1:3]==('pr','edit') and c[3]=='7' for c in self.gh_calls))

    def test_human_commit_on_sync_branch_blocks_overwrite(self):
        self.updates();self.invoke()
        (self.root/'skills/alpha/SKILL.md').write_text('human work\n')
        git(self.root,'add','skills/alpha/SKILL.md')
        git(self.root,'-c','user.name=Human','-c','user.email=human@example.invalid','commit','-qm','human review')
        git(self.root,'push','-q','origin',publish.BRANCH)
        protected_sha=git(self.remote,'rev-parse',publish.BRANCH)
        git(self.root,'checkout','-q','main');self.updates()
        with self.assertRaisesRegex(ValueError,'non-bot work'):
            self.invoke()
        self.assertEqual(protected_sha,git(self.remote,'rev-parse',publish.BRANCH))

    def test_wrong_repository_refuses_before_api_or_push(self):
        with patch.object(publish,'ROOT',self.root), patch.dict(os.environ,{'GITHUB_REPOSITORY':'0xStalin-eth/grimoire'}):
            with self.assertRaisesRegex(ValueError,'restricted'):
                publish.main()

    def test_status_parser_keeps_spaces_and_rename_sources(self):
        self.assertEqual(['vendor/upstream/new name.md','vendor/upstream/old name.md'],
            publish.status_paths('R  vendor/upstream/new name.md\0vendor/upstream/old name.md\0'))
