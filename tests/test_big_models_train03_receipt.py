"""Arithmetic/privacy replay of published TRAIN-03 model aggregates; no live inference."""
import json
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "benchmarks"
          / "big-models-20261123" / "observations.json")


class BigModelsTrain03ReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = SOURCE.read_text(encoding="utf-8")
        cls.report = json.loads(cls.raw)

    def test_model_coverage_and_unique_ids(self):
        self.assertEqual(self.report["schema"], "hexelion.train03.big-models-observations/1")
        models = self.report["models"]
        self.assertEqual(len(models), 14)
        self.assertEqual(len({m["id"] for m in models}), len(models))
        self.assertTrue(all(m["state"] for m in models))

    def test_arithmetic_bounds_and_noncomparable_cohorts(self):
        cohort = self.report["measurement_sources"]
        self.assertEqual(cohort["six_case_pilot"]["samples_per_model"], 12)
        self.assertEqual(cohort["mistral_nine_case"]["samples"], 18)
        for model in self.report["models"]:
            if model["state"] == "MEASURED_DEV":
                self.assertIn(model["samples"], (12, 18))
                self.assertLessEqual(0, model["exact"])
                self.assertLessEqual(model["exact"], model["strict_json"])
                self.assertLessEqual(model["strict_json"], model["samples"])
                self.assertGreater(model["peak_vram_bytes"], 0)
            elif model["samples"] == 0:
                self.assertIsNone(model["exact"])
                self.assertIsNone(model["strict_json"])
                self.assertIsNone(model["median_s"])

    def test_maxwell_full_output_fail_not_inferred_pass(self):
        rows = {m["id"]: m for m in self.report["models"]}
        model = rows["maxwell-v1-flash-bf16"]
        self.assertEqual((model["samples"], model["strict_json"], model["exact"]),
                         (12, 0, 0))
        self.assertEqual(model["prefix_schema_diagnostic"], 12)
        self.assertEqual(model["prefix_exact_diagnostic"], 8)
        self.assertGreater(model["run_elapsed_s"], 1000)

    def test_preflight_never_becomes_real_effect(self):
        meta = self.report["reliability"]
        self.assertIs(meta["gold"], False)
        self.assertIs(meta["blind_holdout"], False)
        for key in ("real_tool_calls", "new_training_runs", "model_promotions",
                    "real_cross_model_KV_transfers",
                    "verified_cross_device_routed_turns", "verified_voice_parity"):
            self.assertEqual(meta[key], 0)
        hard = self.report["measurement_sources"]["hard_dev_round2"]
        self.assertEqual(hard["samples_planned"], hard["cases"] * hard["repetitions"] * hard["models_planned"])
        self.assertFalse(hard["has_gold"])

    def test_no_raw_or_personal_source_data(self):
        forbidden = ("raw_prompt", "raw_response", "completion_text", "ssh_key",
                     "private_address", "user_email", "password", "access_token",
                     "/home/", "100.125.", "100.81.")
        lower = self.raw.lower()
        for marker in forbidden:
            self.assertNotIn(marker, lower)
        for m in self.report["models"]:
            self.assertEqual(set(m.keys()) & {"raw", "prompt", "response"}, set())


if __name__ == "__main__":
    unittest.main()
