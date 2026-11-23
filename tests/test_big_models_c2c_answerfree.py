"""Replay TRAIN-03 answer-free C2C-0 negative outcome; no source answers on GitHub."""
import json
from pathlib import Path
import unittest

BASE = Path(__file__).resolve().parents[1] / "benchmarks" / "big-models-20261123"


class Train03AnswerFreeC2C(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (BASE / "c2c0-answerfree.json").read_text(encoding="utf-8")
        cls.x = json.loads(cls.raw)

    def test_all_three_arms_complete_with_two_repeats(self):
        x = self.x
        self.assertEqual(x["schema"], "hexelion.train03.c2c0-answerfree-ablation/1")
        self.assertEqual(x["run_state"], "PASS_DEV_COMPLETE")
        self.assertEqual((x["case_count"], x["repetitions"], x["samples_completed"]),
                         (6, 2, 36))
        self.assertFalse(x["gold"])
        rows = {r["name"]: r for r in x["arms"]}
        self.assertEqual(set(rows), {"baseline", "verified_metadata_answer_free",
                                     "forged_metadata_answer_free"})
        self.assertEqual([(rows[k]["exact"], rows[k]["strict_json"]) for k in
                          ("baseline", "verified_metadata_answer_free",
                           "forged_metadata_answer_free")], [(9, 9), (6, 8), (6, 8)])
        for row in rows.values():
            self.assertEqual(row["n"], 12)
            self.assertLessEqual(row["exact"], row["strict_json"])
            self.assertLessEqual(row["strict_json"], row["n"])
            self.assertGreater(row["median_wall_s"], 0)

    def test_no_answer_or_state_in_transferred_frame(self):
        frame = self.x["frame"]
        for field in ("includes_answer", "includes_tasks", "includes_state",
                      "includes_cause"):
            self.assertFalse(frame[field])
        self.assertTrue(frame["contains_prior_exposed_DEV_witness"])
        self.assertTrue(frame["requires_host_permission_at_use"])
        self.assertEqual(self.x["unload"], "PASS_UNLOADED_DMEM0")
        for field, value in self.x["evidence_boundary"].items():
            self.assertEqual(value, 0, field)
        self.assertIn("NO_DATA(real_C2C1_KV_reuse)", self.x["limits"])

    def test_source_integrity_and_privacy(self):
        for field in ("source_summary_sha256", "private_full_sha256", "runner_sha256",
                      "source_prior_summary_sha256", "source_model_digest",
                      "receiver_digest"):
            digest = self.x[field]
            self.assertEqual(len(digest), 64)
            self.assertTrue(all(c in "0123456789abcdef" for c in digest))
        for forbidden in ("/home/", "password", "access_token", "raw_prompt",
                          "raw_response", "100.81.", "100.125."):
            self.assertNotIn(forbidden, self.raw.lower())
        self.assertIn("(c2c0-answerfree.json)",
                      (BASE / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
