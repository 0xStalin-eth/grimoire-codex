#!/usr/bin/env python3
"""Publish already validated generated changes to the downstream's dedicated sync PR only."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from sync import ROOT, MANAGED, guard_root

REPO = '0xStalin-eth/grimoire-codex'
BRANCH = 'automation/sync-upstream'
BOT = '41898282+github-actions[bot]@users.noreply.github.com'
MARKER = 'Grimoire-Sync-Managed: true'


def call(*args, capture=True, check=True):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=capture, check=check)


def managed_path(path):
    return path == 'sync-state.json' or any(path.startswith(p) for p in MANAGED)


def status_paths(status):
    records = iter(status.rstrip('\0').split('\0')) if status else iter(())
    paths = []
    for record in records:
        paths.append(record[3:])
        if 'R' in record[:2] or 'C' in record[:2]:
            paths.append(next(records))
    return paths


def main():
    guard_root(ROOT)
    if os.environ.get('GITHUB_REPOSITORY', '').lower() != REPO.lower():
        raise ValueError('REFUSED: publishing is restricted to the configured downstream repository')
    remote = call('git', 'remote', 'get-url', 'origin').stdout.strip()
    if remote not in [f'https://github.com/{REPO}.git', f'https://github.com/{REPO}']:
        raise ValueError('REFUSED: unexpected origin')
    call('gh', 'auth', 'setup-git')
    default = json.loads(call('gh', 'api', f'repos/{REPO}').stdout)['default_branch']
    if not re.fullmatch(r'[A-Za-z0-9._/-]+', default) or default.startswith('-'):
        raise ValueError('invalid downstream default branch')
    # Rebase from the current default branch next run if it moved during preparation.
    current = call('git', 'rev-parse', 'HEAD').stdout.strip()
    call('git', 'fetch', '--no-tags', 'origin', default)
    if call('git', 'rev-parse', 'FETCH_HEAD').stdout.strip() != current:
        raise ValueError('default branch advanced during generation; retry sync')
    status = call('git', 'status', '--porcelain=v1', '-z', '--untracked-files=all').stdout
    paths = status_paths(status)
    if any(not managed_path(p) for p in paths):
        raise ValueError('REFUSED: non-managed local changes present')
    if not paths:
        print('No changes; no PR needed.')
        return 0
    result = call('git', 'ls-remote', '--heads', 'origin', BRANCH)
    old_sha = result.stdout.split()[0] if result.stdout.strip() else ''
    if old_sha:
        call('git', 'fetch', '--no-tags', 'origin', BRANCH)
        for sha in call('git', 'rev-list', f'HEAD..{old_sha}').stdout.splitlines():
            message = call('git', 'show', '-s', '--format=%B', sha).stdout
            author = call('git', 'show', '-s', '--format=%ae', sha).stdout.strip()
            if MARKER not in message or author != BOT:
                raise ValueError('sync branch contains non-bot work; resolve manually, do not overwrite')
            changed = call('git', 'diff-tree', '--no-commit-id', '--name-only', '-z', '-r', sha).stdout.rstrip('\0').split('\0')
            if any(not managed_path(p) for p in changed):
                raise ValueError('sync branch contains non-managed changes')
    call('git', 'add', '-A', '--', 'vendor/upstream', 'skills', 'agents', '.agents/skills', 'sync-state.json')
    new_tree = call('git', 'write-tree').stdout.strip()
    if old_sha and call('git', 'rev-parse', f'{old_sha}^{{tree}}').stdout.strip() == new_tree:
        print('Existing synchronization PR already contains this tree.')
        return 0
    state = json.loads((ROOT / 'sync-state.json').read_text())
    upstream_sha = state['upstream_sha']
    call('git', 'config', 'user.name', 'github-actions[bot]')
    call('git', 'config', 'user.email', BOT)
    call('git', 'checkout', '-b', BRANCH)
    # Structured text file prevents shell interpolation of Markdown or upstream filenames.
    summary = call('git', 'diff', '--cached', '--stat').stdout
    message = f'chore(sync): upstream {upstream_sha[:12]}\n\nUpstream-SHA: {upstream_sha}\n{MARKER}\n'
    with tempfile.TemporaryDirectory(prefix='grimoire-pr-') as temp:
        msg = Path(temp) / 'commit.txt'
        msg.write_text(message)
        call('git', 'commit', '--file', str(msg))
        call('git', 'push', f'--force-with-lease=refs/heads/{BRANCH}:{old_sha}', 'origin', f'HEAD:refs/heads/{BRANCH}')
        body = Path(temp) / 'body.md'
        body.write_text(f'Updates the downstream snapshot and generated Codex skills to '
                        f'[upstream {upstream_sha}](https://github.com/0xStalin-eth/grimoire/commit/{upstream_sha}).\n\n'
                        'Structural validation and synchronization tests ran before this PR was published. '
                        'Model execution and workflow equivalence are not established by these checks. '
                        'Review adapted behavior before merging. No automatic merge.\n\n'
                        f'```text\n{summary[:30000]}\n```\n\n'
                        'All retrieval was read-only. No upstream repository configuration is required.\n')
        prs = json.loads(call('gh', 'pr', 'list', '--repo', REPO, '--head', BRANCH, '--state', 'open', '--json', 'number').stdout)
        title = f'chore(sync): Grimoire {upstream_sha[:12]}'
        if prs:
            call('gh', 'pr', 'edit', str(prs[0]['number']), '--repo', REPO, '--title', title, '--body-file', str(body))
        else:
            call('gh', 'pr', 'create', '--repo', REPO, '--base', default, '--head', BRANCH, '--title', title, '--body-file', str(body))
    print(f'Updated downstream sync PR for {upstream_sha}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'PR PUBLICATION FAILED: {exc}', file=sys.stderr)
        sys.exit(1)
