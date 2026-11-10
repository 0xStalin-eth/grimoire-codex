#!/usr/bin/env python3
"""Record independent audit runs and compare only completed, manually adjudicated results."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

SCHEMA = 1
SEVERITIES = {'critical', 'high', 'medium', 'low', 'informational', 'unknown'}


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def git(target, *args):
    return subprocess.check_output(['git', '-C', str(target), *args], env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'), stderr=subprocess.PIPE).decode().strip()


def safe_output(path):
    path = Path(path).expanduser().resolve()
    for parent in [path, *path.parents]:
        if (parent / '.claude-plugin/plugin.json').exists():
            raise ValueError('REFUSED: benchmark output would modify a Claude toolkit checkout')
        if (parent / '.git').exists():
            remotes = git(parent, 'remote', '-v')
            if re.search(r'github\.com[:/]0xStalin-eth/grimoire(?:\.git)?\s', remotes, re.I):
                raise ValueError('REFUSED: benchmark output would modify canonical upstream')
            break
    return path


def require_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} must be non-empty text')


def sha(value, field):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{40}', value):
        raise ValueError(f'{field} must be an exact 40-character Git commit SHA')


def numeric(value, field, optional=False):
    if value is None and optional:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f'{field} must be a finite nonnegative number')


def findings_valid(data):
    if not isinstance(data, dict) or data.get('schema_version') != SCHEMA or not isinstance(data.get('findings'), list):
        raise ValueError('expected schema_version: 1 and findings array')
    ids = set()
    for finding in data['findings']:
        for key in ['id', 'title', 'root_cause', 'impact']:
            require_text(finding.get(key), key)
        if finding['id'] in ids:
            raise ValueError('duplicate finding ID')
        ids.add(finding['id'])
        if finding.get('severity') not in SEVERITIES:
            raise ValueError('invalid severity')
        if not isinstance(finding.get('evidence'), list) or not finding['evidence']:
            raise ValueError('evidence must contain source/proof references')
        for item in finding['evidence']:
            require_text(item, 'evidence')
        locations = finding.get('locations')
        if not isinstance(locations, list) or not locations:
            raise ValueError('locations must be nonempty')
        for location in locations:
            require_text(location.get('path'), 'location.path')
            if Path(location['path']).is_absolute() or '..' in Path(location['path']).parts:
                raise ValueError('finding locations must be target-relative paths')
            if type(location.get('line')) is not int or location['line'] < 1:
                raise ValueError('location.line must be a positive integer')
        reproduction = finding.get('reproduction')
        if not isinstance(reproduction, dict) or reproduction.get('status') not in {'reproduced', 'not_reproduced', 'not_tested'}:
            raise ValueError('reproduction status required')
        for key in ['command', 'result']:
            require_text(reproduction.get(key), 'reproduction.' + key)
    return ids


def initialize(args):
    output = safe_output(args.output)
    if output.exists():
        raise ValueError('run output already exists; choose a fresh directory')
    commit = git(args.target, 'rev-parse', 'HEAD')
    sha(commit, 'target commit')
    if git(args.target, 'status', '--porcelain', '--untracked-files=all'):
        raise ValueError('target checkout must be clean before starting a comparable run')
    sha(args.skill_version, 'skill version')
    sha(args.upstream_sha, 'upstream SHA')
    instructions, scope = Path(args.instructions).read_bytes(), Path(args.scope).read_bytes()
    environment = load(args.environment)
    if not isinstance(environment, dict) or not environment:
        raise ValueError('environment must be a nonempty JSON object with tool versions and runtime configuration')
    for field in ['model', 'runtime', 'runtime_version', 'workflow']:
        require_text(getattr(args, field), field)
    run = {'schema_version': SCHEMA, 'run_id': str(uuid.uuid4()), 'status': 'pending', 'agent': args.agent,
           'workflow': args.workflow, 'target_commit': commit, 'skill_version': args.skill_version,
           'upstream_sha': args.upstream_sha, 'model': args.model, 'runtime': args.runtime,
           'runtime_version': args.runtime_version, 'environment': environment,
           'instructions_sha256': hash_bytes(instructions), 'scope_sha256': hash_bytes(scope),
           'created_at': datetime.now(timezone.utc).isoformat(), 'metrics': None}
    output.mkdir(parents=True)
    (output / 'instructions.txt').write_bytes(instructions)
    (output / 'scope.txt').write_bytes(scope)
    save(output / 'run.json', run)
    print(f'Prepared independent {args.agent} run: {output}')


def complete(args):
    run_dir = safe_output(args.run)
    if any(p.is_symlink() for p in run_dir.rglob('*')):
        raise ValueError('run metadata/output symlinks are not accepted')
    run = load(run_dir / 'run.json')
    if run.get('status') != 'pending':
        raise ValueError('only a pending run can be completed; completed runs are immutable')
    normalized = load(args.findings)
    findings_valid(normalized)
    numeric(args.elapsed_seconds, 'elapsed seconds')
    for key in ['input_tokens', 'output_tokens', 'estimated_cost_usd']:
        numeric(getattr(args, key), key, optional=True)
    raw_input = Path(args.raw)
    raw = raw_input.resolve()
    if not raw.exists() or raw_input.is_symlink() or raw == run_dir or run_dir in raw.parents or raw in run_dir.parents:
        raise ValueError('raw outputs must be a separate existing file or directory')
    if (run_dir / 'raw').exists():
        raise ValueError('raw output already exists; inspect incomplete capture manually')
    paths = sorted(raw.rglob('*')) if raw.is_dir() else [raw]
    if any(p.is_symlink() for p in paths):
        raise ValueError('raw output symlinks are not accepted')
    files = [p for p in paths if p.is_file()]
    if not files:
        raise ValueError('raw output must not be empty')
    # Copy only explicitly selected reports/logs, never a target checkout automatically.
    raw_data = {(p.relative_to(raw).as_posix() if raw.is_dir() else p.name): p.read_bytes() for p in files}
    (run_dir / 'raw').mkdir()
    for name, data in raw_data.items():
        target = run_dir / 'raw' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    save(run_dir / 'results.json', normalized)
    captured = {f'raw/{name}': hash_bytes(data) for name, data in raw_data.items()}
    captured['results.json'] = hash_bytes((run_dir / 'results.json').read_bytes())
    run.update(status='completed', completed_at=datetime.now(timezone.utc).isoformat(), artifacts=captured,
               metrics={'elapsed_seconds': args.elapsed_seconds, 'input_tokens': args.input_tokens,
                        'output_tokens': args.output_tokens, 'estimated_cost_usd': args.estimated_cost_usd})
    save(run_dir / 'run.json', run)
    save(run_dir / 'seal.json', {'run_sha256': hash_bytes((run_dir / 'run.json').read_bytes())})
    print(f'Completed run: {run_dir}. Raw reports preserved; no agent was launched or findings published.')


def read_completed(path):
    path = Path(path).resolve()
    run = load(path / 'run.json')
    if load(path / 'seal.json').get('run_sha256') != hash_bytes((path / 'run.json').read_bytes()):
        raise ValueError('run metadata changed after completion')
    if run.get('schema_version') != SCHEMA or run.get('status') != 'completed':
        raise ValueError('comparison requires two completed runs')
    for field in ['target_commit', 'skill_version', 'upstream_sha']:
        sha(run.get(field), field)
    for field in ['run_id', 'model', 'runtime', 'runtime_version', 'workflow']:
        require_text(run.get(field), field)
    if run.get('agent') not in {'claude', 'codex'} or not isinstance(run.get('environment'), dict):
        raise ValueError('invalid run metadata')
    for name in ['instructions', 'scope']:
        if (path / f'{name}.txt').is_symlink():
            raise ValueError('run inputs must not be symlinks')
        if hash_bytes((path / f'{name}.txt').read_bytes()) != run.get(f'{name}_sha256'):
            raise ValueError(f'{name} changed since initialization')
    artifacts = run.get('artifacts', {})
    if 'results.json' not in artifacts or not any(n.startswith('raw/') for n in artifacts):
        raise ValueError('missing raw/normalized output integrity manifest')
    for name, expected_hash in artifacts.items():
        p = path / name
        if Path(name).is_absolute() or '..' in Path(name).parts or p.is_symlink() or not p.resolve().is_relative_to(path):
            raise ValueError('unsafe artifact path')
        if hash_bytes(p.read_bytes()) != expected_hash:
            raise ValueError(f'artifact changed after completion: {name}')
    actual_raw = {p.relative_to(path).as_posix() for p in (path / 'raw').rglob('*') if p.is_file()}
    if actual_raw != {n for n in artifacts if n.startswith('raw/')}:
        raise ValueError('raw outputs changed after completion')
    metrics = run.get('metrics') or {}
    numeric(metrics.get('elapsed_seconds'), 'elapsed seconds')
    for key in ['input_tokens', 'output_tokens', 'estimated_cost_usd']:
        numeric(metrics.get(key), key, optional=True)
    results = load(path / 'results.json')
    findings_valid(results)
    return run, {f['id']: f for f in results['findings']}


def compare(left, right, review):
    a, af = read_completed(left)
    b, bf = read_completed(right)
    if a['run_id'] == b['run_id'] or a['agent'] == b['agent']:
        raise ValueError('require distinct Claude and Codex runs')
    for key in ['target_commit', 'scope_sha256', 'instructions_sha256', 'workflow', 'upstream_sha']:
        if a[key] != b[key]:
            raise ValueError(f'non-equivalent benchmark inputs: {key}')
    review = load(review)
    if not isinstance(review, dict):
        raise ValueError('adjudication must be a JSON object')
    if review.get('schema_version') != SCHEMA or review.get('left_run_id') != a['run_id'] or review.get('right_run_id') != b['run_id']:
        raise ValueError('adjudication must identify these exact left/right runs')
    require_text(review.get('reviewer'), 'reviewer')
    require_text(review.get('review_notes'), 'review_notes')
    judgments = review.get('adjudications', {})
    if not isinstance(judgments, dict) or not isinstance(review.get('matches', []), list):
        raise ValueError('invalid adjudication or matches structure')
    ground_truth = review.get('ground_truth')
    truth = {}
    if ground_truth is not None:
        if not isinstance(ground_truth, dict) or ground_truth.get('reliable') is not True or not isinstance(ground_truth.get('items'), list):
            raise ValueError('ground truth must be explicitly reliable and evidence-backed')
        for item in ground_truth['items']:
            require_text(item.get('id'), 'ground-truth id')
            require_text(item.get('evidence'), 'ground-truth evidence')
            if item['id'] in truth:
                raise ValueError('duplicate ground-truth id')
            truth[item['id']] = item
    metrics = {}
    valid = {}
    for side, findings in [('left', af), ('right', bf)]:
        decisions = judgments.get(side, {})
        if not isinstance(decisions, dict):
            raise ValueError('adjudications for each side must be an object keyed by finding ID')
        if set(decisions) != set(findings):
            raise ValueError(f'adjudicate every {side} finding, including uncertain reports')
        counts = {'valid': 0, 'false_positive': 0, 'uncertain': 0}
        valid[side] = set()
        found_truth = set()
        quality = {'reasoning': [], 'evidence': [], 'reproducibility': []}
        for fid, item in decisions.items():
            verdict = item.get('verdict')
            if verdict not in counts:
                raise ValueError('invalid adjudication verdict')
            require_text(item.get('evidence'), 'adjudication evidence')
            counts[verdict] += 1
            if verdict == 'valid':
                valid[side].add(fid)
            truth_ids = item.get('ground_truth_ids', [])
            if not isinstance(truth_ids, list) or set(truth_ids) - set(truth):
                raise ValueError('unknown ground-truth reference')
            if truth_ids and verdict != 'valid':
                raise ValueError('only valid findings can cover ground truth')
            found_truth.update(truth_ids)
            for key in quality:
                score = item.get('quality', {}).get(key)
                if score is not None:
                    if type(score) is not int or not 1 <= score <= 5:
                        raise ValueError('manual quality scores must be 1..5 or null')
                    quality[key].append(score)
        counts['missed_ground_truth_ids'] = sorted(set(truth) - found_truth) if ground_truth is not None else None
        counts['quality_mean'] = {k: sum(v)/len(v) if v else None for k, v in quality.items()}
        metrics[side] = counts
    pairs = []
    seen_left, seen_right = set(), set()
    for pair in review.get('matches', []):
        require_text(pair.get('evidence'), 'root-cause matching evidence')
        require_text(pair.get('root_cause'), 'matched root cause')
        l, r = pair.get('left'), pair.get('right')
        if l not in valid['left'] or r not in valid['right'] or l in seen_left or r in seen_right:
            raise ValueError('matches must be one-to-one, valid, evidence-backed findings')
        seen_left.add(l); seen_right.add(r)
        pairs.append({'left': l, 'right': r, 'root_cause': pair['root_cause'], 'evidence': pair['evidence'],
                      'left_severity': af[l]['severity'], 'right_severity': bf[r]['severity']})
    matching_complete = review.get('matching_complete') is True
    unmatched = {'left': sorted(valid['left'] - seen_left), 'right': sorted(valid['right'] - seen_right)}
    confounds = {k: {'left': a[k], 'right': b[k]} for k in ['skill_version', 'runtime', 'runtime_version', 'environment'] if a[k] != b[k]}
    return {'schema_version': SCHEMA, 'left': a, 'right': b, 'adjudication': review, 'metrics': metrics,
            'confirmed_overlap': pairs, 'matching_complete': matching_complete,
            'unique_valid' if matching_complete else 'unmatched_valid_candidates': unmatched,
            'confounds': confounds,
            'interpretation': 'Observed workflow comparison; model effects are not isolated from adaptation, tools or runtime. '
                              'Matches and verdicts are human adjudications, not textual similarity. '
                              'False negatives are measured only against supplied reliable ground truth.'}


def markdown(report):
    a, b = report['left'], report['right']
    out = ['# Independent audit comparison', '', f"Left: {a['agent']} / {a['model']}; right: {b['agent']} / {b['model']}.",
           f"Target commit: `{a['target_commit']}`. Upstream: `{a['upstream_sha']}`.", '',
           '| Metric | Left | Right |', '|---|---:|---:|']
    for key in ['valid', 'false_positive', 'uncertain', 'missed_ground_truth_ids']:
        out.append(f"| {key} | {report['metrics']['left'][key]} | {report['metrics']['right'][key]} |")
    for key in ['elapsed_seconds', 'input_tokens', 'output_tokens', 'estimated_cost_usd']:
        out.append(f"| {key} | {a['metrics'][key]} | {b['metrics'][key]} |")
    out += ['', f"Evidence-confirmed overlapping pairs: {len(report['confirmed_overlap'])}.",
            'Unique valid findings: ' + json.dumps(report['unique_valid']) if report['matching_complete'] else
            'Overlap review is incomplete; unmatched findings are candidates, not proven unique.', '',
            'Confounding variables: ' + ', '.join(report['confounds'] or ['none recorded; unmeasured differences may remain']), '',
            report['interpretation'], '', 'See comparison.json for raw provenance, severity disagreements, quality scores and evidence.']
    return '\n'.join(out) + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init')
    for field in ['output', 'target', 'instructions', 'scope', 'environment', 'skill-version', 'upstream-sha', 'model', 'runtime', 'runtime-version', 'workflow']:
        init.add_argument('--' + field, required=True)
    init.add_argument('--agent', choices=['claude', 'codex'], required=True)
    done = sub.add_parser('complete')
    for field in ['run', 'findings', 'raw']:
        done.add_argument('--' + field, required=True)
    done.add_argument('--elapsed-seconds', required=True, type=float)
    for field in ['input-tokens', 'output-tokens']:
        done.add_argument('--' + field, type=int)
    done.add_argument('--estimated-cost-usd', type=float)
    comp = sub.add_parser('compare')
    comp.add_argument('left'); comp.add_argument('right')
    comp.add_argument('--review', required=True)
    comp.add_argument('--output', required=True)
    args = p.parse_args()
    try:
        if args.command == 'init':
            initialize(args)
        elif args.command == 'complete':
            complete(args)
        else:
            report = compare(args.left, args.right, args.review)
            output = safe_output(args.output)
            if output.exists():
                raise ValueError('comparison output must be a fresh directory')
            output.mkdir(parents=True)
            save(output / 'comparison.json', report)
            (output / 'comparison.md').write_text(markdown(report))
            print(markdown(report))
    except (ValueError, KeyError, TypeError, AttributeError, OSError, subprocess.CalledProcessError) as exc:
        print(f'BENCHMARK FAILED: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
