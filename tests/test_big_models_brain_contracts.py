"""Read-only arithmetic replay of TRAIN-03 physical architecture contract DEV; not model GOLD."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "big-models-20261123"
SOURCE = ROOT / "brain-contracts.json"
EXPECTED = {
    "gpt-oss:120b": {"state": 5, "cache": 11, "head": 14, "tasks": 14, "all_non_cause": 5},
    "qwen3-coder:30b": {"state": 8, "cache": 10, "head": 10, "tasks": 14, "all_non_cause": 4},
    "qwen38-27b-q4xl:latest": {"state": 4, "cache": 8, "head": 6, "tasks": 14, "all_non_cause": 0},
}
CASE_IDS = {"head_rotated_cache_scope", "cross_family_kv_c2c",
            "calm_public_native_edge", "sleep_sim_unwitnessed_live",
            "hetero_pi120b_budget", "acho_parity_visual_voice",
            "s1_revocation_and_mcp_error"}


class Train03BrainContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = SOURCE.read_text(encoding="utf-8")
        cls.data = json.loads(cls.raw)

    def test_physical_receipts_and_42_samples(self):
        d = self.data
        self.assertEqual(d["schema"], "hexelion.train03.brain-contracts-field-audit/1")
        self.assertEqual((d["source_case_count"], d["repetitions"]), (7, 2))
        self.assertFalse(d["gold"])
        self.assertEqual(set(d["models"]), set(EXPECTED))
        self.assertIn("FREE_FORM_SNAKE_CASE_NOT_CLOSED_LABEL_SET", d["cause_contract"])
        for name, row in d["models"].items():
            with self.subTest(model=name):
                self.assertEqual((row["n"], row["strict_json"], row["full_exact"]), (14, 14, 0))
                self.assertEqual(row["field_exact"]["cause"], 0)
                self.assertEqual(row["cause_snake_case_format"], 14)
                self.assertEqual(row["unload"], "PASS_UNLOADED_DMEM0")
                self.assertEqual(row["all_non_cause"], EXPECTED[name]["all_non_cause"])
                self.assertEqual(set(row["bycase"]), CASE_IDS)
                self.assertEqual(sum(v["n"] for v in row["bycase"].values()), 14)
                for case in row["bycase"].values():
                    self.assertEqual(case["n"], 2)
                    for field in ("state", "cause", "cache", "head", "tasks", "exact",
                                  "strict_json", "all_non_cause"):
                        self.assertLessEqual(0, case[field])
                        self.assertLessEqual(case[field], 2)

    def test_field_sums_reproduce_and_no_fake_task_effect(self):
        d = self.data
        for name, row in d["models"].items():
            expected = EXPECTED[name]
            for field in ("state", "cache", "head", "tasks"):
                self.assertEqual(row["field_exact"][field], expected[field])
                self.assertEqual(sum(v[field] for v in row["bycase"].values()),
                                 row["field_exact"][field])
            self.assertEqual(sum(v["all_non_cause"] for v in row["bycase"].values()),
                             expected["all_non_cause"])
        for key in ("actual_tools", "actual_kv_transfers", "real_lora_rotations",
                    "train_steps", "calm_changes", "dream_promotions"):
            self.assertEqual(d[key], 0)

    def test_invalid_initial_fixture_and_dual_runtime_are_not_hidden(self):
        d = self.data
        for key in ("physical_receipt_sha256", "original_invalid_harness_receipt_sha256",
                    "dual_ollama_reconciliation_sha256", "v2_script_sha256"):
            ref = d[key]
            self.assertEqual(len(ref), 64)
            self.assertTrue(all(char in "0123456789abcdef" for char in ref))
        for forbidden in ("raw_prompt", "raw_response", "password", "access_token",
                          "/home/", "100.125.", "100.81."):
            self.assertNotIn(forbidden, self.raw.lower())
        self.assertIn("(brain-contracts.json)",
                      (ROOT / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
