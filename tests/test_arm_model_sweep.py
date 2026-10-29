import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1] / 'benchmarks' / 'arm-small-model-sweep-20261029'
spec = importlib.util.spec_from_file_location('arm_sweep', ROOT / 'sweep.py')
sweep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sweep)


class SweepTests(unittest.TestCase):
    def test_limits_and_private_text(self):
        entries = {'models': [
            {'name': 'private-name', 'digest': 'a' * 64, 'size': 10},
            {'name': 'embedding', 'digest': 'b' * 64, 'size': 10},
            {'name': 'large', 'digest': 'c' * 64, 'size': sweep.LIMIT + 1}]}
        answer = {'done': True, 'response': 'private answer', 'eval_count': 1, 'eval_duration': 1}
        def fake(route, body=None):
            if route == '/api/tags':
                return entries
            if route == '/api/show':
                return {'capabilities': ['completion'] if body['model'] == 'private-name' else ['embedding']}
            return answer
        with mock.patch.object(sweep, 'request', side_effect=fake):
            result = sweep.sweep('private input')
        self.assertEqual(len(result['models']), 1)
        self.assertEqual(result['skipped']['not_completion'], 1)
        self.assertEqual(result['skipped']['over_size_limit'], 1)
        self.assertEqual(len(result['models'][0]['samples']), 2)
        for private in ('private input', 'private answer', 'private-name'):
            self.assertNotIn(private, json.dumps(result))

    def test_empty_output_and_service_error_are_not_success(self):
        entries = {'models': [{'name': 'fixture', 'digest': 'a' * 64, 'size': 1}]}
        def fake(route, body=None):
            if route == '/api/tags': return entries
            if route == '/api/show': return {'capabilities': ['completion']}
            return {'done': True, 'response': ''}
        with mock.patch.object(sweep, 'request', side_effect=fake):
            result = sweep.sweep('synthetic')
        self.assertTrue(all(s['state'] == 'NO_DATA' for s in result['models'][0]['samples']))
        with self.assertRaises(ValueError):
            sweep.sweep('')


if __name__ == '__main__':
    unittest.main()
