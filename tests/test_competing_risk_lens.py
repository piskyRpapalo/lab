"""G0 synthetic-only verification; zero model, host-effect or GPU calls."""
from fractions import Fraction
import unittest

from meta_harness.competing_risk_lens import (
    descriptive_cif, wrong_one_minus_km_for_comparison, cohen_kappa_binary,
    preflight_three_arm_design,
)


def sample():
    groups = (
        ("COMPROMISED", 1, 10),
        ("DEGRADED", 1, 20),
        ("COMPROMISED", 2, 14),
        ("CENSORED", 2, 56),
    )
    return [
        {"trajectory_id": f"{state}-{turn}-{i}", "turn": turn,
         "state": state, "stratum": "hybrid"}
        for state, turn, n in groups for i in range(n)
    ]


class CompetingRiskLensTest(unittest.TestCase):
    def test_compromised_cif(self):
        self.assertEqual(
            descriptive_cif(sample())["cif"]["COMPROMISED"],
            Fraction(6, 25),
        )

    def test_naive_1km_bias_is_explicit(self):
        estimate = descriptive_cif(sample())["cif"]["COMPROMISED"]
        wrong = wrong_one_minus_km_for_comparison(sample(), "COMPROMISED")
        self.assertEqual(wrong, Fraction(7, 25))
        self.assertEqual(wrong - estimate, Fraction(1, 25))

    def test_over_refusal_is_a_competing_failure(self):
        rows = [
            {"trajectory_id": str(i), "turn": 1,
             "state": "OVER_REFUSED", "stratum": "benign"}
            for i in range(10)
        ]
        result = descriptive_cif(rows)
        self.assertEqual(result["cif"]["OVER_REFUSED"], 1)
        self.assertEqual(result["cif"]["COMPROMISED"], 0)
        self.assertEqual(result["event_free_probability"], 0)

    def test_infra_and_degradation_are_not_censored(self):
        rows = [
            {"trajectory_id": "a", "turn": 1, "state": "DEGRADED",
             "stratum": "hybrid"},
            {"trajectory_id": "b", "turn": 2, "state": "INFRA_BLOCKED",
             "stratum": "hybrid"},
        ]
        result = descriptive_cif(rows)
        self.assertEqual(result["cif"]["DEGRADED"], Fraction(1, 2))
        self.assertEqual(result["cif"]["INFRA_BLOCKED"], Fraction(1, 2))

    def test_censor_does_not_prove_success(self):
        result = descriptive_cif([
            {"trajectory_id": "a", "turn": 12,
             "state": "CENSORED", "stratum": "hybrid"},
        ])
        self.assertEqual(sum(result["cif"].values()), 0)
        self.assertEqual(result["event_free_probability"], 1)
        self.assertEqual(result["evidence"], "CALLER_SUPPLIED_NOT_ATTESTED")

    def test_reject_mixed_cohorts(self):
        rows = sample()
        rows[-1]["stratum"] = "benign"
        with self.assertRaisesRegex(ValueError, "mixed_stratum"):
            descriptive_cif(rows)

    def test_reject_duplicate_trajectories(self):
        rows = sample()
        rows[-1]["trajectory_id"] = rows[0]["trajectory_id"]
        with self.assertRaisesRegex(ValueError, "duplicate_trajectory"):
            descriptive_cif(rows)

    def test_reject_boolean_turn(self):
        rows = sample()
        rows[0]["turn"] = True
        with self.assertRaisesRegex(ValueError, "invalid_trajectory"):
            descriptive_cif(rows)

    def test_kappa_republished_marginals_derived_not_measured(self):
        result = cohen_kappa_binary([[51, 187], [0, 62]])
        self.assertEqual(
            result["observed_agreement"], Fraction(113, 300)
        )
        self.assertEqual(
            result["expected_agreement"], Fraction(383, 1250)
        )
        self.assertTrue(
            Fraction(1, 10) < result["kappa"] < Fraction(11, 100)
        )

    def test_kappa_single_label_undefined(self):
        result = cohen_kappa_binary([[10, 0], [0, 0]])
        self.assertIsNone(result["kappa"])

    def test_kappa_malformed_and_negative_rejected(self):
        for table in ([[1, -1], [0, 1]], [[1, 0]], []):
            with self.subTest(table=table):
                with self.assertRaises(ValueError):
                    cohen_kappa_binary(table)


def paired_design(case="1", repeat=0, stratum="hybrid"):
    common = {
        "case_ref": case.zfill(64), "repeat": repeat,
        "stratum": stratum, "gold_ref": "a" * 64,
        "main_model_ref": "b" * 64,
        "main_protocol_ref": "c" * 64,
        "generation_budget": 128, "seed": 42,
        "host_ref": "d" * 64, "feedback_table_ref": "e" * 64,
    }
    sensor = {
        "sensor_base_ref": "f" * 64,
        "sensor_protocol_ref": "1" * 64,
        "sensor_schema_ref": "2" * 64,
    }
    return [
        dict(common, arm="A",
             sensor_base_ref=None, sensor_weights_ref=None,
             sensor_protocol_ref=None, sensor_schema_ref=None),
        dict(common, arm="B", sensor_weights_ref="3" * 64, **sensor),
        dict(common, arm="C", sensor_weights_ref="4" * 64, **sensor),
    ]


class StudyThreeArmPreflightTest(unittest.TestCase):
    def test_cohort_structure_is_not_gold_or_permission(self):
        result = preflight_three_arm_design(paired_design())
        self.assertEqual(result["state"], "NO_DATA")
        self.assertTrue(result["structure_valid"])
        self.assertEqual(result["paired_groups"], 1)
        self.assertEqual(result["strata"], {"hybrid": 1})
        self.assertEqual(result["authority"], "none")

    def test_nonidentical_sensor_weights_required(self):
        items = paired_design()
        items[2]["sensor_weights_ref"] = items[1]["sensor_weights_ref"]
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "sensor_weights_not_distinct")

    def test_missing_third_arm_rejected(self):
        self.assertEqual(preflight_three_arm_design(paired_design()[:2])["state"],
                         "EVAL_INVALID")

    def test_duplicate_arm_rejected(self):
        items = paired_design()
        items.append(dict(items[2]))
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "duplicate_arm_in_group")

    def test_feedback_table_drift_rejected(self):
        items = paired_design()
        items[2]["feedback_table_ref"] = "9" * 64
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "cohort_pin_drift_feedback_table_ref")

    def test_main_protocol_drift_rejected(self):
        items = paired_design()
        items[1]["main_protocol_ref"] = "9" * 64
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "cohort_pin_drift_main_protocol_ref")

    def test_host_drift_rejected(self):
        items = paired_design()
        items[1]["host_ref"] = "9" * 64
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "cohort_pin_drift_host_ref")

    def test_generation_budget_drift_rejected(self):
        items = paired_design()
        items[1]["generation_budget"] = 256
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "cohort_pin_drift_generation_budget")

    def test_gold_mismatch_is_rejected(self):
        items = paired_design()
        items[1]["gold_ref"] = "9" * 64
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "paired_control_drift")

    def test_seed_mismatch_rejected(self):
        items = paired_design()
        items[1]["seed"] = 43
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "paired_control_drift")

    def test_sensor_schema_mutation_rejected(self):
        items = paired_design()
        items[2]["sensor_schema_ref"] = "9" * 64
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "sensor_contract_drift")

    def test_sensor_base_mutation_rejected(self):
        items = paired_design()
        items[2]["sensor_base_ref"] = "9" * 64
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "sensor_contract_drift")

    def test_baseline_sensor_smuggling_rejected(self):
        items = paired_design()
        items[0]["sensor_weights_ref"] = "9" * 64
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "baseline_has_sensor")

    def test_missing_sensor_pin_rejected(self):
        items = paired_design()
        items[2]["sensor_protocol_ref"] = None
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "missing_sensor_pin")

    def test_missing_human_gold_digest_rejected(self):
        items = paired_design()
        items[1]["gold_ref"] = None
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "invalid_pin")

    def test_separate_strata_and_repeats_are_grouped(self):
        items = (paired_design("1", 0, "benign") +
                 paired_design("1", 1, "benign") +
                 paired_design("2", 0, "hybrid"))
        result = preflight_three_arm_design(items)
        self.assertTrue(result["structure_valid"])
        self.assertEqual(result["paired_groups"], 3)
        self.assertEqual(result["strata"], {"benign": 2, "hybrid": 1})

    def test_boolean_generation_budget_not_accepted(self):
        items = paired_design()
        for row in items:
            row["generation_budget"] = True
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "invalid_pin")

    def test_fourth_arm_rejected(self):
        items = paired_design()
        items[2]["arm"] = "D"
        self.assertEqual(preflight_three_arm_design(items)["cause"],
                         "invalid_pin")

    def test_extra_field_rejected_without_leaking(self):
        items = paired_design()
        items[2]["private_prompt"] = "PRIVATE_TEST_PROMPT"
        result = preflight_three_arm_design(items)
        self.assertEqual(result["state"], "EVAL_INVALID")
        self.assertNotIn("PRIVATE_TEST_PROMPT", str(result))


if __name__ == "__main__":
    unittest.main()
