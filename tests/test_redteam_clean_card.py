from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "benchmarks" / "redteam-20261020" / "CLEAN.md"


class CleanCardTests(unittest.TestCase):
    def test_clean_card_explains_scope_and_limits_without_evidence_payload(self):
        text = CARD.read_text(encoding="utf-8")
        self.assertIn("Purpose:", text)
        self.assertIn("Measured summary:", text)
        self.assertIn("Independent review: NO_DATA", text)
        self.assertNotRegex(text, r"(?i)(?:\d+(?:\.\d+)?/\d+|score|vulnerab|prompt|attack|crucible_|lora_test_|\.json|\.txt)")


if __name__ == "__main__":
    unittest.main()
