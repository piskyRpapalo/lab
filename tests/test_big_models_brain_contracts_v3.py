"""Read-only replay of owner-verified TRAIN-03 V3 counts; physical GPU is not tested here."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "big-models-20261123"
V3 = ROOT / "brain-contracts-v3.json"
CASE_IDS = {
    "acho_parity_visual_voice", "calm_public_native_edge",
    "cross_family_kv_c2c", "head_rotated_cache_scope",
    "hetero_pi120b_budget", "s1_revocation_and_mcp_error",
    "sleep_sim_unwitnessed_live",
}
EXPECTED = {
    "qwen3-coder:30b": {"strict_json": 14, "exact": 0, "state": 6,
                          "cause": 10, "cache": 8, "head": 12, "tasks": 14},
    "qwen38-27b-q4xl:latest": {"strict_json": 14, "exact": 0, "state": 4,
                                  "cause": 14, "cache": 8, "head": 6, "tasks": 14},
    "gpt-oss:120b": {"strict_json": 9, "exact": 2, "state": 2,
                       "cause": 8, "cache": 5, "head": 9, "tasks": 9},
}
FIELDS = ("strict_json", "exact", "state", "cause", "cache", "head", "tasks")


class Train03BrainContractsClosedCauseV3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = V3.read_text(encoding="utf-8")
        cls.data = json.loads(cls.raw)

    def test_physical_receipts_scoped_and_sanitized(self):
        d = self.data
        self.assertEqual(d["schema"],
                         "hexelion.train03.brain-contracts-closed-cause-field-audit/1")
        self.assertEqual(d["status"], "PASS_DEV_COMPLETE")
        self.assertEqual((d["case_count"], d["repetitions"],
                          d["source_response_files"]), (7, 2, 42))
        self.assertTrue(d["all_21_pairs_repeated_twice"])
        self.assertFalse(d["gold"])
        self.assertFalse(d["training"])
        for key in ("real_tools", "kv_tensors_transferred", "head_rotations",
                    "calm_deployments", "sleep_promotions"):
            self.assertEqual(d[key], 0)
        self.assertIn("CLOSED_ENUM_7", d["cause_contract"])
        self.assertEqual(d["postflight"]["canonical_ollama_resident_models"], 0)
        self.assertEqual(d["postflight"]["drm_vram_used_bytes"], 612917248)
        for sha in d["hashes"].values():
            self.assertEqual(len(sha), 64)
            self.assertTrue(all(c in "0123456789abcdef" for c in sha))
        for secret in ("raw_prompt", "raw_response", "password", "access_token",
                       "/home/", "100.125.", "100.81.", "private_response"):
            self.assertNotIn(secret, self.raw.lower())

    def test_field_and_case_replay(self):
        self.assertEqual(set(self.data["models"]), set(EXPECTED))
        for model, row in self.data["models"].items():
            with self.subTest(model=model):
                self.assertEqual(row["n"], 14)
                self.assertEqual(row["unload"], "PASS_UNLOADED_DMEM0")
                self.assertEqual(set(row["bycase"]), CASE_IDS)
                for field, count in EXPECTED[model].items():
                    self.assertEqual(row[field], count)
                for field in FIELDS:
                    self.assertEqual(
                        sum(case[field] for case in row["bycase"].values()),
                        row[field]
                    )
                    self.assertGreaterEqual(row["strict_json"], row[field])
                for case in row["bycase"].values():
                    self.assertEqual(case["n"], 2)
                    for field in FIELDS:
                        self.assertGreaterEqual(case[field], 0)
                        self.assertLessEqual(case[field], case["strict_json"])
                    self.assertLessEqual(case["exact"], case["strict_json"])
                self.assertEqual(sum(case["n"] for case in row["bycase"].values()),
                                 row["n"])

    def test_explicit_negative_gates_and_v2_noncomparable(self):
        d = self.data
        self.assertIn("not GOLD", d["scope"])
        self.assertTrue(any("not a clean causal" in v for v in d["limits"]))
        self.assertTrue(any("not device E2E" in v for v in d["limits"]))
        self.assertIn("FREE_FORM_SNAKE_CASE", d["cause_contract"])
        self.assertEqual(d["models"]["gpt-oss:120b"]["bycase"]
                         ["acho_parity_visual_voice"]["strict_json"], 0)


if __name__ == "__main__":
    unittest.main()
