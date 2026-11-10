#!/usr/bin/env python3
"""Owned, per-run Codex reports and PoCs; every write stays inside the audit launch directory."""
import argparse
import glob
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid


def no_links(path, boundary):
    path = Path(os.path.abspath(path))
    if not path.is_relative_to(boundary):
        raise ValueError('path leaves the audit launch directory')
    for parent in [path, *path.parents]:
        if parent.is_symlink():
            raise ValueError(f'symlink in artifact path: {parent}')
        if parent == boundary:
            break
    return path


class Artifacts:
    def __init__(self):
        launch = os.environ.get('GRIMOIRE_AUDIT_ROOT', '')
        self.sid = os.environ.get('GRIMOIRE_SESSION_ID', '')
        if not launch or not os.path.isabs(launch) or not Path(launch).is_dir():
            raise ValueError('GRIMOIRE_AUDIT_ROOT must be the absolute Codex launch directory')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{7,63}', self.sid):
            raise ValueError('GRIMOIRE_SESSION_ID is missing or malformed')
        self.launch = Path(launch).resolve()
        result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], check=True, capture_output=True,
                                text=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
        self.workspace = Path(result.stdout.strip()).resolve()
        if not self.workspace.is_relative_to(self.launch):
            raise ValueError('Git root is above/outside the Codex launch directory')
        remotes = subprocess.run(['git', 'remote', '-v'], cwd=self.workspace, check=True,
                                 capture_output=True, text=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0')).stdout
        if re.search(r'github\.com[:/]0xStalin-eth/grimoire(?:\.git)?(?:\s|$)', remotes, re.I):
            raise ValueError('the canonical Claude Grimoire repository is strictly read-only')
        self.root = no_links(self.workspace/'grimoire-codex'/self.sid, self.launch)
        self.copies = no_links(self.workspace/'.isolated-codex'/self.sid, self.launch)
        self.expected = {'runtime': 'codex', 'session': self.sid, 'workspace': str(self.workspace),
                         'audit_root': str(self.launch)}

    def owner(self, root, artifacts=False):
        no_links(root/'.owner', self.launch)
        data = json.loads((root/'.owner').read_text())
        expected = self.expected | ({'kind': 'reports-and-pocs'} if artifacts else {})
        if not isinstance(data, dict) or any(data.get(k) != value for k, value in expected.items()):
            raise ValueError(f'foreign/unmarked Codex ownership: {root}')

    def initialize(self):
        if self.root.exists():
            self.owner(self.root, artifacts=True)
        else:
            self.root.parent.mkdir(parents=True, exist_ok=True)
            self.root.mkdir()  # An existing unmarked directory must never be adopted.
            with (self.root/'.owner').open('x') as stream:
                json.dump(self.expected | {'kind': 'reports-and-pocs'}, stream, indent=2)
        for rel in ['pocs/peer-review', 'pocs/mitigation-review', 'peer-review/WIP',
                    'mitigation-review/WIP', 'findings/WIP', 'findings/original-findings']:
            no_links(self.root/rel, self.launch).mkdir(parents=True, exist_ok=True)
        return self.paths()

    def paths(self):
        self.owner(self.root, artifacts=True)
        return {'reports': str(self.root), 'context': str(self.root/'GRIMOIRE.md'),
                'pocs': str(self.root/'pocs'), 'poc-relative': (self.root/'pocs').relative_to(self.workspace).as_posix(),
                'peer-pocs': str(self.root/'pocs/peer-review'),
                'mitigation-pocs': str(self.root/'pocs/mitigation-review'),
                'mirror': str(self.root/'findings/original-findings')}

    def output(self, value, reports_only=False):
        path = no_links(Path(value), self.launch)
        if path.is_relative_to(self.root) and path != self.root:
            self.owner(self.root, artifacts=True)
            return path
        if not reports_only and path.is_relative_to(self.copies) and path != self.copies:
            self.owner(self.copies)
            return path
        raise ValueError(f'output must be inside this run’s grimoire-codex or .isolated-codex directory: {path}')

    def source(self, value):
        path = Path(value).resolve()
        if not path.is_relative_to(self.workspace) or not path.is_file():
            raise ValueError('source must be an existing file inside the audit Git workspace')
        return path

    def write(self, output, data, replace=False):
        output = self.output(output)
        if output.name == '.owner':
            raise ValueError('ownership markers cannot be replaced')
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('wb' if replace else 'xb') as stream:
            stream.write(data)
        return output

    def run_forge(self, name, suites=(), source=None, ref=None):
        self.owner(self.root, artifacts=True)
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', name):
            raise ValueError('copy name must contain only letters, digits, hyphens or underscores')
        if source:
            file = self.output(source, reports_only=True)
            if not file.is_relative_to(self.root/'pocs') or not file.is_file():
                raise ValueError('build input must be a PoC/snapshot from this Codex run')
        else:
            if not suites:
                raise ValueError('at least one PoC suite is required')
            for suite in suites:
                prefix = self.paths()['poc-relative']+'/'
                if not suite.startswith(prefix) or '..' in Path(suite).parts:
                    raise ValueError('PoC suites must be relative paths inside this run’s PoC directory')
                if not any(p.endswith('.t.sol') for p in glob.glob(str(self.workspace/suite), recursive=True)):
                    raise ValueError('PoC suite matches no .t.sol test files')
        helper = Path(__file__).resolve().parents[1]/'skills/peer-review/scripts/isolated-workspace.sh'
        def isolation(*args):
            return subprocess.run(['bash', str(helper), *args], cwd=self.workspace,
                                  capture_output=True, text=True, check=True).stdout.strip()
        desired = subprocess.run(['git', 'rev-parse', (ref or 'HEAD')+'^{commit}'], cwd=self.workspace,
                                 env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'), check=True,
                                 capture_output=True, text=True).stdout.strip()
        session = Path(isolation('session'))
        copy = session/name
        if copy.exists():
            if json.loads((copy/'.isolated-state.json').read_text())['ref'] != desired:
                raise ValueError('existing copy uses a different commit; select a new copy name')
            isolation('sync', name)
        else:
            isolation('create', name, '--ref', desired)
        copy = Path(isolation('path', name))
        work = Path(isolation('work', 'forge-'+name))
        for folder in ['tmp', 'out', 'cache']:
            self.output(work/folder).mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, TMPDIR=str(work/'tmp'), FOUNDRY_TEST=self.paths()['poc-relative'])
        for setting, folder in {'BUILD_INFO_PATH': 'build-info', 'SNAPSHOTS': 'snapshots',
                                'FUZZ_FAILURE_PERSIST_DIR': 'fuzz', 'INVARIANT_FAILURE_PERSIST_DIR': 'invariant',
                                'FUZZ_CORPUS_DIR': 'fuzz-corpus', 'INVARIANT_CORPUS_DIR': 'invariant-corpus'}.items():
            env['FOUNDRY_'+setting] = str(self.output(work/folder))
        command = ['forge', 'build' if source else 'test', '--root', str(copy),
                   '--out', str(work/'out'), '--cache-path', str(work/'cache'), '--offline']
        if not source:
            command.append('--no-storage-caching')
        logs = self.root/'runs'/name/uuid.uuid4().hex
        def execute(arguments, index, test=False):
            result = subprocess.run(command+arguments, cwd=copy, env=env, capture_output=True)
            self.write(logs/f'{index}.stdout', result.stdout)
            self.write(logs/f'{index}.stderr', result.stderr)
            sys.stdout.buffer.write(result.stdout);sys.stdout.buffer.flush()
            sys.stderr.buffer.write(result.stderr);sys.stderr.buffer.flush()
            if result.returncode:
                return result.returncode
            if test:
                try:
                    data = json.loads(result.stdout)
                    tests = [value for suite in data.values() for value in suite.get('test_results', {}).values()]
                    if any(test.get('status') == 'Failure' for test in tests):
                        return 1
                    count = sum(test.get('status') == 'Success' for test in tests)
                except (ValueError, AttributeError, TypeError):
                    raise ValueError('Forge produced no usable JSON test evidence; inspect the saved raw output')
                if not count:
                    raise ValueError('Forge executed zero tests; no reproduction established')
            return 0
        if source:
            return execute([file.relative_to(self.workspace).as_posix()], 'build')
        for index, suite in enumerate(suites, 1):
            code = execute(['--match-path', suite, '--json'], str(index), test=True)
            if code:
                return code
        return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    path = sub.add_parser('path')
    path.add_argument('kind', choices=['reports', 'context', 'pocs', 'poc-relative', 'peer-pocs', 'mitigation-pocs', 'mirror'])
    guard = sub.add_parser('guard-output')
    guard.add_argument('paths', nargs='+')
    guard.add_argument('--reports-only', action='store_true')
    write = sub.add_parser('write')
    write.add_argument('output')
    write.add_argument('--source', help='copy an explicitly supplied input; otherwise read bytes from stdin')
    write.add_argument('--replace', action='store_true', help='update an existing file in this run only')
    move = sub.add_parser('move')
    move.add_argument('source');move.add_argument('output')
    for action in ['test', 'build']:
        run = sub.add_parser(action)
        run.add_argument('--name', required=True)
        run.add_argument('--ref', help='explicit pre/post-fix commit; defaults to HEAD')
        if action == 'test':
            run.add_argument('--suite', action='append', required=True)
        else:
            run.add_argument('--file', required=True)
    args = parser.parse_args()
    try:
        artifacts = Artifacts()
        if args.command == 'init':
            print(json.dumps(artifacts.initialize(), indent=2))
        elif args.command == 'path':
            print(artifacts.paths()[args.kind])
        elif args.command == 'guard-output':
            for path in args.paths:
                artifacts.output(path, args.reports_only)
        elif args.command == 'write':
            # Validate the destination before reading an input or creating output directories.
            artifacts.output(args.output)
            data = artifacts.source(args.source).read_bytes() if args.source else sys.stdin.buffer.read()
            print(artifacts.write(args.output, data, args.replace))
        elif args.command == 'move':
            source = artifacts.output(args.source)
            destination = artifacts.output(args.output)
            if source.name == '.owner' or destination.name == '.owner':
                raise ValueError('ownership markers cannot be moved')
            artifacts.write(destination, source.read_bytes())  # exclusive destination, then remove our source
            source.unlink()
            print(destination)
        elif args.command in ['test', 'build']:
            return artifacts.run_forge(args.name, suites=getattr(args, 'suite', ()),
                                       source=getattr(args, 'file', None), ref=args.ref)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'REFUSED: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
