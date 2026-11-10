import argparse
import copy
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import benchmark as bench


FINDING = {
    'id': 'F-1', 'title': 'Fixture loses funds after external call', 'severity': 'high',
    'root_cause': 'Balance updated after untrusted callback', 'impact': 'Repeat withdrawal in a local fixture',
    'locations': [{'path': 'src/Fixture.sol', 'line': 12}],
    'evidence': ['raw/report.txt: local proof and callback trace'],
    'reproduction': {'status': 'reproduced', 'command': 'fixture-test', 'result': 'repeat withdrawal observed'},
}


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.temp = tempfile.TemporaryDirectory(prefix='grimoire-benchmark-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        target = self.root / 'target'
        target.mkdir()
        subprocess.run(['git', 'init', '-q', str(target)], check=True)
        (target / 'fixture.txt').write_text('synthetic target\n')
        subprocess.run(['git', '-C', str(target), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(target), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'], check=True)
        for name, text in [('instructions.txt', 'Inspect the synthetic target.'), ('scope.txt', 'fixture.txt'), ('env.json', '{"tools":{"fixture-test":"1"},"sandbox":"local"}')]:
            (self.root / name).write_text(text)
        self.runs = []
        for side, agent in [('left', 'claude'), ('right', 'codex')]:
            run = self.root / side
            bench.initialize(argparse.Namespace(output=run, target=target, instructions=self.root/'instructions.txt',
                scope=self.root/'scope.txt', environment=self.root/'env.json', skill_version=('a' if side=='left' else 'b')*40,
                upstream_sha='c'*40, model=agent+'-fixture-model', runtime=agent, runtime_version='fixture-1', workflow='peer-review', agent=agent))
            raw = self.root / (side+'-raw.txt')
            raw.write_text('synthetic raw report: same balance callback root cause\n')
            normalized = self.root / (side+'-findings.json')
            finding = copy.deepcopy(FINDING)
            if side == 'right': finding['severity'] = 'medium'
            normalized.write_text(json.dumps({'schema_version': 1, 'findings': [finding]}))
            bench.complete(argparse.Namespace(run=run, findings=normalized, raw=raw, elapsed_seconds=1.5,
                input_tokens=None, output_tokens=None, estimated_cost_usd=None))
            self.runs.append(run)
        self.review = self.root / 'review.json'
        self.ledger = {'schema_version': 1, 'left_run_id': bench.load(self.runs[0]/'run.json')['run_id'],
            'right_run_id': bench.load(self.runs[1]/'run.json')['run_id'], 'reviewer': 'fixture adjudicator',
            'review_notes': 'Synthetic fixture: inspected callback traces.', 'matching_complete': False,
            'adjudications': {side: {'F-1': {'verdict':'valid', 'evidence':'local callback trace confirms repeated withdrawal',
                'ground_truth_ids': [], 'quality': {'reasoning':4, 'evidence':4, 'reproducibility':5}}} for side in ['left', 'right']},
            'matches': []}
        self.write_review()

    def write_review(self):
        bench.save(self.review, self.ledger)

    def compare(self):
        return bench.compare(*self.runs, self.review)

    def test_complete_cli_pipeline_keeps_raw_outputs(self):
        self.assertEqual('synthetic raw report: same balance callback root cause\n', (self.runs[0]/'raw/left-raw.txt').read_text())
        report = self.compare()
        self.assertEqual(1, report['metrics']['left']['valid'])
        self.assertIn('unmatched_valid_candidates', report)
        self.assertEqual([], report['confirmed_overlap'])
        self.assertIsNone(report['metrics']['left']['missed_ground_truth_ids'])
        self.assertIn('skill_version', report['confounds'])
        self.assertIn('not proven unique', bench.markdown(report))

    def test_manual_evidence_matching_and_severity_disagreement(self):
        self.ledger['matches'] = [{'left':'F-1','right':'F-1','root_cause':'same callback balance ordering', 'evidence':'both traces execute Fixture.withdraw before balance update'}]
        self.ledger['matching_complete'] = True
        self.write_review()
        report = self.compare()
        self.assertEqual(1, len(report['confirmed_overlap']))
        self.assertEqual('high', report['confirmed_overlap'][0]['left_severity'])
        self.assertEqual('medium', report['confirmed_overlap'][0]['right_severity'])
        self.assertEqual({'left': [], 'right': []}, report['unique_valid'])

    def test_cannot_compare_unfinished_runs(self):
        run = bench.load(self.runs[0]/'run.json'); run['status']='pending'
        bench.save(self.runs[0]/'run.json', run)
        bench.save(self.runs[0]/'seal.json', {'run_sha256':bench.hash_bytes((self.runs[0]/'run.json').read_bytes())})
        with self.assertRaisesRegex(ValueError, 'completed runs'):
            self.compare()

    def test_modified_raw_report_is_rejected(self):
        (self.runs[0]/'raw/left-raw.txt').write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'changed after completion'):
            self.compare()

    def test_modified_metadata_is_rejected(self):
        run = bench.load(self.runs[0]/'run.json');run['model']='changed'
        bench.save(self.runs[0]/'run.json',run)
        with self.assertRaisesRegex(ValueError, 'metadata changed'):
            self.compare()

    def test_different_scope_rejected(self):
        (self.runs[0]/'scope.txt').write_text('different')
        with self.assertRaisesRegex(ValueError, 'scope changed'):
            self.compare()

    def test_match_without_evidence_is_rejected(self):
        self.ledger['matches']=[{'left':'F-1','right':'F-1','root_cause':'same','evidence':''}]
        self.write_review()
        with self.assertRaisesRegex(ValueError, 'matching evidence'):
            self.compare()

    def test_duplicate_matches_rejected(self):
        pair={'left':'F-1','right':'F-1','root_cause':'same','evidence':'verified identical trace'}
        self.ledger['matches']=[pair,pair];self.write_review()
        with self.assertRaisesRegex(ValueError, 'one-to-one'):
            self.compare()

    def test_ground_truth_misses_only_when_reliably_supplied(self):
        self.ledger['ground_truth']={'reliable':True,'items':[{'id':'GT-1','evidence':'fixture oracle and expected exploit'}, {'id':'GT-2','evidence':'second fixture oracle'}]}
        self.ledger['adjudications']['left']['F-1']['ground_truth_ids']=['GT-1']
        self.write_review()
        report=self.compare()
        self.assertEqual(['GT-2'],report['metrics']['left']['missed_ground_truth_ids'])
        self.assertEqual(['GT-1','GT-2'],report['metrics']['right']['missed_ground_truth_ids'])

    def test_invalid_finding_structure_and_negative_metrics_rejected(self):
        bad=copy.deepcopy(FINDING);bad['locations'][0]['line']=0
        with self.assertRaisesRegex(ValueError,'positive integer'):
            bench.findings_valid({'schema_version':1,'findings':[bad]})
        with self.assertRaises(ValueError): bench.numeric(-1,'elapsed')
        with self.assertRaises(ValueError): bench.numeric(float('nan'),'elapsed')
