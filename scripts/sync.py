#!/usr/bin/env python3
"""Read-only upstream retrieval; explicit downstream generation with ownership checks."""
import argparse
import hashlib
import io
import json
import os
import posixpath
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = 'https://github.com/0xStalin-eth/grimoire.git'
MANAGED = ('vendor/upstream/', 'skills/', 'agents/', '.agents/skills/')
BANNED = re.compile(r'CLAUDE_|Claude Code|\bclaude\s+-|mcp__plugin_|\.claude/|grimoire:(?:sigil|familiar)|Task tool|subagent_type|\b(?:WebFetch|WebSearch|ToolSearch|EnterPlanMode|ExitPlanMode|TodoWrite|AskUserQuestion)\b')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(*args, cwd=None, input=None):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0')
    return subprocess.check_output(args, cwd=cwd, env=env, stderr=subprocess.PIPE, input=input)


def safe_path(name):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or not p.parts or '.git' in p.parts:
        raise ValueError(f'unsafe path: {name}')
    return p


def guard_root(root):
    root = Path(root).resolve()
    config = json.loads((root / 'codex/project.json').read_text())
    if config['project'] != 'grimoire-codex' or config['upstream'] != UPSTREAM:
        raise ValueError('REFUSED: downstream marker does not match')
    if (root / '.git').exists():
        remotes = run('git', 'remote', '-v', cwd=root).decode()
        if re.search(r'github\.com[:/]0xStalin-eth/grimoire(?:\.git)?\s', remotes, re.I):
            raise ValueError('REFUSED: canonical upstream remote in write target')
    for prefix in MANAGED:
        cur = root
        for part in PurePosixPath(prefix).parts:
            cur /= part
            if cur.is_symlink():
                raise ValueError(f'REFUSED: managed directory is symlink: {cur}')
    return root


@contextmanager
def lock(root):
    p = root / '.sync.lock'
    try:
        p.mkdir()
    except FileExistsError:
        raise ValueError('another synchronization holds .sync.lock; inspect before removing a stale lock')
    try:
        yield
    finally:
        p.rmdir()


def snapshot(source):
    """Read exact Git blobs: no checkout, attributes filters, hooks or writes in source."""
    sha = run('git', 'rev-parse', 'HEAD', cwd=source).decode().strip()
    tree = run('git', 'ls-tree', '-rz', sha, cwd=source)
    if not tree:
        return sha, {}
    entries = []
    for entry in tree.rstrip(b'\0').split(b'\0'):
        info, path = entry.split(b'\t', 1)
        mode, kind, oid = info.decode().split()
        if kind != 'blob' or mode not in {'100644', '100755', '120000'}:
            raise ValueError(f'upstream link/submodule requires explicit adaptation: {path!r}')
        entries.append((str(safe_path(path.decode())), mode, oid))
    batch = run('git', 'cat-file', '--batch', cwd=source,
                input=('\n'.join(oid for _, _, oid in entries) + '\n').encode())
    stream = io.BytesIO(batch)
    files = {}
    for name, mode, oid in entries:
        header = stream.readline().decode().strip().split()
        if len(header) != 3 or header[:2] != [oid, 'blob']:
            raise ValueError(f'unexpected Git blob response: {name}')
        size = int(header[2])
        if size > 25 * 1024 * 1024:
            raise ValueError(f'oversized upstream file: {name}')
        data = stream.read(size)
        if len(data) != size or stream.read(1) != b'\n':
            raise ValueError(f'truncated Git blob: {name}')
        if mode == '120000':
            link = data.decode()
            target = posixpath.normpath(posixpath.join(posixpath.dirname(name), link))
            safe_path(target)
            if link.startswith('/') or not target.startswith('skills/'):
                raise ValueError(f'unsafe upstream symlink: {name}')
            files[name] = (data, 0o120000)
        else:
            files[name] = (data, 0o755 if mode == '100755' else 0o644)
    return sha, files


def metadata(text, default_name=None, default_description=None):
    """Strict subset used upstream; fail on unfamiliar metadata instead of silently misparsing."""
    if not text.startswith('---\n'):
        if default_name and default_description:
            return default_name, default_description, text
        raise ValueError('missing skill frontmatter')
    head, sep, body = text[4:].partition('\n---\n')
    if not sep:
        raise ValueError('unterminated frontmatter')
    lines = head.splitlines()
    fields = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        match = re.fullmatch(r'([A-Za-z_][\w-]*):\s*(.*)', line)
        if not match:
            raise ValueError(f'unrecognized frontmatter line: {line}')
        key, value = match.groups()
        if key in fields:
            raise ValueError(f'duplicate metadata: {key}')
        if value in ('>-', '>', '|', '|-'):
            values = []
            i += 1
            while i < len(lines) and (lines[i].startswith((' ', '\t')) or not lines[i].strip()):
                values.append(lines[i].strip())
                i += 1
            value = ' '.join(values).strip()
        else:
            i += 1
        fields[key] = value.strip('"\'')
    unknown = set(fields) - {'name', 'description', 'user_invocable', 'tools'}
    if unknown:
        raise ValueError(f'new upstream metadata requires review: {sorted(unknown)}')
    name = default_name or fields.get('name')
    description = default_description or fields.get('description')
    if not name or not description:
        raise ValueError('name and description required')
    return name, description, body


def manifest(files):
    return {name: {'sha256': digest(data), 'mode': mode} for name, (data, mode) in sorted(files.items())}


def actual_managed(root):
    files = {}
    for prefix in MANAGED:
        base = root / prefix
        if not base.exists():
            continue
        for p in base.rglob('*'):
            name = p.relative_to(root).as_posix()
            if p.is_symlink():
                files[name] = (os.readlink(p).encode(), 0o120000)
            elif p.is_file():
                files[name] = (p.read_bytes(), 0o755 if p.stat().st_mode & 0o111 else 0o644)
    return files


def check_ownership(root):
    state_file = root / 'sync-state.json'
    actual = manifest(actual_managed(root))
    if not state_file.exists():
        if actual:
            raise ValueError('unowned managed files exist; refusing initial overwrite')
        return {}
    state = json.loads(state_file.read_text())
    expected = state['managed']
    differences = sorted(k for k in set(actual) | set(expected) if actual.get(k) != expected.get(k))
    if differences:
        raise ValueError('managed content conflict (move customizations to codex/): ' + ', '.join(differences))
    return state


def build(root, upstream):
    review = json.loads((root / 'codex/reviewed.json').read_text())
    edits = json.loads((root / 'codex/patches.json').read_text())
    result = {'vendor/upstream/' + name: value for name, value in upstream.items()}
    inputs = {name: value for name, value in upstream.items() if name.startswith(('skills/', 'agents/'))}
    entrypoints = sorted(name for name in inputs if name.endswith('/SKILL.md') or (name.startswith('agents/') and name.count('/') == 1))
    if entrypoints != review['entrypoints']:
        raise ValueError('entrypoint addition/removal/rename requires review: ' + ', '.join(sorted(set(entrypoints) ^ set(review['entrypoints']))))
    commands = sorted(name for name in upstream if name.startswith('.claude/commands/'))
    if commands != review['commands']:
        raise ValueError('maintenance command inventory changed; review required')
    skill_names = [PurePosixPath(name).parent.name for name in entrypoints if name.endswith('/SKILL.md')]
    skill_names += ['grimoire-' + PurePosixPath(name).stem for name in entrypoints if name.startswith('agents/')]
    skill_names += ['grimoire-' + PurePosixPath(name).stem for name in commands]
    if len(skill_names) != len(set(skill_names)):
        raise ValueError('upstream skill name collides with a generated role or maintenance skill')
    for name, spec in edits.items():
        if name not in upstream or digest(upstream[name][0]) != spec['source_sha256']:
            raise ValueError(f'adaptation conflict: {name}; review upstream diff, update codex/patches.json explicitly')
    runtime = (root / 'codex/runtime.md').read_text()
    prelude = '\n## Codex adapter (read first)\n\nRead [CODEX.md](CODEX.md) before the workflow. Preserve every stage and confirmation gate.\n\n'
    for name, (data, mode) in {**inputs, **{x: upstream[x] for x in commands}}.items():
        if name.endswith('/CODEX.md'):
            raise ValueError(f'upstream name conflicts with adapter resource: {name}')
        if mode == 0o120000:
            result[name] = (data, mode)
            continue
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            if name in edits:
                raise ValueError(f'cannot patch binary {name}')
            result[name] = (data, mode)
            continue
        for edit in edits.get(name, {}).get('edits', []):
            if not edit['old'] or text.count(edit['old']) != edit['count']:
                raise ValueError(f'exact patch no longer applies: {name}: {edit["old"][:70]}')
            text = text.replace(edit['old'], edit['new'])
        if BANNED.search(text):
            raise ValueError(f'unresolved platform instruction in {name}: {BANNED.search(text).group()}')
        if name.endswith('/SKILL.md'):
            skill, desc, body = metadata(text)
            desc = desc.replace('<', '').replace('>', '')
            if skill != PurePosixPath(name).parent.name:
                raise ValueError(f'skill name/directory mismatch: {name}')
            text = f'---\nname: {skill}\ndescription: {json.dumps(desc)}\n---\n' + prelude + body
            result[f'skills/{skill}/CODEX.md'] = (runtime.encode(), 0o644)
        elif name.startswith('agents/') and name.count('/') == 1:
            role, desc, body = metadata(text)
            desc = desc.replace('<', '').replace('>', '')
            text = '# Codex role procedure\n\n' + runtime + '\n' + body
            skill = 'grimoire-' + role
            wrapper = f'---\nname: {skill}\ndescription: {json.dumps(desc)}\n---\n' + prelude + f'Load the installed Grimoire-Codex `agents/{role}.md` and follow its complete procedure.\nIf independent review is requested, use a separate agent context.\n'
            result[f'skills/{skill}/SKILL.md'] = (wrapper.encode(), 0o644)
            result[f'skills/{skill}/CODEX.md'] = (runtime.encode(), 0o644)
        elif name.startswith('.claude/commands/'):
            command = PurePosixPath(name).stem
            desc = review['command_descriptions'][command]
            desc = desc.replace('<', '').replace('>', '')
            skill = 'grimoire-' + command
            _, _, body = metadata(text, skill, desc)
            text = f'---\nname: {skill}\ndescription: {json.dumps(desc)}\n---\n' + prelude + '\n' + (root / 'codex/maintenance.md').read_text() + '\n' + body
            name = f'skills/{skill}/SKILL.md'
            result[f'skills/{skill}/CODEX.md'] = (runtime.encode(), 0o644)
        result[name] = (text.encode(), mode)
    for name in list(result):
        if name.startswith('skills/') and name.endswith('/SKILL.md'):
            skill = PurePosixPath(name).parent.name
            if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', skill) or len(skill) > 64:
                raise ValueError(f'invalid skill name: {skill}')
            result['.agents/skills/' + skill] = (f'../../skills/{skill}'.encode(), 0o120000)
    for name, (data, mode) in result.items():
        if mode == 0o120000:
            target = posixpath.normpath(posixpath.join(posixpath.dirname(name), data.decode()))
            if target not in result and not any(k.startswith(target + '/') for k in result):
                raise ValueError(f'broken generated symlink: {name}')
    return result


def synchronize(root, source=None, check=False):
    root = guard_root(root)
    with lock(root), tempfile.TemporaryDirectory(prefix='grimoire-readonly-') as temp:
        old = check_ownership(root)
        if source is None:
            source = Path(temp) / 'upstream'
            run('git', '-c', 'core.hooksPath=/dev/null', 'clone', '--depth=1', '--no-checkout', UPSTREAM, str(source))
        source = Path(source).resolve()
        if source == root or root in source.parents or source in root.parents:
            raise ValueError('source and downstream must be separate, non-nested repositories')
        sha, upstream = snapshot(source)
        files = build(root, upstream)
        state = {'schema_version': 1, 'upstream_url': UPSTREAM, 'upstream_sha': sha, 'managed': manifest(files)}
        previous = old.get('managed', {})
        changes = [name for name in sorted(set(previous) | set(state['managed'])) if previous.get(name) != state['managed'].get(name)]
        summary = {'upstream_sha': sha, 'previous_sha': old.get('upstream_sha'), 'changed_files': changes,
                   'deleted_files': sorted(set(previous) - set(state['managed']))}
        if check:
            if changes or old != state:
                raise ValueError('generated content or upstream snapshot differs; synchronize first')
            return summary
        # All conflicts were checked before any managed write. Do not follow links when writing.
        for name in sorted(set(previous) - set(files), reverse=True):
            p = root / safe_path(name)
            p.unlink()
        if set(previous) - set(files):
            for prefix in MANAGED:
                base = root / prefix
                if base.exists():
                    for p in sorted(base.rglob('*'), key=lambda p: len(p.parts), reverse=True):
                        if p.is_dir() and not p.is_symlink():
                            try:
                                p.rmdir()
                            except OSError:
                                pass  # Only empty directories in managed trees are removed.
        for name, (data, mode) in sorted(files.items()):
            if previous.get(name) == state['managed'][name]:
                continue
            p = root / safe_path(name)
            for parent in p.parents:
                if parent == root:
                    break
                if parent.is_symlink():
                    raise ValueError(f'REFUSED: parent symlink {parent}')
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.is_symlink():
                p.unlink()
            if mode == 0o120000:
                p.symlink_to(data.decode())
            else:
                p.write_bytes(data)
                p.chmod(mode)
        state_text = json.dumps(state, indent=2, sort_keys=True) + '\n'
        if old != state:
            (root / 'sync-state.json').write_text(state_text)
        return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, help='read tracked HEAD of a separate local clone, never its working tree')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--summary', type=Path, help='write JSON summary outside the managed trees')
    args = parser.parse_args()
    try:
        summary = synchronize(ROOT, args.source, args.check)
        if args.summary:
            summary_path = args.summary.resolve()
            if not summary_path.is_relative_to(ROOT) or any(summary_path.is_relative_to(ROOT / p) for p in MANAGED):
                raise ValueError('summary must be a downstream-owned path inside this repository')
            args.summary.write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary, indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'SYNC FAILED: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
