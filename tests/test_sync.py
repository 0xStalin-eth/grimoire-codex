import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import sync


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE).decode().strip()


def commit(root):
    git(root, 'add', '-A')
    git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')


def tree(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='grimoire-test-')
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name).resolve()
        self.source = base / 'source'
        self.root = base / 'downstream'
        self.source.mkdir(); self.root.mkdir()
        git(self.source, 'init', '-q')
        skill = self.source / 'skills/alpha'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text('---\nname: alpha\ndescription: Inspect fixture code.\nuser_invocable: true\n---\n# Alpha\n\n1. Inspect.\n2. Verify.\n')
        (skill / 'asset.txt').write_text('original\n')
        commit(self.source)
        (self.root / 'codex').mkdir()
        (self.root / 'codex/project.json').write_text((sync.ROOT / 'codex/project.json').read_text())
        (self.root / 'codex/runtime.md').write_text('Codex fixture adapter.\n')
        (self.root / 'codex/maintenance.md').write_text('Fixture maintenance.\n')
        (self.root / 'codex/reviewed.json').write_text(json.dumps({'entrypoints': ['skills/alpha/SKILL.md'], 'commands': [], 'command_descriptions': {}}))
        (self.root / 'codex/patches.json').write_text('{}')

    def run_sync(self):
        return sync.synchronize(self.root, self.source)

    def test_idempotent_and_source_files_and_git_metadata_unchanged(self):
        before = tree(self.source)
        first = self.run_sync()
        state = (self.root / 'sync-state.json').read_bytes()
        second = self.run_sync()
        self.assertTrue(first['changed_files'])
        self.assertEqual([], second['changed_files'])
        self.assertEqual(state, (self.root / 'sync-state.json').read_bytes())
        self.assertEqual(before, tree(self.source))
        self.assertEqual((self.root / '.agents/skills/alpha').resolve(), self.root / 'skills/alpha')

    def test_tracked_upstream_bytecode_is_archived_and_survives_a_clean_clone(self):
        name = 'skills/alpha/__pycache__/module.cpython-311.pyc'
        bytecode = self.source/name
        bytecode.parent.mkdir();bytecode.write_bytes(b'\x80\x81tracked upstream cache fixture')
        git(self.source, 'add', '-f', name);commit(self.source)
        self.run_sync()
        self.assertEqual(bytecode.read_bytes(), (self.root/'vendor/upstream'/name).read_bytes())
        self.assertFalse((self.root/name).exists())
        # Match real packaging: global cache ignores must not drop exact archive blobs.
        (self.root/'.gitignore').write_bytes((sync.ROOT/'.gitignore').read_bytes())
        git(self.root, 'init', '-q');commit(self.root)
        clone = self.root.parent/'clean-clone'
        git(self.root, 'clone', '-q', str(self.root), str(clone))
        self.assertEqual(bytecode.read_bytes(), (clone/'vendor/upstream'/name).read_bytes())
        self.assertFalse((clone/name).exists())
        sync.check_ownership(clone)
        self.assertEqual([], sync.synchronize(clone, self.source, check=True)['changed_files'])

    def test_shared_updates_deletions_and_rename_preserve_overlay(self):
        self.run_sync()
        overlay = self.root / 'codex/custom.txt'
        overlay.write_text('must survive')
        old = self.source / 'skills/alpha/asset.txt'
        old.rename(old.with_name('renamed.txt'))
        commit(self.source)
        result = self.run_sync()
        self.assertIn('skills/alpha/asset.txt', result['deleted_files'])
        self.assertFalse((self.root / 'skills/alpha/asset.txt').exists())
        self.assertEqual('original\n', (self.root / 'skills/alpha/renamed.txt').read_text())
        self.assertEqual('must survive', overlay.read_text())

    def test_neutral_workflow_updates_keep_stages(self):
        self.run_sync()
        p = self.source / 'skills/alpha/SKILL.md'
        p.write_text(p.read_text() + '3. Report evidence.\n')
        commit(self.source); self.run_sync()
        self.assertIn('3. Report evidence.', (self.root / 'skills/alpha/SKILL.md').read_text())

    def test_directory_to_file_transition_removes_only_obsolete_content(self):
        folder = self.source/'skills/alpha/resource'
        folder.mkdir();(folder/'old.txt').write_text('old')
        commit(self.source);self.run_sync()
        (folder/'old.txt').unlink();folder.rmdir();folder.write_text('replacement file')
        commit(self.source);self.run_sync()
        self.assertEqual('replacement file',(self.root/'skills/alpha/resource').read_text())

    def test_uncommitted_source_content_is_not_imported(self):
        self.run_sync()
        (self.source / 'skills/alpha/asset.txt').write_text('dirty upstream working tree')
        (self.source / 'secret.env').write_text('not a credential fixture')
        self.assertEqual([], self.run_sync()['changed_files'])
        self.assertFalse((self.root / 'vendor/upstream/secret.env').exists())

    def test_snapshot_ignores_git_export_attributes(self):
        (self.source / '.gitattributes').write_text('skills/alpha/asset.txt export-ignore\n')
        commit(self.source);self.run_sync()
        self.assertEqual('original\n', (self.root/'vendor/upstream/skills/alpha/asset.txt').read_text())

    def test_metadata_normalization_preserves_workflow_placeholders(self):
        p = self.source/'skills/alpha/SKILL.md'
        p.write_text(p.read_text().replace('Inspect fixture code.', 'Inspect issue <N>.') + '3. Check <N> paths.\n')
        commit(self.source);self.run_sync()
        text = (self.root/'skills/alpha/SKILL.md').read_text()
        self.assertIn('Inspect issue N.', text)
        self.assertIn('3. Check <N> paths.', text)

    def test_managed_edit_is_conflict_before_any_write(self):
        self.run_sync()
        p = self.root / 'skills/alpha/SKILL.md'
        p.write_text(p.read_text() + 'hand edit')
        before = tree(self.root)
        with self.assertRaisesRegex(ValueError, 'managed content conflict'):
            self.run_sync()
        self.assertEqual(before, tree(self.root))

    def test_hash_pinned_patch_conflict_is_atomic(self):
        name = 'skills/alpha/asset.txt'
        data = (self.source / name).read_bytes()
        patch = {name: {'source_sha256': sync.digest(data), 'edits': [{'old': 'original', 'new': 'adapted', 'count': 1}]}}
        (self.root / 'codex/patches.json').write_text(json.dumps(patch))
        self.run_sync()
        before = tree(self.root)
        (self.source / name).write_text('upstream changed')
        commit(self.source)
        with self.assertRaisesRegex(ValueError, 'adaptation conflict'):
            self.run_sync()
        self.assertEqual(before, tree(self.root))
        self.assertEqual('adapted\n', (self.root / 'skills/alpha/asset.txt').read_text())

    def test_skill_deletion_or_addition_requires_review(self):
        self.run_sync()
        git(self.source, 'rm', '-r', 'skills/alpha')
        commit(self.source)
        with self.assertRaisesRegex(ValueError, 'entrypoint addition/removal/rename'):
            self.run_sync()

    def test_new_platform_instruction_fails(self):
        p = self.source / 'skills/alpha/SKILL.md'
        p.write_text(p.read_text() + 'Use $CLAUDE_CODE_SESSION_ID.\n')
        commit(self.source)
        with self.assertRaisesRegex(ValueError, 'unresolved platform instruction'):
            self.run_sync()
        self.assertFalse((self.root / 'sync-state.json').exists())

    def test_concurrent_lock_refuses(self):
        (self.root / '.sync.lock').mkdir()
        with self.assertRaisesRegex(ValueError, 'holds .sync.lock'):
            self.run_sync()

    def test_safe_relative_resource_symlink_preserved(self):
        (self.source / 'skills/alpha/link.txt').symlink_to('asset.txt')
        commit(self.source); self.run_sync()
        self.assertEqual('original\n', (self.root / 'skills/alpha/link.txt').read_text())
        self.assertTrue((self.root / 'vendor/upstream/skills/alpha/link.txt').is_symlink())

    def test_escape_symlink_rejected(self):
        (self.source / 'skills/alpha/link.txt').symlink_to('../../../outside')
        commit(self.source)
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            self.run_sync()

    def test_upstream_remote_in_downstream_target_refused(self):
        git(self.root, 'init', '-q')
        git(self.root, 'remote', 'add', 'origin', sync.UPSTREAM)
        with self.assertRaisesRegex(ValueError, 'canonical upstream remote'):
            self.run_sync()

    def test_unknown_metadata_requires_review(self):
        p = self.source / 'skills/alpha/SKILL.md'
        p.write_text(p.read_text().replace('user_invocable: true', 'context: fork'))
        commit(self.source)
        with self.assertRaisesRegex(ValueError, 'metadata requires review'):
            self.run_sync()

    def test_missing_reference_and_script_syntax_fail_validation(self):
        import validate
        p=self.source/'skills/alpha/SKILL.md'
        p.write_text(p.read_text()+'Read [missing](references/missing.md).\n')
        script=self.source/'skills/alpha/helper.sh'
        script.write_text('#!/bin/bash\nif broken syntax\n');script.chmod(0o755)
        commit(self.source);self.run_sync()
        with self.assertRaisesRegex(ValueError,'broken Markdown reference'):
            validate.validate(self.root)
