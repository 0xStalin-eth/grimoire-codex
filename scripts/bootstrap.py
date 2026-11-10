#!/usr/bin/env python3
"""Explicit replacement for the personal-store init hook; never touches source repositories."""
import argparse
from pathlib import Path
import os
import subprocess


def bootstrap(path):
    path = Path(path).expanduser().resolve()
    # Refuse initializing a personal store inside any existing source repository.
    probe = subprocess.run(['git', '-C', str(path if path.exists() else path.parent), 'rev-parse', '--show-toplevel'],
                           capture_output=True, text=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    if probe.returncode == 0 and Path(probe.stdout.strip()).resolve() != path:
        raise ValueError('personal store must not be nested inside a source repository')
    if (path / 'codex/project.json').exists() or (path / '.claude-plugin/plugin.json').exists():
        raise ValueError('REFUSED: personal store path is a toolkit checkout')
    for suffix in ['librarian/library', 'librarian/qdrant', 'librarian/cache', 'sigils/archived', 'knowledge']:
        target = path / suffix
        if target.is_symlink() or not target.resolve().is_relative_to(path):
            raise ValueError(f'unsafe store directory: {target}')
        target.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', 'init', '-q', str(path)], check=True)
    registry = path / 'librarian/library/libraries.yaml'
    try:
        with registry.open('x') as f:
            f.write('libraries: {}\n')
    except FileExistsError:
        pass
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', default=os.environ.get('GRIMOIRE_HOME', '~/.grimoire'))
    args = parser.parse_args()
    print(bootstrap(args.home))
