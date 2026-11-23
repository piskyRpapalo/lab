"""TRAIN-03 C2C-0 semantic pilot evidence replay, NOT KV performance certification."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "big-models-20261123"
RECEIPT = ROOT / "c2c0-semantic.json"


class BigModelsSemanticCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = RECEIPT.read_text(encoding="utf-8")
        cls.data = json.loads(cls.raw)

    def test_four_arms_pinned_and_compared_honestly(self):
        d = self.data
        self.assertEqual(d["schema"], "hexelion.train03.c2c0-semantic-observations/1")
        self.assertEqual((d["cases"], d["repetitions"]), (6, 1))
        self.assertFalse(d["gold"])
        self.assertEqual(d["run_state"], "PASS_DEV_COMPLETE")
        self.assertEqual(set(d["arms"]), {"source", "receiver_baseline",
                                         "receiver_verified_frame", "receiver_forged_frame"})
        for x in d["arms"].values():
            self.assertEqual(x["n"], 6)
            self.assertLessEqual(x["exact"], x["strict_json"])
            self.assertLessEqual(x["strict_json"], x["n"])
        self.assertEqual([d["arms"][arm]["exact"] for arm in
                          ("source", "receiver_baseline", "receiver_verified_frame",
                           "receiver_forged_frame")], [6, 3, 5, 3])

    def test_oracle_answer_leakage_is_explicit(self):
        d = self.data
        relay = d["mechanism"]
        self.assertTrue(relay["includes_source_answer"])
        self.assertTrue(relay["includes_source_state_and_cause"])
        self.assertTrue(relay["missing_answer_free_ablation"])
        for forbidden_claim in ("neural_kv_cache", "trained_fuser", "interhost_transport"):
            self.assertFalse(relay[forbidden_claim])
        self.assertFalse(d["gold"])
        self.assertIn("ANSWER_LEAKAGE_IN_VERIFIED_FRAME", d["limits"])
        self.assertIn("NO_DATA(independent_blind_gold)", d["limits"])

    def test_no_tool_effects_or_weights_modified(self):
        a = self.data["authorizations"]
        self.assertIs(a["dispatch_authorized"], False)
        for key in ("real_tools", "kv_tensors_transferred", "real_grants",
                    "active_lora_rotations"):
            self.assertEqual(a[key], 0)
        self.assertFalse(a["training"])
        self.assertEqual(set(self.data["unload"].values()), {"PASS_UNLOADED_DMEM0"})

    def test_privacy_and_source_digest(self):
        d = self.data
        for key in ("public_summary_sha256", "private_full_sha256",
                    "fixture_sha256", "harness_sha256"):
            value = d[key]
            self.assertEqual(len(value), 64)
            self.assertTrue(all(x in "0123456789abcdef" for x in value))
        for forbidden in ("raw_prompt", "raw_response", "completion_text",
                          "/home/", "100.125.", "100.81.", "access_token", "password"):
            self.assertNotIn(forbidden, self.raw.lower())
        self.assertIn("(c2c0-semantic.json)", (ROOT / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
