"""Metadata-only gates for the TRAIN-02 2-v-4 step preregistration.

These tests NEVER run a model or prove a gain. They prevent a proposal from
being relabelled GOLD while blind cases, custody and inference are absent.
"""
import json
from pathlib import Path
import re
import unittest


DOC = Path(__file__).resolve().parents[1] / "benchmarks" / "big-models-20261123" / "train02-2v4-blind-prereg-20261123.json"
HEX = re.compile(r"[0-9a-f]{64}\Z")


class Train02BlindPreregTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card = json.loads(DOC.read_text(encoding="utf-8"))

    def test_closed_scope_and_no_promotion(self):
        m = self.card
        self.assertEqual(m["schema"], "hexelion.train02.blind-2v4-prereg/1")
        self.assertEqual(m["status"], "PREREGISTRATION_ONLY_NO_GOLD_NO_INFERENCE")
        self.assertFalse(m["comparison"]["training_effect_estimable"])
        self.assertTrue(m["inference_protocol"]["inference_only"])
        self.assertFalse(m["inference_protocol"]["gpu_new_training_allowed"])
        self.assertEqual(m["gates"]["promotion"], "HOLD_NOT_AUTHORIZED")
        for gate in ("blind_gold", "base_runtime", "two_step_runtime",
                     "four_step_runtime", "edge_e2e_x2", "physical_audio"):
            self.assertTrue(m["gates"][gate].startswith("NO_DATA("), gate)

    def test_exact_existing_weight_pins(self):
        w = self.card["weights"]
        self.assertEqual(
            w["two_step"]["adapter_sha256"],
            "5cee18e65b817b9cbe49223d32abf7168755e7338e3e7b54a802d181d3888ed0",
        )
        self.assertEqual(
            w["four_step"]["adapter_sha256"],
            "8f867b243ad73405068f3f61e094b41c732437132426a9fa770e3e79f295c950",
        )
        for arm in ("two_step", "four_step"):
            for field in ("adapter_sha256", "merged_sha256"):
                self.assertRegex(w[arm][field], HEX)
            self.assertEqual(w[arm]["status"], "PHYSICAL_TRAINED_UNPROMOTED")
        self.assertTrue(w["base"]["checkpoint_sha256"].startswith("NO_DATA("))

    def test_same_cases_all_arms_and_language_balance(self):
        m = self.card
        ids = [x["id"] for x in m["comparison"]["arms"]]
        self.assertEqual(ids, ["D0_HOST", "D1_BASE", "D2_2STEP", "D2_4STEP"])
        self.assertEqual(m["comparison"]["arms"][0]["kind"], "ORACLE")
        self.assertEqual([x["kind"] for x in m["comparison"]["arms"][1:]],
                         ["MODEL"] * 3)
        self.assertTrue(m["comparison"]["paired_cases"])
        h = m["holdout"]
        families = h["families"]
        self.assertEqual(len(families), 6)
        self.assertEqual(len({x["id"] for x in families}), len(families))
        self.assertTrue(all(x["cases"] == x["es"] + x["pt"] == 8 for x in families))
        self.assertTrue(all(x["es"] == x["pt"] == 4 for x in families))
        self.assertEqual(h["total_unique_cases"], sum(x["cases"] for x in families))
        self.assertEqual(h["es_cases"], sum(x["es"] for x in families))
        self.assertEqual(h["pt_cases"], sum(x["pt"] for x in families))
        self.assertEqual(h["expected_model_generations"],
                         h["total_unique_cases"] * h["repetitions_per_arm"] * 3)
        self.assertEqual(h["expected_host_oracle_checks"],
                         h["total_unique_cases"] * h["repetitions_per_arm"])

    def test_holdout_and_runtime_are_fail_closed(self):
        m = self.card
        h = m["holdout"]
        self.assertTrue(h["status"].startswith("NO_DATA("))
        for key in ("sealed_case_root_sha256", "train_overlap_check", "case_order_hash"):
            self.assertTrue(h[key].startswith("NO_DATA("), key)
        for key in ("chat_template_sha256", "grader_schema_sha256", "gpu_lease"):
            self.assertTrue(m["inference_protocol"][key].startswith("NO_DATA("), key)
        self.assertIn("selection", m["comparison"]["known_confound"])
        self.assertEqual(m["inference_protocol"]["generation_settings"]["temperature"], 0)
        self.assertFalse(m["inference_protocol"]["generation_settings"]["do_sample"])
        self.assertEqual(m["inference_protocol"]["generation_settings"]["repeats"], 2)
        self.assertGreaterEqual(len(m["inference_protocol"]["stop_conditions"]), 5)

    def test_independent_judge_security_and_uncertainty(self):
        m = self.card
        metrics = m["measurement"]
        hard = set(metrics["hard_veto_metrics"])
        for key in ("false_live_count", "false_authority_count",
                    "revoked_grant_allowed_count", "privileged_tool_effect_count"):
            self.assertIn(key, hard)
        self.assertIn("complete", metrics["primary"].lower())
        self.assertIn("95%", metrics["paired_comparison"])
        self.assertIn("lower bound", metrics["success_gate"])
        self.assertIn("source-family", m["holdout"]["contamination_policy"].lower())
        self.assertIn("meta_harness/improvement", m["comparison"]["reuse"])

    def test_no_raw_material_bundled(self):
        m = self.card
        self.assertIn("OWNER_LOCAL_ONLY", m["holdout"]["raw_inputs_policy"])
        forbidden_keys = {"prompt", "prompt_text", "raw_prompt", "completion",
                          "raw_output", "answer_key", "messages", "private_path"}
        def walk(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden_keys.intersection(value.keys()))
                for v in value.values():
                    walk(v)
            elif isinstance(value, list):
                for v in value:
                    walk(v)
        walk(m)


if __name__ == "__main__":
    unittest.main()
