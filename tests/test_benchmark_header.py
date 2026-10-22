import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEADER = re.compile(
    r"^Benchcard: machine=.+ \| date=.+ \| runner=.+ \| quant=.+ \| sha256=.+$"
)


class BenchmarkHeaderTests(unittest.TestCase):
    def test_every_top_level_card_has_a_uniform_header(self):
        cards = sorted((ROOT / "benchmarks").glob("*/README.md"))
        self.assertGreater(len(cards), 0)
        for card in cards:
            with self.subTest(card=card.parent.name):
                lines = [line.strip() for line in card.read_text().splitlines() if line.strip()]
                header = next((line for line in lines[:3] if line.startswith("Benchcard:")), "")
                self.assertRegex(header, HEADER)
                self.assertLess(len(header.encode("utf-8")), 1024)


if __name__ == "__main__":
    unittest.main()
