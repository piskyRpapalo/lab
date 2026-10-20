#!/usr/bin/env python3
"""Tests for bin/eval_harness.py — red before green, gates n=2, receipt < 1,024 B."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "bin" / "eval_harness.py"
sys.path.insert(0, str(ROOT / "bin"))
import eval_harness as eh


class EvalHarnessTests(unittest.TestCase):
    def test_module_imports(self):
        self.assertEqual(eh.SCHEMA, "preceptoros.lab.harness-receipt/1")
        self.assertEqual(eh.CEILING, 1024)

    def test_receipt_under_ceiling(self):
        r = eh.attach_hash(eh.evaluate("tests", "test_yardstick_receipt.py", 1, 60))
        ok, size = eh.check_ceiling(r)
        self.assertLess(size, 1024, f"receipt {size} B >= 1024 B")
        self.assertTrue(ok)

    def test_determinism_two_runs_same_counts(self):
        r = eh.evaluate("tests", "test_yardstick_receipt.py", 2, 60)
        a, b = r["runs"]
        self.assertEqual(a.get("tests"), b.get("tests"))
        self.assertEqual(a.get("passed"), b.get("passed"))
        self.assertTrue(r["determinism"])

    def test_green_suite_verdict_green(self):
        r = eh.evaluate("tests", "test_yardstick_receipt.py", 2, 60)
        self.assertEqual(r["verdict"], "GREEN")
        self.assertEqual(r["runs"][0]["state"], "GREEN")

    def test_red_suite_verdict_red(self):
        r = eh.evaluate("tests", "test_agent_contract.py", 1, 60)
        if r["runs"][0]["state"] == "GREEN":
            r = eh.evaluate("tests", "test_ideas18oct_contracts.py", 1, 60)
        if r["runs"][0]["state"] == "RED":
            self.assertEqual(r["verdict"], "RED")
        else:
            self.skipTest("no RED suite available in this tree")

    def test_empty_suite_is_no_data(self):
        with tempfile.TemporaryDirectory() as d:
            r = eh.evaluate(d, "test_*.py", 1, 30)
            self.assertEqual(r["verdict"], "NO_DATA")
            self.assertEqual(r["runs"][0]["state"], "NO_DATA")

    def test_sha256_stable_and_present(self):
        r1 = eh.attach_hash(eh.evaluate("tests", "test_yardstick_receipt.py", 1, 60))
        body = {k: v for k, v in r1.items() if k != "sha256"}
        r2 = dict(body)
        r2["sha256"] = r1["sha256"]
        self.assertEqual(r1["sha256"], eh.attach_hash(dict(body))["sha256"])

    def test_compare_ranks(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "a.json"
            b = Path(d) / "b.json"
            ra = {"schema": eh.SCHEMA, "suite": "a", "verdict": "GREEN",
                  "coverage": 10, "determinism": True, "weight_b": 1024, "speed_s": 1.0}
            rb = {"schema": eh.SCHEMA, "suite": "b", "verdict": "GREEN",
                  "coverage": 20, "determinism": True, "weight_b": 1024, "speed_s": 1.0}
            a.write_text(json.dumps(ra))
            b.write_text(json.dumps(rb))
            res = eh.compare(str(a), str(b))
            self.assertEqual(res["winner"], "B")
            self.assertGreater(res["score_b"], res["score_a"])

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            green = subprocess.run(
                [sys.executable, str(EVAL), "--suite", "tests",
                 "--pattern", "test_yardstick_receipt.py", "--runs", "1", "--timeout", "60"],
                capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(green.returncode, 0, green.stdout + green.stderr)
            self.assertIn('"verdict":"GREEN"', green.stdout)
            empty = subprocess.run(
                [sys.executable, str(EVAL), "--suite", d, "--runs", "1", "--timeout", "30"],
                capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(empty.returncode, 2)
            self.assertIn("NO_DATA", empty.stdout)

    def test_sabotage_over_ceiling_is_no_data(self):
        r = {"schema": eh.SCHEMA, "suite": "x", "verdict": "GREEN",
             "padding": "x" * 2000}
        ok, size = eh.check_ceiling(r)
        self.assertFalse(ok)
        self.assertGreaterEqual(size, 1024)


if __name__ == "__main__":
    unittest.main()
