import tempfile
import unittest
from pathlib import Path

from bin.verify_depth_budgets import inspect


class DepthBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "readme.md").write_bytes(b"1234")
        self.roots = {"web": self.root}

    def tearDown(self):
        self.temp.cleanup()

    def row(self, budget=4, targets=None):
        return {"schema": "declared-depth-targets/1", "depths": [{
            "depth": 0, "budget_bytes": budget,
            "targets": targets if targets is not None else [{"repo": "web", "path": "readme.md"}]
        }]}

    def test_measured_target_within_budget_is_live(self):
        self.assertEqual(inspect(self.row(), self.roots)[0]["status"], "LIVE")

    def test_over_budget_target_is_red(self):
        result = inspect(self.row(budget=3), self.roots)[0]
        self.assertEqual((result["status"], result["bytes"]), ("RED", 4))

    def test_missing_budget_is_no_data(self):
        result = inspect(self.row(budget=None), self.roots)[0]
        self.assertEqual(result["status"], "NO_DATA")

    def test_missing_target_is_red(self):
        result = inspect(self.row(targets=[{"repo": "web", "path": "absent.md"}]), self.roots)[0]
        self.assertEqual((result["status"], result["cause"]), ("RED", "target_missing"))

    def test_path_escape_is_red(self):
        result = inspect(self.row(targets=[{"repo": "web", "path": "../outside"}]), self.roots)[0]
        self.assertEqual(result["cause"], "target_escapes_repository")

    def test_piece_over_ceiling_is_red(self):
        (self.root / "large.md").write_bytes(b"x" * 16385)
        result = inspect(self.row(targets=[{"repo": "web", "path": "large.md"}]), self.roots)[0]
        self.assertEqual(result["cause"], "piece_limit_exceeded")


if __name__ == "__main__":
    unittest.main()
