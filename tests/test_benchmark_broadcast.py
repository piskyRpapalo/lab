import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = re.compile(
    r"^Broadcast receipt: figure=.+ \| model=.+ \| machine=.+ \| "
    r"date=.+ \| sha256=.+$"
)


class BenchmarkBroadcastTests(unittest.TestCase):
    def test_every_top_level_card_starts_with_a_broadcast_receipt(self):
        cards = sorted((ROOT / "benchmarks").glob("*/README.md"))
        self.assertGreater(len(cards), 0)
        for card in cards:
            with self.subTest(card=card.parent.name):
                lines = [line.strip() for line in card.read_text().splitlines() if line.strip()]
                self.assertGreaterEqual(len(lines), 2)
                receipt = next(
                    (line for line in lines[:2] if line.startswith("Broadcast receipt:")),
                    "",
                )
                self.assertRegex(receipt, RECEIPT)
                self.assertLess(len(receipt.encode("utf-8")), 1024)


if __name__ == "__main__":
    unittest.main()
