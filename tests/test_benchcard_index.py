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

    def test_every_card_has_uniform_benchcard_and_broadcast_receipt(self):
        cards = sorted((ROOT / "benchmarks").glob("*/README.md"))
        self.assertEqual(len(cards), 26)
        for card in cards:
            with self.subTest(card=card.parent.name):
                text = card.read_text(encoding="utf-8")
                lines = text.splitlines()
                title = next((line for line in lines if line.startswith("#")), "")
                self.assertRegex(title, r"20\d{2}-\d{2}-\d{2}|date\s+NO_DATA")
                for field in ("Benchcard:", "Broadcast receipt:"):
                    self.assertEqual(sum(line.startswith(field) for line in lines), 1)

    def test_root_index_links_every_benchmark_card(self):
        index = (ROOT / "benchmarks" / "README.md").read_text(encoding="utf-8")
        for card in sorted((ROOT / "benchmarks").glob("*/README.md")):
            self.assertIn(f"({card.parent.name}/README.md)", index)


if __name__ == "__main__":
    unittest.main()
