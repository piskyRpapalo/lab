"""TRAIN-02 synthetic DEV readback: prevent false GOLD or promotion claims."""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "benchmarks" / "big-models-20261123" / "train02-2v4-dev-smoke-20261124.json"

class Train02PairedDevReadback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = json.loads(DATA.read_text(encoding="utf-8"))

    def test_evidence_is_dev_not_gold(self):
        d = self.obj
        self.assertEqual(d["status"], "PASS_PHYSICAL_INFERENCE_DEV_ONLY_NOT_GOLD")
        self.assertFalse(d["cases"]["independent_holdout"])
        self.assertFalse(d["interpretation"]["quality_gain_demonstrated"])
        self.assertTrue(d["interpretation"]["unpromoted"])
        self.assertEqual(d["gates"]["promotion"], "HOLD_NOT_AUTHORIZED")
        self.assertTrue(d["gates"]["gold"].startswith("NO_DATA("))

    def test_case_accounting(self):
        d = self.obj
        c = d["cases"]
        self.assertEqual(c["unique"], 6)
        self.assertEqual(c["es"] + c["pt"], 6)
        self.assertEqual(c["repetitions"], 2)
        self.assertEqual(c["model_arms"], 3)
        self.assertEqual(c["generations"], 36)
        self.assertEqual(sum(x["n"] for x in d["metrics"].values()), 36)

    def test_each_arm_strict_and_zero_exact(self):
        for name in ("base", "two_step", "four_step"):
            with self.subTest(arm=name):
                arm = self.obj["metrics"][name]
                self.assertEqual(arm["n"], 12)
                self.assertEqual(arm["strict_json"], 6)
                self.assertEqual(arm["all_fields_exact"], 0)
                self.assertEqual(arm["false_live"], 0)
                self.assertEqual(arm["false_grant"], 0)
                self.assertLess(arm["p50_s"], arm["max_s"])
                self.assertLess(arm["post_arm_gpu_bytes"], 2_000_000_000)

    def test_resource_and_unload_bounds(self):
        w = self.obj["resource_witness"]
        self.assertLess(w["peak_gpu_used_bytes"], 12_000_000_000)
        self.assertLess(w["max_gpu_temp_c"], 64)
        self.assertEqual(w["post_process_gpu_busy_percent"], 0)
        self.assertLess(w["post_process_gpu_used_bytes"], 2_000_000_000)

    def test_pins_are_digest_only(self):
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", v)
                            for v in self.obj["artifact_pin"].values()))
        self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", self.obj["cases"]["case_root_sha256"]))
        self.assertTrue(self.obj["gates"]["edge"].startswith("NO_DATA("))

    def test_scrub_no_private_payloads(self):
        d = self.obj
        raw = DATA.read_text(encoding="utf-8")
        self.assertFalse(any(k in d for k in ("rows", "prompts", "answers", "completions", "private_paths")))
        for s in ("/home/", "100.81.", "100.125.", "Bearer ", "source_excerpt", "private_prompt"):
            self.assertNotIn(s, raw)
        self.assertLess(len(raw.encode("utf-8")), 9000)

    def test_negative_canary_rejects_promotion(self):
        modified = json.loads(json.dumps(self.obj))
        modified["interpretation"]["unpromoted"] = False
        with self.assertRaises(AssertionError):
            self.assertTrue(modified["interpretation"]["unpromoted"])

if __name__ == "__main__":
    unittest.main()
