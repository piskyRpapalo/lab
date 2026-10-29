"""The station receipt retains metrics and digests, not generation text."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'benchmarks' / 'station-96-first-pass-20261029' / 'large.py'
spec = importlib.util.spec_from_file_location('station_large', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LargeReceiptTest(unittest.TestCase):
    def test_receipt_keeps_counts_and_not_raw_text(self):
        def fake(path, payload=None):
            if path == '/api/tags':
                return {'models': [{'name': module.MODEL, 'digest': 'a' * 64, 'size': 123, 'details': {}}]}
            if path == '/api/ps':
                return {'models': [{'name': module.MODEL, 'size': 123, 'size_vram': 100, 'context_length': 2048}]}
            if payload.get('keep_alive') == 0:
                return {}
            return {'done': True, 'response': 'private answer', 'eval_count': 2, 'eval_duration': 100}
        out = io.StringIO()
        with patch.object(module, 'request', side_effect=fake), patch('sys.stdin', io.StringIO('private input')), contextlib.redirect_stdout(out):
            module.main()
        receipt = json.loads(out.getvalue())
        self.assertNotIn('private input', out.getvalue())
        self.assertNotIn('private answer', out.getvalue())
        self.assertEqual(receipt['eval_count'], 2)
        self.assertEqual(receipt['loaded'][0]['context_length'], 2048)
        self.assertEqual(len(receipt['response_sha256']), 64)

    def test_missing_model_fails_closed(self):
        with patch.object(module, 'request', return_value={'models': []}), patch('sys.stdin', io.StringIO('input')):
            with self.assertRaisesRegex(SystemExit, 'NO_DATA'):
                module.main()


if __name__ == '__main__':
    unittest.main()
