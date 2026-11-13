"""Integrity and scope of immutable measurements, not capability certification."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

from meta_harness.reuse import instrument

ROOT=Path(__file__).parents[1]


class ResourceEvidence(unittest.TestCase):
    def test_experiment_seal_source_and_two_failed_quality_attempts(self):
        path=ROOT/'benchmarks/receipts/20261113-node-d-public-resource-r1.json'
        self.assertLess(path.stat().st_size,16384)
        record=json.loads(path.read_bytes());ref=record.pop('experiment_ref')
        self.assertEqual(ref,hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':')).encode()).hexdigest())
        source=record['throughput']['source']
        for key,path in [('probe_sha256','bin/jetson_public_probe.py'),
                         ('runner_sha256','benchmarks/station-96-first-pass-20261029/smoke.py')]:
            self.assertEqual(source[key],hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
        code=(ROOT/'meta_harness/transports.py').read_text()
        node=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name=='grade_public')
        self.assertEqual(source['grader_sha256'],hashlib.sha256(ast.get_source_segment(code,node).encode()).hexdigest())
        self.assertEqual(record['model_calls'],2)
        self.assertEqual(record['quality']['grades'],['OUTPUT_SCHEMA','OUTPUT_SCHEMA'])
        self.assertEqual(record['quality']['distinct_cases'],1)
        self.assertEqual(record['GPU_attribution']['state'],'NO_DATA')
        self.assertEqual(record['TTFT']['state'],'NO_DATA')
        self.assertFalse(record['settings_changed'])

    def test_post_measurement_snapshot_preserves_identity_and_missing_pressure(self):
        path=ROOT/'benchmarks/receipts/20261113-node-d-postmeasure-r2.json'
        record=json.loads(path.read_bytes());ref=record.pop('snapshot_ref')
        self.assertEqual(instrument('resources').sha(record),ref)
        self.assertEqual(record['node'],'node-d')
        self.assertEqual(record['resident_count'],0)
        for axis in ('cpu','memory','io'):
            self.assertEqual(record['host']['pressure_avg10'][axis]['state'],'NO_DATA')
        self.assertEqual(record['training'],'NOT_AUTHORIZED')
