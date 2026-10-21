from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "ENERGY_BUDGET.md"
FORMULA = "`J_net/token = (ΔE_paquete_J − P_idle_W × Δt_s) / tokens_generados`"


class EnergyBudgetEnglishTests(unittest.TestCase):
    def test_translation_keeps_formula_and_no_data_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("# ENERGY_BUDGET · proposal REQUIRES_FIRMA", text)
        self.assertIn(FORMULA, text)
        self.assertIn("Generated-token count and net joules/token: `NO_DATA`", text)
        self.assertIn("Wall-power meter: `NO_DATA`", text)
        self.assertIn("does not represent wall consumption", text)
        self.assertIn("10 thermal channels visible", text)
        self.assertIn("No inference traffic was generated", text)


if __name__ == "__main__":
    unittest.main()
