import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from bin import run_crucible


class ReadingProbeTests(unittest.TestCase):
    def test_poisoned_index_path_is_rejected_by_the_real_guardian(self):
        receipt = run_crucible.run_probe("P5")
        self.assertEqual(receipt["probe"], "P5")
        self.assertEqual(receipt["state"], "SIMULATED")
        self.assertTrue(receipt["detected"])
        self.assertEqual(receipt["probes"], 1)
        self.assertEqual(len(receipt["fixture_sha256"]), 64)

    def test_depth_budget_lure_is_rejected_by_the_real_guardian(self):
        receipt = run_crucible.run_probe("P4")
        self.assertEqual(receipt["probe"], "P4")
        self.assertEqual(receipt["state"], "SIMULATED")
        self.assertTrue(receipt["detected"])

    def test_guardian_false_green_is_red(self):
        with patch.object(run_crucible, "invoke_verifier", return_value=(0, "LIVE")):
            receipt = run_crucible.run_probe("P5")
        self.assertEqual(receipt["state"], "RED")
        self.assertFalse(receipt["detected"])
        self.assertEqual(receipt["cause"], "guardian accepted adversarial input")

    def test_unwired_probes_are_explicit_no_data(self):
        expected = {"P1", "P2", "P3", "P6", "P7", "P8", "P9", "P10", "P11", "P12", "P13"}
        self.assertEqual(set(run_crucible.UNWIRED_PROBES), expected)
        for probe in sorted(expected):
            receipt = run_crucible.run_probe(probe)
            self.assertEqual(receipt["state"], "NO_DATA", probe)
            self.assertFalse(receipt["detected"], probe)
            self.assertTrue(receipt["adversarial"], probe)
            self.assertTrue(receipt["expected"], probe)
            self.assertTrue(receipt["cause"], probe)
            self.assertLess(len(json.dumps(receipt).encode("utf-8")), 1024, probe)

    def test_aggregate_distinguishes_defined_from_detected(self):
        receipt = run_crucible.aggregate_receipt()
        self.assertEqual(receipt["defined"], "13/13")
        self.assertEqual(receipt["detected"], "2/13")
        self.assertEqual(receipt["no_data"], "11/13")
        self.assertLess(len(json.dumps(receipt).encode("utf-8")), 1024)

    def test_receipt_is_compact_and_cli_returns_green(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = run_crucible.main(["--probe", "P4"])
        payload = output.getvalue().strip()
        self.assertEqual(result, 0)
        self.assertLess(len(payload.encode("utf-8")), 1024)
        self.assertTrue(json.loads(payload)["detected"])


if __name__ == "__main__":
    unittest.main()
