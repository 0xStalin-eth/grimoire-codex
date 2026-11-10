#!/usr/bin/env python3
"""Install all generated skills into an engagement's Codex discovery directory with no overwrites."""
import argparse
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def install(project):
    project = Path(project).expanduser().resolve()
    if not project.is_dir():
        raise ValueError('engagement project directory must already exist')
    for parent in [project, *project.parents]:
        if (parent / '.claude-plugin/plugin.json').exists():
            raise ValueError('REFUSED: destination is in a Claude toolkit checkout')
        if (parent / '.git').exists():
            result = subprocess.run(['git', '-C', str(parent), 'remote', '-v'], text=True, capture_output=True,
                                    check=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
            if re.search(r'github\.com[:/]0xStalin-eth/grimoire(?:\.git)?\s', result.stdout, re.I):
                raise ValueError('REFUSED: destination is in canonical upstream')
            break
    directory = project / '.agents/skills'
    if not directory.resolve().is_relative_to(project):
        raise ValueError('discovery directory must stay inside the engagement')
    links = [(directory / p.name, p.resolve()) for p in sorted((ROOT / 'skills').iterdir()) if (p / 'SKILL.md').is_file()]
    for link, target in links:
        if (link.exists() or link.is_symlink()) and (not link.is_symlink() or link.resolve() != target):
            raise ValueError(f'collision: {link}; existing content was not changed')
    directory.mkdir(parents=True, exist_ok=True)
    for link, target in links:
        if not link.is_symlink():
            link.symlink_to(target, target_is_directory=True)
    return len(links)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    args = parser.parse_args()
    print(f'Installed {install(args.project)} Codex skills. Restart Codex if they are not visible.')
