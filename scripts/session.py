#!/usr/bin/env python3
"""Agent-invoked session setup: inspect Git and create a fresh audit-local Codex run."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

# The installed toolkit may be outside the audit's writable boundary.
sys.dont_write_bytecode = True
from review_artifacts import Artifacts, no_links


def checkout():
    def git(*args):
        return subprocess.check_output(
            ['git', '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false', *args],
            env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'), stderr=subprocess.PIPE, text=True).rstrip('\n')
    return {'head': git('rev-parse', '--verify', 'HEAD'),
            'status': git('status', '--porcelain=v1', '--untracked-files=normal')}


def shared_references(artifacts):
    """Discover Claude research as optional inputs; never create or change its files."""
    found = {'access': 'read-only', 'contexts': [], 'research': [], 'tomes': [], 'unavailable': []}
    for base in dict.fromkeys([artifacts.launch, artifacts.workspace]):
        for kind, relative in [('contexts', 'GRIMOIRE.md'), ('research', 'grimoire'), ('tomes', 'grimoire/tomes')]:
            path = base/relative
            try:
                no_links(path, artifacts.launch)
            except ValueError:
                found['unavailable'].append(str(path))
                continue
            exists = path.is_file() if kind == 'contexts' else path.is_dir()
            if exists:
                found[kind].append(str(path))
    return found


def read_reference(artifacts, value):
    path = no_links(Path(value), artifacts.launch)
    shared = shared_references(artifacts)
    permitted = str(path) in shared['contexts'] or any(path.is_relative_to(Path(p)) for p in shared['research'])
    if not permitted or not path.is_file() or path.suffix.lower() != '.md':
        raise ValueError('reference must be a Markdown file in the audit’s shared GRIMOIRE.md or grimoire/ research')
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'content': data.decode('utf-8')}


def setup(audit_root, run_id=None):
    launch = Path(audit_root)
    if not launch.is_absolute() or not launch.is_dir():
        raise ValueError('audit root must be the original absolute Codex launch directory')
    # Never inherit a previous terminal's ID or a stale/broader audit boundary.
    os.environ['GRIMOIRE_AUDIT_ROOT'] = str(launch.resolve())
    os.environ['GRIMOIRE_SESSION_ID'] = run_id if run_id is not None else str(uuid.uuid4())
    artifacts = Artifacts()
    current = checkout()  # All read-only checks finish before creating output.
    record = artifacts.root/'session.json'
    if run_id is None:
        if artifacts.root.exists():
            raise ValueError('new run directory already exists; it will not be adopted')
        paths = artifacts.initialize()
        saved = {'schema_version': 1, 'runtime': 'codex', 'run_id': artifacts.sid,
                 'audit_root': str(artifacts.launch), 'workspace': str(artifacts.workspace),
                 'checkout_at_start': current, 'paths': paths}
        artifacts.write(record, (json.dumps(saved, indent=2)+'\n').encode())
    else:
        artifacts.output(record, reports_only=True)
        saved = json.loads(record.read_text())
        expected = {'schema_version': 1, 'runtime': 'codex', 'run_id': artifacts.sid,
                    'audit_root': str(artifacts.launch), 'workspace': str(artifacts.workspace),
                    'paths': artifacts.paths()}
        if not isinstance(saved, dict) or any(saved.get(key) != value for key, value in expected.items()):
            raise ValueError('session record does not match this run and audit launch directory')
        if not isinstance(saved.get('checkout_at_start'), dict):
            raise ValueError('session record has no original checkout evidence')
    return dict(saved, session_file=str(record), checkout_now=current, shared_references=shared_references(artifacts),
                environment={'GRIMOIRE_AUDIT_ROOT': str(artifacts.launch),
                             'GRIMOIRE_SESSION_ID': artifacts.sid,
                             'GRIMOIRE_CODEX_POC_REL': saved['paths']['poc-relative']})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['start', 'resume', 'read-reference']:
        action = sub.add_parser(name)
        action.add_argument('--audit-root', default=str(Path.cwd()),
                            help='original absolute runtime launch directory; never a broader Git root')
        if name != 'start':
            action.add_argument('--run-id', required=True, help='own run ID already recorded in this chat')
        if name == 'read-reference':
            action.add_argument('--path', required=True, help='shared context or research Markdown file to read')
    args = parser.parse_args()
    try:
        result = setup(args.audit_root, getattr(args, 'run_id', None))
        if args.command == 'read-reference':
            result = read_reference(Artifacts(), args.path)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'REFUSED: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
