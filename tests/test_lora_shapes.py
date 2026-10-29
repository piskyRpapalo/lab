import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'benchmarks' / 'lora-shapes-20261028'
spec = importlib.util.spec_from_file_location('shape_audit', ROOT / 'shape_audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def write_header(path, data):
    raw = json.dumps(data).encode()
    path.write_bytes(struct.pack('<Q', len(raw)) + raw)


class LoraShapesTests(unittest.TestCase):
    def test_match_and_shape_sabotage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base, adapters = root / 'base', root / 'adapters'
            base.mkdir()
            adapters.mkdir()
            write_header(base / 'base.safetensors', {'model.layer.weight': {'shape': [6, 4]}})
            adapter = adapters / 'adapter_model.safetensors'
            a = 'base_model.model.model.layer.lora_A.weight'
            b = 'base_model.model.model.layer.lora_B.weight'
            write_header(adapter, {a: {'shape': [2, 4]}, b: {'shape': [6, 2]}})
            row = audit.scan(base, adapters)['adapters'][0]
            self.assertEqual((row['pairs'], row['matching_shapes'], row['shape_mismatches']), (1, 1, 0))
            write_header(adapter, {a: {'shape': [2, 5]}, b: {'shape': [6, 2]}})
            row = audit.scan(base, adapters)['adapters'][0]
            self.assertEqual((row['matching_shapes'], row['shape_mismatches']), (0, 1))
            write_header(adapter, {a: {'shape': [2, 4]}})
            self.assertEqual(audit.scan(base, adapters)['adapters'][0]['invalid_pairs'], 1)

    def test_reject_short_and_oversized_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'x'
            path.write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError, 'short_header'):
                audit.read_header(path)
            path.write_bytes(struct.pack('<Q', audit.MAX_HEADER + 1))
            with self.assertRaisesRegex(ValueError, 'invalid_header_size'):
                audit.read_header(path)


if __name__ == '__main__':
    unittest.main()
