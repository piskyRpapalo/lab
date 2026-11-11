import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "benchmarks/receipts/20261111-dfa-b5-gemma2-candidate.json"


class TestGemmaCandidateHistoricalReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(DOC.read_text(encoding="utf-8"))

    def test_two_passes_same_fixture(self):
        r = self.record
        self.assertEqual(len(r["passes"]), 2)
        self.assertEqual(len({p["cases_sha256"] for p in r["passes"]}), 1)
        self.assertEqual(r["fixture_sha256"], r["passes"][0]["cases_sha256"])

    def test_red_not_promoted(self):
        self.assertEqual(self.record["pilot_verdict"], "RED_UNCALIBRATED")
        self.assertTrue(self.record["quality_context"]["human_ground_truth"].startswith("NO_DATA"))
        self.assertTrue(self.record["quality_context"]["heldout_sample"].startswith("NO_DATA"))
        self.assertTrue(self.record["quality_context"]["judge_family_independence"].startswith("NO_DATA"))

    def test_denominators_and_abstention_negative(self):
        for p in self.record["passes"]:
            self.assertEqual((p["correct"], p["total"]), (4, 8))
            self.assertEqual(p["malformed_or_error"], 1)
            self.assertEqual(p["class_results"]["FALSE_NO_DATA"], {"correct": 0, "total": 2})
            self.assertEqual(sum(row["total"] for row in p["class_results"].values()), 8)
            self.assertEqual(sum(row["correct"] for row in p["class_results"].values()), 4)

    def test_source_digests_and_separate_gpu_smoke(self):
        for p in self.record["passes"]:
            self.assertRegex(p["receipt_sha256_local"], r"^[0-9a-f]{64}$")
        self.assertRegex(self.record["fixture_sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("separate", self.record["gpu_smoke_separate"]["causal_scope"])
        self.assertEqual(self.record["gpu_smoke_separate"]["after_unload_resident_models"], 0)

    def test_no_raw_prompts_answers_or_private_host(self):
        s = DOC.read_text(encoding="utf-8")
        self.assertNotIn('"per_case"', s)
        self.assertNotIn('"prompt"', s)
        self.assertNotIn('"response"', s)
        self.assertNotIn("/home/", s)
        self.assertNotIn("127.0.0.1", s)


if __name__ == "__main__":
    unittest.main()
