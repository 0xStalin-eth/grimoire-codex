#!/usr/bin/env python3
"""Exercise the collection/comparison CLI with SYNTHETIC outputs; does not run either model."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'scripts/benchmark.py'


def run(*args, **kwargs):
    subprocess.run(list(map(str, args)), check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / 'scripts'))
    from benchmark import safe_output
    output = safe_output(args.output)
    if output.exists():
        raise ValueError('choose a fresh demo output directory')
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='grimoire-synthetic-') as temp:
        temp = Path(temp)
        target = temp / 'target'
        target.mkdir()
        run('git', 'init', '-q', target)
        (target / 'README.md').write_text('Synthetic metadata fixture. No actual vulnerability or model run.\n')
        run('git', '-C', target, 'add', 'README.md')
        run('git', '-C', target, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'synthetic fixture',
            env=dict(os.environ, GIT_AUTHOR_DATE='2000-01-01T00:00:00Z', GIT_COMMITTER_DATE='2000-01-01T00:00:00Z'))
        (temp / 'instructions.txt').write_text('Synthetic comparison demonstration only.\n')
        (temp / 'scope.txt').write_text('README.md\n')
        (temp / 'env.json').write_text('{"fixture": "synthetic; no model or security test executed"}\n')
        upstream = json.loads((ROOT / 'sync-state.json').read_text())['upstream_sha']
        for agent in ['claude', 'codex']:
            run(sys.executable, CLI, 'init', '--output', output/agent, '--target', target,
                '--instructions', temp/'instructions.txt', '--scope', temp/'scope.txt', '--environment', temp/'env.json',
                '--skill-version', upstream, '--upstream-sha', upstream, '--agent', agent,
                '--model', 'synthetic-no-model', '--runtime', 'fixture', '--runtime-version', '1', '--workflow', 'synthetic-demo')
            raw = temp/'report.txt'
            raw.write_text('SYNTHETIC report: illustrative callback ordering, not a real finding.\n')
            run(sys.executable, CLI, 'complete', '--run', output/agent, '--findings', ROOT/'benchmark/examples/findings.json',
                '--raw', raw, '--elapsed-seconds', '0', '--input-tokens', '0', '--output-tokens', '0', '--estimated-cost-usd', '0')
        review = json.loads((ROOT/'benchmark/examples/review.json').read_text())
        review['left_run_id'] = json.loads((output/'claude/run.json').read_text())['run_id']
        review['right_run_id'] = json.loads((output/'codex/run.json').read_text())['run_id']
        review['reviewer'] = 'synthetic demo fixture'
        review['review_notes'] = 'Synthetic demonstration, not a model evaluation or vulnerability validation.'
        (output/'review.json').write_text(json.dumps(review, indent=2)+'\n')
        run(sys.executable, CLI, 'compare', output/'claude', output/'codex', '--review', output/'review.json', '--output', output/'comparison')


if __name__ == '__main__':
    main()
