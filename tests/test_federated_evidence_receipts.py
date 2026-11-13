"""Independent reconstruction of the published, split measured snapshots."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
# Frozen measurements were verified against their then-current collector in
# CI43401694565/43402154518. Keep their exact seals; no new census is needed for
# the two-line anonymous-node expansion. Source bytes remain at immutable
# commit3d9f7cb9677147a7c0e4f0d9c3fa260cf34b64ad, blob7e4ad71bcd86436977d6aa89300e92b41e3ff592.
FROZEN_SOURCE = '97b0014a91647210217ea0218ee3e4adfdb00c5793e5dc9a2224608690dda5d5'
FROZEN_SEALS = {
    '9a1adac53532e6a558c53498de72d67b52656044cd7ff9358e73d0d5af1f3d4e',
    '073f6cd0e4f188a94aae87fe867d7510460ca775ad68d1897ca27f6c1866d422',
    '64613d5a810da8fd89084866308f934064a420c1f4f24e18a6aa7cc03a4c3dd4',
}


class Evidence(unittest.TestCase):
    def test_same_alias_on_two_nodes_does_not_mean_same_model(self):
        folder = ROOT / 'benchmarks/receipts'
        def models(name):
            doc = json.loads((folder / ('20261113-federated-' + name + '.json')).read_bytes())
            return [m for part in doc['parts'] for m in json.loads((folder / part['file']).read_bytes())]
        primary, edge = models('node-c-primary'), models('node-d')
        large = next(m for m in primary if m['model_version'].startswith('b0593ac3ce75'))
        small = next(m for m in edge if m['model_version'].startswith('7f16ae1d80ac'))
        self.assertEqual(large['model_ref'], small['model_ref'])
        self.assertNotEqual(large['model_version'], small['model_version'])
        self.assertNotEqual(large['catalog_bytes'], small['catalog_bytes'])

    def test_measured_snapshots_have_exact_source_and_complete_parts(self):
        source = hashlib.sha256((ROOT / 'bin/federated_node_snapshot.py').read_bytes()).hexdigest()
        manifests = sorted((ROOT / 'benchmarks/receipts').glob('20261113-federated-node-*.json'))
        manifests = [p for p in manifests if '-models-' not in p.name]
        self.assertEqual(len(manifests), 5)
        counts = []
        for path in manifests:
            doc = json.loads(path.read_bytes())
            snapshot = doc['header']
            expected_source = FROZEN_SOURCE if doc['snapshot_ref'] in FROZEN_SEALS else source
            self.assertEqual(snapshot['collector_sha256'], expected_source)
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
        self.assertEqual(sorted(counts), [1, 2, 6, 17, 29])


if __name__ == '__main__':
    unittest.main()
