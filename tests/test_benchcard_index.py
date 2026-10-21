from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BenchcardIndexTests(unittest.TestCase):
    def test_broadcast_receipt_has_all_five_fields(self):
        text = (ROOT / "benchmarks" / "README.md").read_text(encoding="utf-8")
        line = next((row for row in text.splitlines() if row.startswith("Broadcast receipt:")), "")
        for field in ("figure", "model", "machine", "date", "sha256"):
            self.assertIn(field, line)
        self.assertIn("NO_DATA", line)
        self.assertIn("cause", line)

    def test_undated_titles_are_explicit_without_inventing_measurement_dates(self):
        expected = {
            "bench-fluency": "2026-10-15",
            "g0": "2026-07-18",
            "tg32": "NO_DATA",
            "harness-receipts": "2026-10-20",
            "receipts": "2026-10-19",
        }
        for folder, marker in expected.items():
            with self.subTest(folder=folder):
                path = ROOT / "benchmarks" / folder / "README.md"
                self.assertTrue(path.is_file())
                title = next((row for row in path.read_text(encoding="utf-8").splitlines() if row.startswith("#")), "")
                self.assertIn(marker, title)


if __name__ == "__main__":
    unittest.main()
