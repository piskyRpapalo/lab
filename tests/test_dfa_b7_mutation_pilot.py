"""Red-before-green evidence for three targeted F6 perturbations."""
import importlib.util
from pathlib import Path
import unittest

target = Path(__file__).resolve().parents[1] / "bin" / "dfa_b7_mutation_pilot.py"
spec = importlib.util.spec_from_file_location("dfa_b7", target)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TestDfaB7Pilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = m.pilot()

    def test_baseline_green(self):
        self.assertEqual(self.result["baseline"], "GREEN")

    def test_all_declared_mutants_attempted(self):
        self.assertEqual(self.result["mutants"], 3)

    def test_boundary_mutants_killed(self):
        self.assertEqual(self.result["killed"], 3)

    def test_no_full_dfa_claim(self):
        self.assertTrue(self.result["suite_at_large"].startswith("NO_DATA"))

    def test_scoped_measurement(self):
        self.assertEqual(self.result["scope"], "F6_FIXTURES_ONLY")


if __name__ == "__main__":
    unittest.main()
