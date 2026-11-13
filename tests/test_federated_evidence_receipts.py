"""Independent reconstruction of the published, split measured snapshots."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]


class Evidence(unittest.TestCase):
    def test_measured_snapshots_have_exact_source_and_complete_parts(self):
        source = hashlib.sha256((ROOT / 'bin/federated_node_snapshot.py').read_bytes()).hexdigest()
        manifests = sorted((ROOT / 'benchmarks/receipts').glob('20261113-federated-node-*.json'))
        manifests = [p for p in manifests if '-models-' not in p.name]
        self.assertEqual(len(manifests), 3)
        counts = []
        for path in manifests:
            doc = json.loads(path.read_bytes())
            snapshot = doc['header']
            self.assertEqual(snapshot['collector_sha256'], source)
            models = []
            for part in doc['parts']:
                self.assertEqual(Path(part['file']).name, part['file'])
                raw = (path.parent / part['file']).read_bytes()
                self.assertLess(len(raw), 16384)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), part['sha256'])
                entries = json.loads(raw)
                self.assertEqual(len(entries), part['count'])
                models.extend(entries)
            self.assertEqual(len(models), doc['model_count'])
            counts.append(len(models))
            snapshot['models'] = models
            canonical = json.dumps(snapshot, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
            self.assertEqual(hashlib.sha256(canonical).hexdigest(), doc['snapshot_ref'])
            self.assertEqual(snapshot['admission']['state'], 'NO_DATA')
            self.assertEqual(snapshot['training'], 'NOT_AUTHORIZED')
            for model in models:
                self.assertRegex(model['model_version'], '^[a-f0-9]{64}$')
                self.assertNotIn('name', model)
                self.assertEqual(model['task_quality']['state'], 'NO_DATA')
        self.assertEqual(sorted(counts), [2, 17, 29])


if __name__ == '__main__':
    unittest.main()
