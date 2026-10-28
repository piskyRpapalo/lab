import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1] / 'benchmarks' / 'model-inventory-20261028'
spec = importlib.util.spec_from_file_location('inventory', ROOT / 'inventory.py')
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def test_adapter_inventory_reports_scope_and_no_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = root / 'private-label'
            child.mkdir()
            (child / 'adapter_model.safetensors').write_bytes(b'example')
            result = inventory.adapters(root)
            self.assertEqual(result['weight_files'], 1)
            self.assertEqual(result['rows'][0]['config_state'], 'NO_DATA')
            self.assertNotIn('private-label', json.dumps(result))
            (child / 'adapter_config.json').write_text('{}')
            self.assertEqual(inventory.adapters(root)['rows'][0]['config_state'], 'MEASURED')
        self.assertEqual(inventory.adapters(root)['state'], 'NO_DATA')

    def test_service_inventory_omits_names_and_rejects_bad_digest(self):
        response = mock.MagicMock()
        response.__enter__.return_value = io.BytesIO(json.dumps({'models': [
            {'name': 'private-label', 'digest': 'a' * 64, 'size': 17}]}).encode())
        with mock.patch.object(inventory.urllib.request, 'urlopen', return_value=response):
            result = inventory.models()
        self.assertEqual(result['manifest_entries'], 1)
        self.assertNotIn('private-label', json.dumps(result))
        response.__enter__.return_value = io.BytesIO(b'{"models":[{"digest":"bad","size":17}]}')
        with mock.patch.object(inventory.urllib.request, 'urlopen', return_value=response):
            self.assertEqual(inventory.models()['state'], 'NO_DATA')


if __name__ == '__main__':
    unittest.main()
