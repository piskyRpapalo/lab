import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'benchmarks' / 'lora-shapes-20261028'
spec = importlib.util.spec_from_file_location('finite_audit', ROOT / 'finite_audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def fixture(path, header, payload):
    encoded = json.dumps(header).encode()
    path.write_bytes(struct.pack('<Q', len(encoded)) + encoded + payload)


class FiniteAuditTests(unittest.TestCase):
    def test_detects_nan_and_infinity_without_returning_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'adapter'
            header = {'test': {'dtype': 'F32', 'shape': [4], 'data_offsets': [0, 16]}}
            fixture(path, header, struct.pack('<4f', 1.0, float('nan'), float('inf'), -2.0))
            result = audit.inspect(path)
            self.assertEqual((result['finite_values'], result['nan_values'], result['infinite_values']), (2, 1, 1))
            self.assertNotIn('test', json.dumps(result))

    def test_rejects_bad_offsets_and_unsupported_dtype(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'adapter'
            fixture(path, {'a': {'dtype': 'F32', 'shape': [1], 'data_offsets': [1, 5]}}, b'12345')
            with self.assertRaisesRegex(ValueError, 'overlap_or_gap'):
                audit.inspect(path)
            fixture(path, {'a': {'dtype': 'F16', 'shape': [1], 'data_offsets': [0, 2]}}, b'12')
            with self.assertRaisesRegex(ValueError, 'unsupported_dtype'):
                audit.inspect(path)


if __name__ == '__main__':
    unittest.main()
