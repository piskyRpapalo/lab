import json
import tempfile
import unittest
from pathlib import Path

from bin import study_spec_runner as runner

ROOT = Path(__file__).resolve().parents[1]


class StudySpecRunnerTests(unittest.TestCase):
    def test_template_validates_and_dry_run_emits_bounded_receipt(self):
        loaded = runner.cargar_spec(ROOT / "study_spec.json")
        self.assertEqual(loaded["estado"], "VALIDA")
        result = runner.despachar_a_anillos(loaded["spec"])
        consolidated = runner.consolidar_resultados(list(result["anillos"].values()))
        receipt = runner.emitir_recibo(consolidated, "test-machine", "2026-10-22T00:00:00Z")
        self.assertLess(len(receipt.encode()), 1024)
        self.assertIn('"cause":"one or more ring results are NO_DATA"', receipt)

    def test_no_data_variables_keep_their_cause_and_do_not_dispatch(self):
        loaded = runner.cargar_spec(ROOT / "study_spec.json")
        self.assertEqual(loaded["spec"]["variables"]["TREND_VECTOR"]["state"], "NO_DATA")
        self.assertTrue(loaded["spec"]["variables"]["TREND_VECTOR"]["cause"])
        self.assertEqual(runner.ejecutar_en_anillo(loaded["spec"], "EDGE")["estado"], "NO_DATA")

    def test_ceiling_rejects_whole(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "spec.json"
            path.write_bytes(b" " * 1024)
            result = runner.cargar_spec(path)
        self.assertEqual(result["estado"], "RECHAZADA")
        self.assertIn("1024-byte", result["causa"])

    def test_bad_variable_and_ring_are_rejected(self):
        loaded = runner.cargar_spec(ROOT / "study_spec.json")["spec"]
        bad = json.loads(json.dumps(loaded))
        bad["variables"]["TREND_VECTOR"] = {"state": "NO_DATA"}
        self.assertEqual(runner.validar_variables(bad)["estado"], "RECHAZADA")
        self.assertEqual(runner.ejecutar_en_anillo(loaded, "RING-4")["estado"], "RECHAZADA")


if __name__ == "__main__":
    unittest.main()
