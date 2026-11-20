"""Deterministic checks for the published synthetic context-fusion card."""
import importlib.util
import math
import random
import sys
import unittest
from dataclasses import replace
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "benchmarks" / "context-fusion-20261120" / "context_fusion_bench.py"
SPEC = importlib.util.spec_from_file_location("context_fusion_bench", SCRIPT)
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class ContextFusionBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.c = mod.case(5, random.Random(42))

    def test_orthogonal_calibration_on_heldout_anchors(self):
        t = mod.angle_fit(self.c[3][:4])
        self.assertTrue(mod.math_judge(t, self.c[3][4:]))
        self.assertAlmostEqual(
            mod.cosine(mod.concept(self.c[1].concept),
                       mod.rotate(self.c[1].vector, t)), 1, places=10)

    def test_missing_evidence_is_not_invented(self):
        self.assertEqual(mod.judge_case(self.c, "short-only"), "missing_second_source")

    def test_correct_fusion(self):
        self.assertEqual(mod.judge_case(self.c, "aligned"), "correct")

    def test_anchor_poisoning_detected(self):
        self.assertEqual(mod.judge_case(self.c, "aligned", "poisoned-anchors"), "refused_alignment")

    def test_anisotropic_geometry_detected(self):
        self.assertEqual(mod.judge_case(self.c, "aligned", "anisotropic-space"), "refused_alignment")

    def test_revocation_scope_freshness_and_source_scrub(self):
        for attack in ("revoked","stale","wrong-generation","wrong-scope",
                       "missing-witness","tampered-bytes"):
            with self.subTest(attack=attack):
                self.assertEqual(mod.judge_case(self.c, "aligned", attack), "refused_source")

    def test_sha_is_not_grant(self):
        e = self.c[1]
        self.assertTrue(mod.source_judge(e))
        self.assertFalse(mod.source_judge(replace(e, witness=False)))
        self.assertFalse(mod.source_judge(replace(e, permitted=False)))
        self.assertFalse(mod.source_judge(replace(e, sha256="0"*64)))

    def test_missing_anchors_rejected(self):
        with self.assertRaisesRegex(ValueError, "insufficient_anchors"):
            mod.angle_fit(self.c[3][:2])

    def test_degenerate_alignment_rejected(self):
        with self.assertRaisesRegex(ValueError, "ambiguous_alignment"):
            mod.angle_fit([((1.,0.),(0.,1.)),((1.,0.),(0.,-1.)),((1.,0.),(0.,0.))])

    def test_ambiguous_vector_match_rejected(self):
        a=mod.Evidence.make(1,"a",(1.,0.))
        b=mod.Evidence.make(2,"b",(1.,0.))
        self.assertIsNone(mod.retrieve((1.,0.),[a,b]))

    def test_replay_is_deterministic(self):
        self.assertEqual(mod.run(),mod.run())

    def test_denominators_and_fail_closed(self):
        r=mod.run()
        self.assertEqual(r["cases"],64)
        self.assertEqual(r["results"]["aligned_gated"],{"correct":64})
        self.assertEqual(r["results"]["short_only"],{"missing_second_source":64})
        self.assertEqual(r["results"]["poisoned_anchors"],{"refused_alignment":64})
        self.assertEqual(r["results"]["anisotropic_space"],{"refused_alignment":64})
        for k,counts in r["results"].items():
            self.assertEqual(sum(counts.values()),64,k)
        self.assertFalse(r["promotion_authorized"])
        self.assertFalse(r["model_inference"])

    def test_invalid_budget_rejected(self):
        with self.assertRaisesRegex(ValueError,"case_count_out_of_bounds"):
            mod.run(count=0)
        with self.assertRaisesRegex(ValueError,"case_count_out_of_bounds"):
            mod.run(count=10001)

    def test_hard_negative_for_wrong_rotation(self):
        theta=mod.angle_fit(self.c[3][:4])
        self.assertFalse(mod.math_judge(theta+math.pi/2, self.c[3][4:]))


if __name__ == "__main__":
    unittest.main()
