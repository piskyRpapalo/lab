import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "benchmarks" / "plot-morphism-20261021" / "README.md"
SPEC = ROOT / "study_spec.json"


class PlotMorphismCardTests(unittest.TestCase):
    def test_card_preserves_no_data_and_measured_scope_counts(self):
        card = CARD.read_text(encoding="utf-8")
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        self.assertIn("Verdict: `NO_DATA`", card)
        self.assertIn("10 served HTML files", card)
        self.assertIn("128 `public/game/*.js` modules", card)
        self.assertIn("40 `public/assets/*.js` modules", card)
        self.assertIn("five study variables are all `NO_DATA`", card)
        self.assertIn("not a count of rendered visual elements", card)
        self.assertTrue(all(v["state"] == "NO_DATA" and v.get("cause") for v in spec["variables"].values()))


if __name__ == "__main__":
    unittest.main()
