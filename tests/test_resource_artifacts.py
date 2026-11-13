import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'bin'))
import resource_decision as r
import resource_decision_probe as p
import resource_contract_probe as bridge


class Artifacts(unittest.TestCase):
    def load(self, filename):
        raw = (ROOT / 'benchmarks/receipts' / filename).read_bytes()
        self.assertLess(len(raw), 16384)
        return json.loads(raw)

    def test_compatibility_record_matches_exact_readonly_source(self):
        record = self.load('20261113-node-d-compatibility-r1.json')
        ref = record.pop('compatibility_ref')
        self.assertEqual(ref, r.sha(record))
        self.assertEqual(record['collector_sha256'], hashlib.sha256((ROOT / 'bin/nvidia_readonly_compat.py').read_bytes()).hexdigest())
        self.assertEqual(record['node'], 'node-d')
        self.assertEqual(record['kind'], 'compatibility-observation')
        self.assertFalse(record['settings_changed'])
        self.assertEqual(record['gpu_execution']['state'], 'NO_DATA')
        self.assertEqual(record['model_catalog']['cause'], 'not_recensused')

    def test_control_report_reproduces_without_node_measurements(self):
        record = self.load('20261113-resource-decision-controls.json')
        self.assertEqual(record, p.report())
        self.assertEqual(record['model_calls'], 0)
        self.assertIn('SYNTHETIC', record['evidence_basis'])

    def test_real_catalog_replay_is_reproducible_and_cannot_execute(self):
        historical = ROOT / 'benchmarks/receipts/20261113-resource-contract-replay.json'
        self.assertEqual(hashlib.sha256(historical.read_bytes()).hexdigest(),
                         '62bce6dce90537db776abac72fc3b7b02c7e7c5e3c33281eb5d70e7d4810a6b9')
        historical2 = ROOT / 'benchmarks/receipts/20261113-resource-contract-replay-r2.json'
        self.assertEqual(hashlib.sha256(historical2.read_bytes()).hexdigest(),
                         'c660d8b041654efd3593acb5d0ed2b12be2b4244932a030ad1f0885cc82993d0')
        historical3 = ROOT / 'benchmarks/receipts/20261113-resource-contract-replay-r3.json'
        self.assertEqual(hashlib.sha256(historical3.read_bytes()).hexdigest(),
                         '7041ff4c883c379c97ea4674e9b7742cbc5cccdffd2d767d40d7cbd2d74f25ae')
        historical4 = ROOT / 'benchmarks/receipts/20261113-resource-contract-replay-r4.json'
        self.assertEqual(hashlib.sha256(historical4.read_bytes()).hexdigest(),
                         '72ecc13092e41b91e851f680249208e2a0065804a960ab62b2f90d6525140925')
        record = self.load('20261113-resource-contract-replay-r5.json')
        self.assertEqual(record, bridge.report())
        self.assertEqual(record['model_calls'], 0)
        for key in ('no_profile', 'tampered', 'expired', 'malicious'):
            self.assertEqual(record[key]['state'], 'ABSTAIN')
            self.assertFalse(record[key]['dispatch_authorized'])

    def test_real_contract_bridge_retains_synthetic_and_unmerged_scope(self):
        record = self.load('20261113-resource-contract-bridge.json')
        ref = record.pop('bridge_ref')
        self.assertEqual(ref, r.sha(record))
        self.assertIn('SYNTHETIC', record['basis'])
        self.assertEqual(record['resource_decision_sha256'], hashlib.sha256((ROOT / 'bin/resource_decision.py').read_bytes()).hexdigest())
        self.assertEqual(record['positive']['state'], 'SIMULATED_ELIGIBLE')
        self.assertFalse(record['positive']['dispatch_authorized'])
        self.assertEqual(record['malicious_override']['state'], 'ABSTAIN')
        preview = self.load('20261113-cerebro-reconciliation-preview.json')
        self.assertEqual(record['preview_tree'], preview['preview_tree'])
        self.assertFalse(preview['main_merged'])
        self.assertFalse(preview['published_177_changed'])


if __name__ == '__main__':
    unittest.main()
