import datetime as dt
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rack_status", ROOT / "bin" / "rack_status.py")
rack_status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rack_status)


class RackStatusTests(unittest.TestCase):
    def test_live_becomes_stale_at_exact_seven_day_boundary(self):
        observed = dt.datetime(2026, 10, 12, 10, tzinfo=dt.timezone.utc)
        before = dt.datetime(2026, 10, 19, 9, 59, 59, tzinfo=dt.timezone.utc)
        boundary = dt.datetime(2026, 10, 19, 10, tzinfo=dt.timezone.utc)
        self.assertEqual(rack_status.TTL_DAYS, 7)
        self.assertEqual(rack_status.TTL_SECONDS, 604800)
        self.assertEqual(rack_status.evaluate("LIVE", observed, before), "LIVE")
        self.assertEqual(rack_status.evaluate("LIVE", observed, boundary), "STALE")

    def test_non_live_state_is_preserved(self):
        now = dt.datetime(2026, 10, 19, 10, tzinfo=dt.timezone.utc)
        for state in ("STALE", "STATIC", "SIMULATED", "NO_DATA", "ERROR"):
            with self.subTest(state=state):
                self.assertEqual(rack_status.evaluate(state, None, now), state)

    def test_cli_reports_automatic_transition(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "rack_status.py"),
             "--observed-at", "2026-10-12T10:00:00Z",
             "--now", "2026-10-19T10:00:00Z"],
            check=True, capture_output=True, text=True)
        self.assertIn('"state": "STALE"', result.stdout)


class LlmsTreeTests(unittest.TestCase):
    def verify(self, root):
        return subprocess.run(
            [sys.executable, str(ROOT / "bin" / "verify_llms_tree.py"),
             "--root", str(root)], capture_output=True, text=True)

    def test_resolves_real_files_and_line_anchors(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("title\nbody\n", encoding="utf-8")
            (root / "STATE.md").write_text("status\n", encoding="utf-8")
            (root / "llms.txt").write_text(
                "INDEX: README.md#L2; STATE.md#L1.\n", encoding="utf-8")
            result = self.verify(root)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn("2 indexed paths", result.stdout)

    def test_rejects_missing_path_and_outside_symlink(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            (root / "llms.txt").write_text(
                "INDEX: missing.md#L1; escaped.md\n", encoding="utf-8")
            (root / "escaped.md").symlink_to(Path(outside) / "secret.md")
            result = self.verify(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing or outside tree: missing.md", result.stdout)
            self.assertIn("missing or outside tree: escaped.md", result.stdout)


if __name__ == "__main__":
    unittest.main()

class LlmsTreeBudgetTests(unittest.TestCase):
    def verify(self, root):
        return subprocess.run(
            [sys.executable, str(ROOT / "bin" / "verify_llms_tree.py"),
             "--root", str(root)], capture_output=True, text=True)
    def test_rejects_file_over_piece_ceiling(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "llms.txt").write_text("INDEX: big.md#L1.\n", encoding="utf-8")
            (root / "big.md").write_text("x" * 16385, encoding="utf-8")
            result = self.verify(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("over piece ceiling: big.md 16385 B > 16384 B", result.stdout)
    def test_rejects_index_over_depth_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "llms.txt").write_text(
                "INDEX: a.md#L1; b.md#L1.\nBUDGET: 10.\n", encoding="utf-8")
            (root / "a.md").write_text("hello\n", encoding="utf-8")
            (root / "b.md").write_text("world\n", encoding="utf-8")
            result = self.verify(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("over depth budget: INDEX totals 12 B > 10 B", result.stdout)
    def test_budget_line_reports_measured_total(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "llms.txt").write_text(
                "INDEX: a.md#L1.\nBUDGET: 100.\nDEPTH: declare depth 0-4.\n", encoding="utf-8")
            (root / "a.md").write_text("hello\n", encoding="utf-8")
            result = self.verify(root)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn("depth budget 6 B <= 100 B", result.stdout)
