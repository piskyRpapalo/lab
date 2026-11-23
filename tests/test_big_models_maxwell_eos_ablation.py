"""TRAIN-03 Maxwell EOS ablation: published aggregate contract only, no private samples."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORT = ROOT / "benchmarks" / "big-models-20261123" / "maxwell-eos-ablation-20261123.json"


class MaxwellEosAblationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_schema_and_nonpromotion(self):
        data = self.data
        self.assertEqual(data["schema"], "hexelion.train03.maxwell-eos-ablation/1")
        self.assertIn("NON_GOLD", data["scope"])
        self.assertIn("NO_TRAINING", data["scope"])
        self.assertIn("NO_PROMOTION", data["scope"])
        self.assertIn("NO_DATA(", data["results"]["note"])

    def test_generation_ablation_preserves_baseline_settings(self):
        change = self.data["intervention"]
        self.assertEqual(change["previous_eos_generation_config"], [2, 200001])
        self.assertEqual(change["new_explicit_eos_argument"], [2, 200001])
        self.assertFalse(change["previous_explicit_eos_argument"])
        self.assertTrue(change["original_fixture_kept"])
        self.assertEqual(change["planned_samples"], len(change["case_ids"]) * change["repeats"])
        self.assertEqual(len(change["runner_sha256"]), 64)

    def test_pending_not_promoted_to_score(self):
        results = self.data["results"]
        if self.data["status"].startswith("PHYSICAL_RUNNING"):
            self.assertIsNone(results["valid_complete_json"])
            self.assertIsNone(results["fully_exact"])
            self.assertIsNone(results["final_unit_result"])
            self.assertIsNone(results["gpu_unloaded"])
        else:
            self.assertIn(self.data["status"], ("PASS_DEV_COMPLETE", "FAIL_DEV_RUN", "HOLD_RESOURCE"))
        self.assertEqual(self.data["evidence"]["prior_baseline_full_strict_json"], 0)
        self.assertEqual(self.data["evidence"]["prior_baseline_full_exact"], 0)

    def test_no_raw_private_material_in_report(self):
        content = REPORT.read_text(encoding="utf-8")
        for key in ('"raw"', '"prompt"', '"completion"', '"private_key"', '"model_output"'):
            self.assertNotIn(key, content)
        self.assertTrue(all("status" in item and "next" in item for item in self.data["next_models"]))


if __name__ == "__main__":
    unittest.main()
