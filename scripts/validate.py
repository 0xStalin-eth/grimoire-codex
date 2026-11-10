#!/usr/bin/env python3
"""Validate packaging, references, syntax, ownership and deterministic generation (not model behavior)."""
import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from sync import ROOT, BANNED, actual_managed, build, check_ownership, guard_root, manifest, metadata


def validate(root=ROOT):
    root = guard_root(root)
    state = check_ownership(root)
    if not state:
        raise ValueError('no synchronized snapshot')
    vendor = {}
    for name, value in actual_managed(root).items():
        if name.startswith('vendor/upstream/'):
            vendor[name[len('vendor/upstream/'):]] = value
    generated = build(root, vendor)
    if manifest(generated) != state['managed']:
        raise ValueError('generated files drifted from current adapters; run scripts/sync.py')
    errors = []
    skills = sorted((root / 'skills').glob('*/SKILL.md'))
    names = set()
    shell_count = python_count = 0
    for p in skills:
        name, desc, _ = metadata(p.read_text())
        if name != p.parent.name or name in names or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
            errors.append(f'invalid/duplicate skill metadata: {p}')
        names.add(name)
        if not desc or len(desc) > 1024 or '<' in desc or '>' in desc:
            errors.append(f'invalid description: {name}')
        link = root / '.agents/skills' / name
        if not link.is_symlink() or link.resolve() != p.parent.resolve():
            errors.append(f'discovery link missing or wrong: {name}')
    expected = {p.parent.name for p in skills}
    if {p.name for p in (root / '.agents/skills').iterdir()} != expected:
        errors.append('extra/missing discovery entries')
    for base in [root / 'skills', root / 'agents', root / 'scripts']:
        for p in sorted(base.rglob('*')):
            if p.is_symlink():
                if not p.exists() or not p.resolve().is_relative_to(root):
                    errors.append(f'broken/escaping symlink: {p}')
                continue
            if not p.is_file():
                continue
            if p.suffix == '.py':
                try:
                    ast.parse(p.read_text(), filename=str(p))
                    python_count += 1
                except SyntaxError as exc:
                    errors.append(str(exc))
            elif p.suffix == '.sh':
                result = subprocess.run(['bash', '-n', str(p)], capture_output=True, text=True)
                if result.returncode:
                    errors.append(f'{p}: {result.stderr}')
                shell_count += 1
                if not p.name.startswith('_') and not os.access(p, os.X_OK):
                    errors.append(f'non-executable helper: {p}')
            elif p.suffix == '.md':
                text = p.read_text()
                # CODEX.md explains the old platform; generated workflow bodies must be resolved.
                if p.name != 'CODEX.md' and BANNED.search(text):
                    errors.append(f'unresolved platform instruction: {p}')
                prose = re.sub(r'```[\s\S]*?```|`[^`\n]*`', '', text)
                for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^\s)]+)\)', prose):
                    if re.match(r'\w+:|#|\$|<', target) or any(x in target for x in ['{', '*', '...', '<', '…']):
                        continue
                    target = target.split('#')[0].replace('%20', ' ')
                    if target and not (p.parent / target).exists() and not (root / target).exists():
                        errors.append(f'broken Markdown reference: {p.relative_to(root)} -> {target}')
                if p.name == 'SKILL.md':
                    for target in re.findall(r'`((?:references|examples)/[\w./-]+)`', text):
                        if not (p.parent / target).exists():
                            errors.append(f'missing skill resource: {p.relative_to(root)} -> {target}')
                for target in re.findall(r'(?<![\w./-])(?:skills|agents)/[\w./-]+', text):
                    concrete = target.endswith('/') or '.' in Path(target).name
                    if concrete and '...' not in target and not (root / target).exists():
                        errors.append(f'missing shared resource: {p.relative_to(root)} -> {target}')
    for command in ('python3', 'bash', 'git'):
        if not shutil.which(command):
            errors.append(f'missing validation dependency: {command}')
    if errors:
        raise ValueError('\n'.join(errors))
    return {'skills': len(skills), 'bash_syntax_checked': shell_count, 'python_syntax_checked': python_count,
            'upstream_sha': state['upstream_sha'], 'model_runtime_tested': False}


def main():
    try:
        print(json.dumps(validate(), indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'VALIDATION FAILED: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
