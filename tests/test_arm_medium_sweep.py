import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1] / 'benchmarks' / 'arm-medium-model-sweep-20261029'
spec = importlib.util.spec_from_file_location('arm_medium_sweep', ROOT / 'sweep.py')
sweep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sweep)


class MediumSweepTests(unittest.TestCase):
    def test_size_boundaries_and_no_input_or_output(self):
        entries = {'models': [
            {'name': 'small', 'digest': 'a' * 64, 'size': sweep.MINIMUM},
            {'name': 'inside', 'digest': 'b' * 64, 'size': sweep.MINIMUM + 1},
            {'name': 'outside', 'digest': 'c' * 64, 'size': sweep.LIMIT + 1}]}
        def fake(route, body=None):
            if route == '/api/tags': return entries
            if route == '/api/show': return {'capabilities': ['completion']}
            return {'done': True, 'response': 'private answer', 'eval_count': 1, 'eval_duration': 1}
        with mock.patch.object(sweep, 'request', side_effect=fake):
            result = sweep.sweep('private input')
        self.assertEqual(len(result['models']), 1)
        self.assertEqual(result['skipped']['below_size_limit'], 1)
        self.assertEqual(result['skipped']['over_size_limit'], 1)
        self.assertNotIn('private input', json.dumps(result))
        self.assertNotIn('private answer', json.dumps(result))
        self.assertNotIn('inside', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
