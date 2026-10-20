#!/usr/bin/env python3
"""Tests for bin/format_receipt.py — the receipt is the post (ideas20oct §2)."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FMT = ROOT / "bin" / "format_receipt.py"
sys.path.insert(0, str(ROOT / "bin"))
import format_receipt as fr


HARNESS = {
    "schema": "preceptoros.lab.harness-receipt/1", "suite": "tests",
    "verdict": "GREEN", "coverage": 10, "total": 10, "determinism": True,
    "weight_b": 4173, "speed_s": 4.438, "sha256": "abc123",
    "observed_at": "2026-10-20T00:00:00Z",
    "runtime": {"machine": "x86_64", "python": "3.12.15", "system": "Linux"},
}
YARDSTICK = {
    "schema": "preceptoros.lab.yardstick-receipt/1", "state": "GREEN",
    "command": "python3 -m unittest discover -s tests",
    "observed_at": "2026-10-20T00:00:00Z",
    "runs": [{"state": "GREEN", "passed": 34, "tests": 34, "elapsed_s": 0.17}],
    "runtime": {"machine": "x86_64", "python": "3.12.15", "system": "Linux"},
}


class FormatReceiptTests(unittest.TestCase):
    def test_harness_receipt_mentions_measured_figures(self):
        t = fr.format_harness_receipt(HARNESS)
        self.assertIn("GREEN", t)
        self.assertIn("10/10", t)
        self.assertIn("4173 B", t)
        self.assertIn("abc123", t)
        self.assertIn("FIRMO", t)

    def test_yardstick_receipt_mentions_runs(self):
        t = fr.format_yardstick_receipt(YARDSTICK)
        self.assertIn("GREEN", t)
        self.assertIn("34/34", t)
        self.assertIn("run 1", t)
        self.assertIn("FIRMO", t)

    def test_word_count_under_soft_ceiling(self):
        t = fr.format_harness_receipt(HARNESS)
        self.assertLessEqual(len(t.split()), 150)

    def test_privacy_no_test_names(self):
        t = fr.format_harness_receipt(HARNESS)
        self.assertNotIn("test_", t)
        self.assertIn("counts only", t)

    def test_unknown_schema_is_no_data(self):
        t = fr.format_receipt_dict({"schema": "otro/1"}) if hasattr(fr, "format_receipt_dict") else None
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"schema": "otro/1", "observed_at": "2026-10-20"}, f)
            path = f.name
        t = fr.format_receipt(path)
        self.assertIn("NO_DATA", t)
        self.assertIn("FIRMO", t)

    def test_cli_outputs_log_and_wordcount(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(HARNESS, f)
            path = f.name
        r = subprocess.run([sys.executable, str(FMT), path],
                           capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Harness receipt", r.stdout)
        self.assertIn("words:", r.stderr)

    def test_no_data_cause_preserved(self):
        r = dict(HARNESS)
        r["verdict"] = "NO_DATA"
        r["cause"] = "zero tests discovered"
        t = fr.format_harness_receipt(r)
        self.assertIn("NO_DATA", t)


if __name__ == "__main__":
    unittest.main()
