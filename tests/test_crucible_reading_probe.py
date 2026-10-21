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
