import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from bin import agente_mantenedor as maintainer


class MaintainerTests(unittest.TestCase):
    def test_missing_gate_paths_are_no_data_and_global_is_no_data(self):
        report = maintainer.consolidar([maintainer.correr_gates_web(), maintainer.correr_gates_app(), maintainer.correr_gates_lab()])
        self.assertEqual(report["state"], "NO_DATA")
        self.assertEqual(maintainer.verificar_umbrales(report)["estado"], "NO_DATA")

    def test_red_gate_dominates_missing_receipts(self):
        report = maintainer.consolidar([{"estado": "ROJO", "tests": "0/2", "causa": "red"}])
        self.assertEqual(report["state"], "ROJO")
        self.assertEqual(maintainer.verificar_umbrales(report)["estado"], "ROJO")

    def test_runner_counts_only_and_hashes_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "test_web.py").write_text("print('Ran 1 test in 0.01s')\n", encoding="utf-8")
            result = maintainer.correr_gates_web(root)
        self.assertEqual(result["estado"], "VERDE")
        self.assertEqual(result["tests"], "1/1")
        self.assertEqual(len(result["sha256"]), 64)
        self.assertNotIn("test_ok", json.dumps(result))

    def test_receipt_below_ceiling_and_signature_no_data_is_explicit(self):
        report = maintainer.consolidar([maintainer._no_data("missing") for _ in range(3)])
        encoded = maintainer.emitir_reporte(report)
        data = json.loads(encoded)
        self.assertLess(len(encoded.encode()), 1024)
        self.assertEqual(data["signature"]["estado"], "NO_DATA")
        self.assertTrue(data["signature"]["causa"])

    @unittest.skipUnless(shutil.which("ssh-keygen"), "NO_DATA: ssh-keygen unavailable")
    def test_signing_uses_supplied_agent_key_only(self):
        with tempfile.TemporaryDirectory() as folder:
            key = Path(folder) / "key"
            subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)], check=True)
            report = maintainer.consolidar([maintainer._no_data("missing") for _ in range(3)])
            encoded = maintainer.emitir_reporte(report, key)
            signed = json.loads(encoded)
        self.assertLess(len(encoded.encode()), 1024)
        self.assertEqual(signed["signature"]["estado"], "FIRMADO_POR_AGENTE")


if __name__ == "__main__":
    unittest.main()
