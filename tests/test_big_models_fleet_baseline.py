"""Replay of TRAIN-03 two-host same-checkpoint DEV observations, not a model oracle."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "big-models-20261123"
SOURCE = ROOT / "fleet-heterogeneous.json"


class Train03FleetBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = SOURCE.read_text(encoding="utf8")
        cls.data = json.loads(cls.raw)

    def test_exact_model_identity_and_host_count(self):
        d = self.data
        self.assertEqual(d["schema"], "hexelion.train03.fleet-comparative/1")
        self.assertEqual(len(d["hosts"]), 2)
        self.assertEqual(d["repetitions"], 2)
        self.assertEqual(set(d["cases"]), {"math_spanish", "sensor_missing_pt", "revocation_es"})
        self.assertTrue(d["controls"]["same_model_digest"])
        self.assertTrue(d["controls"]["same_synthetic_fixture"])
        self.assertFalse(d["controls"]["same_runtime_version"])
        self.assertFalse(d["controls"]["native_orchestrated_routing"])
        self.assertFalse(d["controls"]["blind_gold"])
        for h in d["hosts"]:
            self.assertEqual(h["arch"], "aarch64")
            self.assertEqual(h["state"], "DEV_COMPLETE")
            self.assertEqual(h["samples"], 6)
            self.assertEqual(h["strict_json"], 6)
            self.assertLessEqual(h["exact"], h["strict_json"])
            self.assertEqual(sum(x["n"] for x in h["case_metrics"].values()), 6)
            self.assertEqual(sum(x["exact"] for x in h["case_metrics"].values()), h["exact"])
            self.assertEqual(h["unload"], "PASS_NO_RESIDENT_MODELS")

    def test_no_causal_hardware_or_promotion_claim(self):
        d = self.data
        self.assertIn("NO_CAUSAL_HARDWARE_RANKING_RUNTIME_VERSION_CONFOUNDED",
                      d["conclusions"])
        self.assertEqual({h["label"]:h["exact"] for h in d["hosts"]},
                         {"fragua":4, "vigia":0})
        self.assertEqual({h["label"]:h["runtime_version"] for h in d["hosts"]},
                         {"fragua":"0.24.0", "vigia":"0.40.13"})
        self.assertFalse(d["effects"]["training"])
        for key in ("real_tools", "kv_transfers", "real_host_dispatches",
                    "dist_adapters_deployed"):
            self.assertEqual(d["effects"][key], 0)

    def test_provenance_privacy_integrity(self):
        d = self.data
        for digest in [d["fixture_sha256"], d["model"]["digest"]]+[
            h["public_summary_sha256"] for h in d["hosts"]
        ]:
            self.assertEqual(len(digest), 64)
            self.assertTrue(all(c in "0123456789abcdef" for c in digest))
        for term in ("password", "access_token", "/home/", "100.125.",
                     "100.81.", "raw_prompt", "raw_response"):
            self.assertNotIn(term, self.raw.lower())
        self.assertIn("(fleet-heterogeneous.json)",
                      (ROOT/"README.md").read_text(encoding="utf8"))


if __name__ == "__main__":
    unittest.main()
