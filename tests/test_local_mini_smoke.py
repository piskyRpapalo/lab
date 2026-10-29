import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1] / 'benchmarks' / 'local-mini-smoke-20261028'
spec = importlib.util.spec_from_file_location('mini_smoke', ROOT / 'run.py')
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class MiniSmokeTests(unittest.TestCase):
    def test_receipt_does_not_contain_input_or_output(self):
        models = {'models': [{'name': 'fixture', 'digest': 'a' * 64}]}
        answer = {'done': True, 'response': 'private answer', 'eval_count': 1,
                  'eval_duration': 1, 'done_reason': 'stop'}
        output = io.StringIO()
        with mock.patch.object(smoke, 'request', side_effect=[models, answer, answer, models]), \
             mock.patch.object(smoke.sys, 'stdin', io.StringIO('private input')), \
             mock.patch.object(smoke.sys, 'stdout', output), \
             mock.patch.object(smoke.sys, 'argv', ['run.py', '--model', 'fixture']):
            smoke.main()
        receipt = json.loads(output.getvalue())
        self.assertNotIn('private input', output.getvalue())
        self.assertNotIn('private answer', output.getvalue())
        self.assertEqual(len(receipt['samples']), 2)
        self.assertEqual(receipt['samples'][0]['response_bytes'], len('private answer'))


if __name__ == '__main__':
    unittest.main()
