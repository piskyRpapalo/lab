"""Offline adversarial consumption tests: no model/backend availability fixture."""
import copy
from datetime import timedelta
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
FOLDER = ROOT / 'benchmarks/receipts'
SPEC = importlib.util.spec_from_file_location('federated_projection', ROOT / 'bin/federated_projection.py')
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)
PINS = {
    'node-b': '9a1adac53532e6a558c53498de72d67b52656044cd7ff9358e73d0d5af1f3d4e',
    'node-c-primary': '073f6cd0e4f188a94aae87fe867d7510460ca775ad68d1897ca27f6c1866d422',
    'node-c-secondary': '64613d5a810da8fd89084866308f934064a420c1f4f24e18a6aa7cc03a4c3dd4',
    'node-d': 'a16605fd146a8b9e1241aa874e0c3de5a79027e6ba00ae30b266142275b47f29',
    'node-e': 'cf9d926a3eb70ac87e8ab33da7d18a942e8b365113912bbbe4e6e9b28635c199',
}


def name(node):
    return '20261113-federated-' + node + '.json'


def source(node='node-e'):
    return p.load_receipt(FOLDER, name(node), PINS[node])


def at(text='2026-11-13T09:42:00Z'):
    return p.instant(text)


class Projection(unittest.TestCase):
    def test_published_example_is_explicit_historical_replay_and_recomputes(self):
        example = json.loads((FOLDER / '20261113-federated-projection-example.json').read_bytes())
        self.assertEqual(example['mode'], 'HISTORICAL_REPLAY_NOT_LIVE')
        original, backend = source()
        self.assertTrue(p.verify_packet(example['packet'], original, at(example['at']), PINS['node-e'], backend))
        self.assertFalse(p.verify_packet(example['packet'], original, at('2026-11-13T10:00:00Z'), PINS['node-e'], backend))

    def test_all_retained_receipts_reconstruct_without_network(self):
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network forbidden')):
            for key, expected in PINS.items():
                original, backend = source(key)
                packet = p.views(p.project(original, at(), expected, backend))
                self.assertLess(len(p.encode(packet)), 16384)
                self.assertTrue(p.verify_packet(packet, original, at(), expected, backend))
                self.assertEqual(packet['record']['source_ref'], expected)
                self.assertFalse(packet['record']['admission']['allowed'])
                self.assertEqual(packet['record']['inference']['state'], 'NO_DATA')

    def test_metadata_is_observed_and_integrity_has_specific_verified_scope(self):
        original, backend = source()
        record = p.project(original, at(), PINS['node-e'], backend)
        self.assertEqual(record['schema'], original['schema'])
        self.assertEqual(record['state'], 'OBSERVED')
        self.assertEqual(record['verification'], {'state': 'VERIFIED', 'scope': 'receipt_integrity'})
        self.assertEqual(record['topology_state'], 'DECLARED')
        self.assertEqual(record['models']['capability_basis'], 'DECLARED')
        self.assertEqual(record['backend_version']['value'], '0.40.13')
        self.assertEqual(record['models']['count'], 1)
        self.assertEqual(record['memory']['available_bytes'], 3884351488)
        self.assertEqual(record['resources']['pressure']['state'], 'NO_DATA')
        self.assertIn('node_pressure', record['missing_measurements'])

    def test_expiry_retains_history_and_does_not_report_available_now(self):
        original, backend = source()
        before = copy.deepcopy(original)
        captured = at(original['observed_at'])
        current = p.project(original, captured + timedelta(seconds=120), PINS['node-e'], backend)
        expired = p.project(original, captured + timedelta(seconds=121), PINS['node-e'], backend)
        self.assertEqual(current['state'], 'OBSERVED')
        self.assertEqual(expired['state'], 'STALE')
        self.assertEqual(expired['memory']['state'], 'STALE')
        self.assertEqual(expired['models']['count'], 1)
        self.assertEqual(expired['observed_at'], current['observed_at'])
        self.assertEqual(expired['responds_now']['state'], 'NO_DATA')
        self.assertEqual(original, before)

    def test_future_clock_and_naive_time_refused(self):
        original, backend = source()
        with self.assertRaises(p.EvidenceError):
            p.project(original, at(original['observed_at']) - timedelta(seconds=1), PINS['node-e'], backend)
        with self.assertRaises(p.EvidenceError):
            p.project(original, at().replace(tzinfo=None), PINS['node-e'], backend)

    def test_original_pin_blocks_mutated_and_resealed_source(self):
        original, backend = source()
        original['host']['memory_bytes']['MemAvailable'] += 1
        original['snapshot_ref'] = p.snapshot.digest({k: v for k, v in original.items() if k != 'snapshot_ref'})
        with self.assertRaises(p.EvidenceError):
            p.project(original, at(), PINS['node-e'], backend)

    def test_jointly_resealed_record_and_views_fail_pinned_recomputation(self):
        original, backend = source()
        record = p.project(original, at(), PINS['node-e'], backend)
        record['models']['count'] = 50
        record.pop('projection_ref')
        packet = p.views(p.seal(record))
        self.assertFalse(p.verify_packet(packet, original, at(), PINS['node-e'], backend))
        self.assertFalse(p.verify_packet(packet, original, at() + timedelta(seconds=1), PINS['node-e'], backend))

    def test_no_packet_can_enable_admission_or_promote_inference(self):
        original, backend = source()
        for key, value in [('admission', {'allowed': True}), ('inference', {'state': 'VERIFIED'})]:
            record = p.project(original, at(), PINS['node-e'], backend)
            record[key] = value
            record.pop('projection_ref')
            with self.assertRaises(p.EvidenceError):
                p.views(p.seal(record))

    def test_four_readings_share_ref_summary_and_structured_state(self):
        original, backend = source()
        record = p.project(original, at(), PINS['node-e'], backend)
        packet = p.views(record)
        self.assertEqual(packet['views']['text'], packet['views']['speech'])
        for view in packet['views'].values():
            self.assertEqual(view['state_ref'], record['projection_ref'])
        self.assertEqual(packet['views']['machine']['record'], packet['record'])
        self.assertEqual(packet['views']['text']['summary'], record['summary'])

    def test_same_tag_and_separate_backends_are_not_collapsed(self):
        large, b = source('node-c-primary')
        small, d = source('node-d')
        left = p.project(large, at(), PINS['node-c-primary'], b)
        right = p.project(small, at(), PINS['node-d'], d)
        lm = next(m for m in left['models']['items'] if m['model_version'].startswith('b0593ac3'))
        sm = next(m for m in right['models']['items'] if m['model_version'].startswith('7f16ae1d'))
        self.assertEqual(lm['model_ref'], sm['model_ref'])
        self.assertNotEqual(lm['model_version'], sm['model_version'])
        secondary, backend = source('node-c-secondary')
        other = p.project(secondary, at(), PINS['node-c-secondary'], backend)
        self.assertEqual((left['models']['count'], other['models']['count']), (17, 2))
        self.assertNotEqual(left['backend'], other['backend'])

    def test_unknown_node_has_no_zero_or_invented_failure(self):
        record = p.missing('node-a', at())
        self.assertIsNone(record['models'])
        self.assertIsNone(record['source_ref'])
        self.assertEqual(record['state'], 'NO_DATA')
        self.assertNotIn('last_failure', record)
        with self.assertRaises(p.EvidenceError):
            p.missing('android-phone', at())

    def test_failed_catalog_preserves_host_facts_without_inventing_zero_models(self):
        original, backend = source()
        original['catalog_state'], original['models'] = 'NO_DATA', []
        original['snapshot_ref'] = p.snapshot.digest({k: v for k, v in original.items() if k != 'snapshot_ref'})
        record = p.project(original, at(), original['snapshot_ref'], backend)
        self.assertEqual(record['state'], 'NO_DATA')
        self.assertIsNone(record['models'])
        self.assertEqual(record['memory']['state'], 'OBSERVED')
        older = p.project(original, at() + timedelta(minutes=10), original['snapshot_ref'], backend)
        self.assertEqual(older['freshness']['state'], 'STALE')
        self.assertEqual(older['memory']['state'], 'STALE')

    def test_failed_backend_identity_is_still_distinct(self):
        primary = p.missing('node-c', at(), backend='primary')
        secondary = p.missing('node-c', at(), backend='secondary')
        self.assertNotEqual(primary['projection_ref'], secondary['projection_ref'])

    def test_prior_failure_is_a_host_cited_claim_not_a_new_probe(self):
        record = p.missing('node-a', at(), last_failure={'cause': 'access_timeout', 'source_ref': 'a'*64})
        self.assertEqual(record['last_failure']['state'], 'DECLARED')
        self.assertEqual(record['last_failure']['cause'], 'access_timeout')
        self.assertIsNone(record['observed_at'])
        with self.assertRaises(p.EvidenceError):
            p.missing('node-a', at(), last_failure={'cause': 'PRIVATE SECRET', 'source_ref': 'a'*64})

    def test_no_private_server_fields_are_projected(self):
        original, backend = source()
        original['private_path'] = '/private/CANARY'
        original['backend_version']['value'] = 'CANARY'
        original['models'][0]['capabilities']['value'].append('CANARY')
        ref = p.snapshot.digest({k: v for k, v in original.items() if k != 'snapshot_ref'})
        original['snapshot_ref'] = ref
        packet = p.views(p.project(original, at(), ref, backend))
        self.assertNotIn('CANARY', p.encode(packet).decode())

    def test_bad_model_identity_and_oversized_packet_refused(self):
        original, backend = source()
        for models in ([{'model_ref': 'private-model', 'model_version': 'a'*64}], original['models']*256):
            altered = copy.deepcopy(original)
            altered['models'] = models
            altered['snapshot_ref'] = p.snapshot.digest({k: v for k, v in altered.items() if k != 'snapshot_ref'})
            with self.assertRaises(p.EvidenceError):
                p.views(p.project(altered, at(), altered['snapshot_ref'], backend))


class FilesAndCLI(unittest.TestCase):
    def test_names_pins_and_duplicate_json_keys_are_bounded(self):
        for bad in ('../secret.json', '/private/file', '20261113-federated-node-phone.json'):
            with self.assertRaises(p.EvidenceError):
                p.load_receipt(FOLDER, bad, PINS['node-e'])
        with self.assertRaises(p.EvidenceError):
            p.load_receipt(FOLDER, name('node-e'), 'x'*64)
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, name('node-e')).write_text('{"schema":1,"schema":2}')
            with self.assertRaises(p.EvidenceError):
                p.load_receipt(folder, name('node-e'), PINS['node-e'])
            for numeric in ('NaN', 'Infinity', '1e999'):
                Path(folder, name('node-e')).write_text('{"value":' + numeric + '}')
                with self.assertRaises(p.EvidenceError):
                    p.load_receipt(folder, name('node-e'), PINS['node-e'])

    def test_mutated_part_symlink_and_cross_node_path_are_refused(self):
        doc = json.loads((FOLDER / name('node-e')).read_bytes())
        part = doc['parts'][0]['file']
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / name('node-e')).write_text(json.dumps(doc))
            (root / part).write_bytes((FOLDER / part).read_bytes() + b' ')
            with self.assertRaises(p.EvidenceError):
                p.load_receipt(root, name('node-e'), PINS['node-e'])
            (root / name('node-e')).unlink()
            (root / name('node-e')).symlink_to(FOLDER / name('node-e'))
            with self.assertRaises(p.EvidenceError):
                p.load_receipt(root, name('node-e'), PINS['node-e'])
            (root / name('node-e')).unlink()
            doc['parts'][0]['file'] = '../secret'
            (root / name('node-e')).write_text(json.dumps(doc))
            with self.assertRaises(p.EvidenceError):
                p.load_receipt(root, name('node-e'), PINS['node-e'])

    def test_cli_repeat_is_identical_and_does_not_relabel_history_live(self):
        cmd = [sys.executable, '-B', str(ROOT / 'bin/federated_projection.py'), '--receipts-root', str(FOLDER),
               '--source', name('node-e') + '=' + PINS['node-e'], '--at', '2026-11-13T10:00:00Z']
        first = subprocess.run(cmd, capture_output=True, check=True)
        second = subprocess.run(cmd, capture_output=True, check=True)
        self.assertEqual(first.stdout, second.stdout)
        rows = [json.loads(line)['record'] for line in first.stdout.splitlines()]
        self.assertEqual(len(rows), 5)
        self.assertEqual(next(r for r in rows if r['node'] == 'node-e')['state'], 'STALE')
        self.assertEqual(next(r for r in rows if r['node'] == 'node-a')['state'], 'NO_DATA')
        bad = cmd.copy()
        bad[bad.index('--source')+1] = name('node-e') + '=' + '0'*64
        failed = subprocess.run(bad, capture_output=True)
        self.assertEqual(failed.returncode, 2)
        self.assertNotIn(str(FOLDER).encode(), failed.stdout + failed.stderr)
        self.assertTrue(all(json.loads(line)['record']['state'] == 'NO_DATA' for line in failed.stdout.splitlines()))


if __name__ == '__main__':
    unittest.main()
