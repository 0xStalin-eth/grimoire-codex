"""Automatic setup on synthetic checkouts; no model, user shell edits or live service calls."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_review_isolation import snapshot

ROOT = Path(__file__).resolve().parents[1]


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='grimoire-session-')
        self.addCleanup(self.temp.cleanup)
        self.outer = Path(self.temp.name).resolve()
        self.repo = self.outer/'audit with spaces';self.repo.mkdir()
        self.env = dict(os.environ, GIT_OPTIONAL_LOCKS='0',
                        GRIMOIRE_AUDIT_ROOT=str(self.outer/'stale-launch'), GRIMOIRE_SESSION_ID='stale-run-1234')
        self.git('init', '-q')
        (self.repo/'source.txt').write_text('original\n')
        self.git('add', 'source.txt');self.commit()
        self.head = self.git('rev-parse', 'HEAD').stdout.strip()
        for rel in ['GRIMOIRE.md', 'grimoire/report.md', 'test/Claude.t.sol', '.isolated/claude/sentinel']:
            file = self.repo/rel;file.parent.mkdir(parents=True, exist_ok=True);file.write_text('Claude-owned\n')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], env=self.env,
                              capture_output=True, text=True, check=True)

    def commit(self):
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')

    def command(self, *args, cwd=None):
        return subprocess.run([sys.executable, str(ROOT/'scripts/session.py'), *map(str, args)],
                              cwd=cwd or self.repo, env=self.env, capture_output=True, text=True)

    def success(self, result):
        self.assertEqual(0, result.returncode, result.stdout+result.stderr)
        return json.loads(result.stdout)

    def test_start_detects_checkout_without_exports_and_preserves_existing_files(self):
        (self.repo/'source.txt').write_text('uncommitted work\n')
        before = snapshot(self.repo)
        installed = snapshot(ROOT/'scripts')
        result = self.success(self.command('start'))
        self.assertEqual(str(self.repo), result['audit_root'])
        self.assertEqual(str(self.repo), result['workspace'])
        self.assertNotEqual('stale-run-1234', result['run_id'])
        self.assertEqual(self.head, result['checkout_at_start']['head'])
        self.assertIn(' M source.txt', result['checkout_at_start']['status'])
        after = snapshot(self.repo)
        self.assertEqual(before, {key: after[key] for key in before})
        self.assertTrue(all(key.startswith('grimoire-codex/'+result['run_id']+'/') for key in set(after)-set(before)))
        self.assertEqual(installed, snapshot(ROOT/'scripts'))
        saved = json.loads(Path(result['session_file']).read_text())
        self.assertEqual(result['checkout_at_start'], saved['checkout_at_start'])

    def test_parallel_starts_have_independent_outputs_and_real_helper_copies(self):
        with ThreadPoolExecutor(max_workers=3) as pool:
            sessions = list(pool.map(lambda _: self.success(self.command('start')), range(3)))
        self.assertEqual(3, len({s['run_id'] for s in sessions}))
        before = snapshot(self.repo/'.isolated')
        def create(session):
            env = dict(self.env, **session['environment'])
            result = subprocess.run(['bash', str(ROOT/'skills/peer-review/scripts/isolated-workspace.sh'),
                                     'create', 'i12'], cwd=self.repo, env=env, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout+result.stderr)
            copy = self.repo/'.isolated-codex'/session['run_id']/'i12'
            self.assertTrue((copy/'source.txt').is_file())
            return copy
        with ThreadPoolExecutor(max_workers=3) as pool:
            copies = list(pool.map(create, sessions))
        self.assertEqual(3, len(set(copies)))
        self.assertEqual(before, snapshot(self.repo/'.isolated'))

    def test_resume_is_read_only_and_keeps_original_commit_evidence(self):
        initial = self.success(self.command('start'))
        (self.repo/'source.txt').write_text('new commit\n')
        self.git('add', 'source.txt');self.commit()
        before = snapshot(self.repo)
        result = self.success(self.command('resume', '--run-id', initial['run_id']))
        self.assertEqual(initial['environment'], result['environment'])
        self.assertEqual(initial['checkout_at_start'], result['checkout_at_start'])
        self.assertNotEqual(self.head, result['checkout_now']['head'])
        self.assertEqual(before, snapshot(self.repo))

    def test_resume_requires_a_specific_owned_record_and_does_not_pick_latest(self):
        initial = self.success(self.command('start'))
        for args in [('resume',), ('resume', '--run-id', 'unknown-run-1234')]:
            before = snapshot(self.repo)
            self.assertNotEqual(0, self.command(*args).returncode)
            self.assertEqual(before, snapshot(self.repo))
        record = Path(initial['session_file'])
        data = json.loads(record.read_text());data['audit_root'] = str(self.outer)
        record.write_text(json.dumps(data))
        before = snapshot(self.repo)
        self.assertNotEqual(0, self.command('resume', '--run-id', initial['run_id']).returncode)
        self.assertEqual(before, snapshot(self.repo))

    def test_nested_launch_never_broadens_to_the_git_root(self):
        nested = self.repo/'nested';nested.mkdir()
        before = snapshot(self.repo)
        self.assertNotEqual(0, self.command('start', cwd=nested).returncode)
        self.assertNotEqual(0, self.command('start', '--audit-root', '.', cwd=self.repo).returncode)
        self.assertEqual(before, snapshot(self.repo))
        # A target below the recorded launch boundary is allowed, with all outputs inside it.
        result = self.success(self.command('start', '--audit-root', self.outer))
        self.assertEqual(str(self.outer), result['audit_root'])
        self.assertTrue(Path(result['session_file']).is_relative_to(self.outer))

    def test_canonical_remote_and_redirected_output_are_refused_before_writes(self):
        self.git('remote', 'add', 'origin', 'https://github.com/0xStalin-eth/grimoire.git')
        before = snapshot(self.repo)
        self.assertNotEqual(0, self.command('start').returncode)
        self.assertEqual(before, snapshot(self.repo))
        self.git('remote', 'remove', 'origin')
        redirect = self.outer/'foreign-output';redirect.mkdir()
        (self.repo/'grimoire-codex').symlink_to(redirect, target_is_directory=True)
        before = snapshot(self.repo)
        self.assertNotEqual(0, self.command('start').returncode)
        self.assertEqual(before, snapshot(self.repo))
        self.assertEqual([], list(redirect.iterdir()))

    def test_checkout_without_a_commit_is_refused_before_output(self):
        empty = self.outer/'empty';empty.mkdir()
        subprocess.run(['git', 'init', '-q', str(empty)], env=self.env, check=True)
        before = snapshot(empty)
        self.assertNotEqual(0, self.command('start', cwd=empty).returncode)
        self.assertEqual(before, snapshot(empty))

    def test_shared_context_and_tomes_are_discovered_and_read_without_changes(self):
        tome = self.repo/'grimoire/tomes/active/flow.md'
        tome.parent.mkdir(parents=True);tome.write_text('# Flow\nSource-backed Claude research.\n')
        before = snapshot(self.repo)
        session = self.success(self.command('start'))
        refs = session['shared_references']
        self.assertEqual('read-only', refs['access'])
        self.assertEqual([str(self.repo/'GRIMOIRE.md')], refs['contexts'])
        self.assertEqual([str(self.repo/'grimoire/tomes')], refs['tomes'])
        after_start = snapshot(self.repo)
        self.assertEqual(before, {key: after_start[key] for key in before})
        for source in [self.repo/'GRIMOIRE.md', tome]:
            result = self.success(self.command('read-reference', '--run-id', session['run_id'], '--path', source))
            self.assertEqual(str(source), result['path'])
            self.assertEqual(source.read_text(), result['content'])
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), result['sha256'])
        self.assertEqual(after_start, snapshot(self.repo))

    def test_research_in_launch_folder_is_available_to_a_contained_target(self):
        context = self.outer/'GRIMOIRE.md';context.write_text('Audit scope for the contained target.\n')
        tome = self.outer/'grimoire/tomes/mechanism.md'
        tome.parent.mkdir(parents=True);tome.write_text('Shared Claude mechanism analysis.\n')
        session = self.success(self.command('start', '--audit-root', self.outer))
        self.assertEqual([str(context), str(self.repo/'GRIMOIRE.md')], session['shared_references']['contexts'])
        self.assertIn(str(tome.parent), session['shared_references']['tomes'])
        before = snapshot(self.outer)
        result = self.success(self.command('read-reference', '--audit-root', self.outer,
                                          '--run-id', session['run_id'], '--path', tome))
        self.assertEqual(tome.read_text(), result['content'])
        self.assertEqual(before, snapshot(self.outer))

    def test_reference_reader_refuses_escape_links_and_other_codex_runs(self):
        research = self.repo/'grimoire/tomes';research.mkdir()
        foreign = self.outer/'foreign.md';foreign.write_text('outside the audit boundary')
        (research/'redirect.md').symlink_to(foreign)
        session = self.success(self.command('start'))
        other = self.success(self.command('start'))
        private = Path(other['paths']['reports'])/'private.md';private.write_text('another run')
        paths = [foreign, research/'redirect.md', private, self.repo/'source.txt']
        for source in paths:
            before = snapshot(self.outer)
            result = self.command('read-reference', '--run-id', session['run_id'], '--path', source)
            self.assertNotEqual(0, result.returncode, str(source))
            self.assertEqual(before, snapshot(self.outer))

    def test_redirected_shared_context_is_reported_unavailable_without_reading_it(self):
        foreign = self.outer/'foreign.md';foreign.write_text('outside the audit boundary')
        context = self.repo/'GRIMOIRE.md';context.unlink();context.symlink_to(foreign)
        before = snapshot(self.repo)
        session = self.success(self.command('start'))
        self.assertNotIn(str(context), session['shared_references']['contexts'])
        self.assertIn(str(context), session['shared_references']['unavailable'])
        after = snapshot(self.repo)
        self.assertEqual(before, {key: after[key] for key in before})
