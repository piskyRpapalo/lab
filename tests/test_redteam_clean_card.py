from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "benchmarks" / "redteam-20261020" / "CLEAN.md"


class CleanCardTests(unittest.TestCase):
    def test_clean_card_is_one_line_verdict_without_evidence_payload(self):
        text = CARD.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], r"^Verdict: (?:NO_DATA|PASS|FAIL) — .+\.$")
        self.assertNotRegex(text, r"(?i)(?:\d+(?:\.\d+)?/\d+|score|vulnerab|prompt|attack)")


if __name__ == "__main__":
    unittest.main()
