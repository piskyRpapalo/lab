import importlib.util
import unittest
from pathlib import Path


PATH = Path(__file__).resolve().parents[1] / "bin" / "measure_yardstick.py"
SPEC = importlib.util.spec_from_file_location("measure_yardstick", PATH)
measure_yardstick = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(measure_yardstick)


class YardstickReceipt(unittest.TestCase):
    def test_green_summary_keeps_counts_and_omits_output(self):
        row = measure_yardstick.summarize(0, "Ran 25 tests in 0.123s\nOK (skipped=2)", 0.2)
        self.assertEqual((row["state"], row["tests"], row["passed"], row["skipped"]),
                         ("GREEN", 25, 23, 2))
        self.assertNotIn("output", row)
        self.assertNotIn("names", row)

    def test_failures_remain_red_even_with_summary(self):
        row = measure_yardstick.summarize(1, "Ran 4 tests in 0.01s\nFAILED (failures=1)", 0.02)
        self.assertEqual((row["state"], row["failures"], row["passed"]), ("RED", 1, 3))

    def test_missing_summary_is_no_data_with_cause(self):
        row = measure_yardstick.summarize(1, "runner stopped before unittest summary", 0.5)
        self.assertEqual(row["state"], "NO_DATA")
        self.assertTrue(row["cause"])

    def test_zero_discovered_tests_is_no_data(self):
        row = measure_yardstick.summarize(0, "Ran 0 tests in 0.001s\nOK", 0.01)
        self.assertEqual(row["state"], "NO_DATA")
        self.assertTrue(row["cause"])


if __name__ == "__main__":
    unittest.main()
