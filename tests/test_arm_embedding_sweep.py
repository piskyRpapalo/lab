import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1] / 'benchmarks' / 'arm-embedding-sweep-20261029'
spec = importlib.util.spec_from_file_location('arm_embedding_sweep', ROOT / 'sweep.py')
sweep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sweep)


class EmbeddingSweepTests(unittest.TestCase):
    def test_vectors_are_bounded_to_hash_and_dimensions(self):
        receipt = sweep.vector_receipt([1.0, 2.0])
        self.assertEqual(receipt['dimensions'], 2)
        self.assertEqual(len(receipt['float32_le_sha256']), 64)
        for vector in ([], [float('nan')], [float('inf')], ['not a number'], [True]):
            with self.subTest(vector=vector), self.assertRaises(ValueError):
                sweep.vector_receipt(vector)

    def test_selection_and_response_redaction(self):
        entries = {'models': [
            {'name': 'private-model', 'digest': 'a' * 64, 'size': 10},
            {'name': 'generation', 'digest': 'b' * 64, 'size': 10},
            {'name': 'large', 'digest': 'c' * 64, 'size': sweep.LIMIT + 1}]}
        def fake(route, body=None):
            if route == '/api/tags': return entries
            if route == '/api/show': return {'capabilities': ['embedding'] if body['model'] == 'private-model' else ['completion']}
            return {'embeddings': [[1.0, 2.0]]}
        with mock.patch.object(sweep, 'request', side_effect=fake):
            result = sweep.sweep('private input')
        self.assertEqual(len(result['models']), 1)
        self.assertEqual(result['skipped']['not_embedding'], 1)
        self.assertEqual(result['skipped']['over_size_limit'], 1)
        self.assertEqual(len(result['models'][0]['samples']), 2)
        self.assertNotIn('private input', json.dumps(result))
        self.assertNotIn('private-model', json.dumps(result))
        self.assertNotIn('embeddings', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
