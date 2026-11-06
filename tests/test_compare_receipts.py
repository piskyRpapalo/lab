import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location("compare_receipts", pathlib.Path(__file__).parents[1] / "bin" / "compare_receipts.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def receipt(device, value):
    return {"state": "MEASURED", "device": device, "value": value,
            "workload": "synthetic", "workload_version": "1", "parameters_digest": "a" * 64,
            "metric": "latency", "unit": "ms", "method": "fixture-clock",
            "observed_at": "2026-11-06T00:00:00Z", "source": "fixture"}


class ComparisonTests(unittest.TestCase):
    def test_matching_conditions_keep_sources_and_delta(self):
        result = module.compare(receipt("a", 5), receipt("b", 8))
        self.assertEqual(result["state"], "COMPARABLE")
        self.assertEqual(result["difference"], 3)
        self.assertEqual(result["left"]["source"], "fixture")
        self.assertIn("not independently verified", result["scope"])

    def test_every_condition_is_required_and_matching(self):
        for field in module.MATCH:
            for variant in ("different", ""):
                with self.subTest(field=field, variant=variant):
                    other = receipt("b", 8)
                    other[field] = variant
                    self.assertEqual(module.compare(receipt("a", 5), other)["state"], "NO_DATA")

    def test_missing_or_invalid_measurements_never_become_zero(self):
        for value in (None, float("nan"), float("inf"), True, "5"):
            with self.subTest(value=value):
                self.assertEqual(module.compare(receipt("a", 5), receipt("b", value))["state"], "NO_DATA")
        other = receipt("b", 8)
        other["state"] = "NO_DATA"
        self.assertEqual(module.compare(receipt("a", 5), other)["state"], "NO_DATA")
        self.assertEqual(module.compare(receipt("a", 1e308), receipt("b", -1e308))["state"], "NO_DATA")


if __name__ == "__main__":
    unittest.main()
