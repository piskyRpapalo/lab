import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "redteam-20261020"


class RedTeamCleanCardTests(unittest.TestCase):
    def test_cover_is_summary_and_verdict_with_evidence_separate(self):
        entries = list(ROOT.iterdir())
        self.assertEqual({entry.name for entry in entries}, {"README.md", "evidence"})
        self.assertTrue((ROOT / "evidence").is_dir())
        cover = (ROOT / "README.md").read_text()
        self.assertLess(len(cover.encode("utf-8")), 1024)
        lines = [line.strip() for line in cover.splitlines() if line.strip()]
        self.assertEqual(len(lines), 2)
        self.assertIn("2026-10-20", lines[0])
        self.assertTrue(lines[1].startswith("Verdict:"))
        self.assertIn("evidence/", lines[1])


if __name__ == "__main__":
    unittest.main()
