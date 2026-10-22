import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATED = re.compile(r"20\d{2}-\d{2}-\d{2}|date\s+NO_DATA", re.IGNORECASE)


class BenchmarkTitleDateTests(unittest.TestCase):
    def test_every_top_level_card_title_states_its_date(self):
        cards = sorted((ROOT / "benchmarks").glob("*/README.md"))
        self.assertGreater(len(cards), 0)
        for card in cards:
            with self.subTest(card=card.parent.name):
                title = next(line.strip() for line in card.read_text().splitlines() if line.strip())
                self.assertRegex(title, DATED)


if __name__ == "__main__":
    unittest.main()
