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


def paired_case_clusters():
    """Four synthetic independent case fixtures, each with two paired repeats."""
    rows = []
    for index in range(1, 5):
        for repeat in (0, 1):
            for arm in ("A", "B", "C"):
                failure = index <= 2 and arm in ("A", "B")
                rows.append({
                    "case_ref": format(index, "064x"),
                    "repeat": repeat, "arm": arm, "stratum": "hybrid",
                    "turn": 2 if failure else 5,
                    "state": "COMPROMISED" if failure else "CENSORED",
                    "horizon": 5,
                })
    return rows


class PairedClusterSpreadTest(unittest.TestCase):
    """These tests describe resampling mechanics, NOT CI coverage."""

    def _score(self, rows=None, **overrides):
        from meta_harness.competing_risk_lens import paired_cluster_spread
        config = dict(
            target="COMPROMISED", reference_arm="A",
            treatment_arm="C", seed=42, draws=48,
        )
        config.update(overrides)
        return paired_cluster_spread(
            paired_case_clusters() if rows is None else rows, **config
        )

    def test_paired_cif_difference_is_exact(self):
        result = self._score()
        self.assertEqual(result["point_difference"], Fraction(-1, 2))
        self.assertEqual(result["case_clusters"], 4)
        self.assertEqual(result["repeats_per_case"], 2)
        self.assertEqual(result["sampled_unit"],
                         "entire_case_A_B_C_with_repeats")

    def test_unchanged_A_B_pairs_have_zero_spread(self):
        result = self._score(treatment_arm="B")
        self.assertEqual(result["point_difference"], 0)
        self.assertEqual(result["resampling_p025"], 0)
        self.assertEqual(result["resampling_p975"], 0)

    def test_resamples_are_order_invariant(self):
        rows = paired_case_clusters()
        self.assertEqual(self._score(rows), self._score(list(reversed(rows))))

    def test_seed_is_reproducible(self):
        self.assertEqual(self._score(), self._score())

    def test_not_a_confidence_interval_or_attested_effect(self):
        result = self._score()
        self.assertEqual(result["state"], "DESCRIPTIVE_ONLY")
        self.assertEqual(result["authority"], "none")
        self.assertEqual(result["evidence"], "CALLER_SUPPLIED_NOT_ATTESTED")
        self.assertTrue(result["coverage"].startswith("NO_DATA("))

    def test_positive_nonzero_variability_is_bounded(self):
        result = self._score()
        self.assertTrue(Fraction(-1) <= result["resampling_p025"] <= 0)
        self.assertTrue(Fraction(-1) <= result["resampling_p975"] <= 0)
        self.assertLessEqual(result["resampling_p025"],
                             result["resampling_p975"])

    def test_reject_mixed_strata(self):
        rows = paired_case_clusters()
        rows[0]["stratum"] = "benign"
        with self.assertRaisesRegex(ValueError, "mixed_stratum_or_horizon"):
            self._score(rows)

    def test_reject_incomplete_arm(self):
        rows = paired_case_clusters()
        rows.pop(3)
        with self.assertRaisesRegex(ValueError, "incomplete_three_arm_case"):
            self._score(rows)

    def test_reject_unequal_repeat_sets(self):
        rows = [row for row in paired_case_clusters()
                if not (row["case_ref"] == format(1, "064x")
                        and row["repeat"] == 1)]
        with self.assertRaisesRegex(ValueError, "unequal_repeat_sets"):
            self._score(rows)

    def test_reject_duplicate_case_repeat_arm(self):
        rows = paired_case_clusters()
        rows.append(dict(rows[0]))
        with self.assertRaisesRegex(ValueError, "duplicate_case_repeat_arm"):
            self._score(rows)

    def test_reject_two_case_clusters_for_spread(self):
        rows = [row for row in paired_case_clusters()
                if row["case_ref"] in
                (format(1, "064x"), format(2, "064x"))]
        with self.assertRaisesRegex(ValueError, "insufficient_case_clusters"):
            self._score(rows)

    def test_reject_early_censor_with_no_reason_field(self):
        rows = paired_case_clusters()
        row = next(row for row in rows if row["state"] == "CENSORED")
        row["turn"] = 3
        with self.assertRaisesRegex(ValueError,
                                    "early_censor_reason_not_represented"):
            self._score(rows)

    def test_reject_observation_beyond_horizon(self):
        rows = paired_case_clusters()
        rows[0]["turn"] = 13
        with self.assertRaisesRegex(ValueError, "invalid_row_value"):
            self._score(rows)

    def test_reject_boolean_and_excessive_draw_budget(self):
        for value in (True, 1, 513):
            with self.subTest(draws=value):
                with self.assertRaisesRegex(ValueError,
                                            "invalid_resampling_budget"):
                    self._score(draws=value)

    def test_reject_unbound_target_and_identical_arms(self):
        with self.assertRaisesRegex(ValueError, "invalid_contrast"):
            self._score(target="GOOD")
        with self.assertRaisesRegex(ValueError, "invalid_contrast"):
            self._score(treatment_arm="A")

    def test_reject_untrusted_extra_field_without_echo(self):
        rows = paired_case_clusters()
        rows[0]["secret"] = "DO_NOT_INCLUDE"
        with self.assertRaisesRegex(ValueError, "invalid_row_shape"):
            self._score(rows)


def _g3_declared_design(terminal=None):
    """Synthetic source plan aligned to the preexisting paired_case_clusters."""
    rows = paired_case_clusters() if terminal is None else terminal
    result = []
    for row in rows:
        arm = row["arm"]
        n = int(row["case_ref"], 16)
        q = lambda value: format(value, "064x")
        result.append({
            "case_ref": row["case_ref"], "repeat": row["repeat"],
            "arm": arm, "stratum": row["stratum"], "gold_ref": q(100+n),
            "main_model_ref": q(700), "main_protocol_ref": q(701),
            "generation_budget": 128, "seed": 10+n,
            "host_ref": q(702), "feedback_table_ref": q(703),
            "sensor_base_ref": None if arm == "A" else q(704),
            "sensor_weights_ref": (
                None if arm == "A" else q(705 if arm == "B" else 706)
            ),
            "sensor_protocol_ref": None if arm == "A" else q(707),
            "sensor_schema_ref": None if arm == "A" else q(708),
        })
    return result


class G3DeclaredLinkTest(unittest.TestCase):
    """Negative controls for structural linkage; not effect attestation."""

    def _link(self, design=None, terminal=None):
        from meta_harness.competing_risk_lens import (
            link_declared_design_to_outcomes,
        )
        if terminal is None:
            terminal = paired_case_clusters()
        if design is None:
            design = _g3_declared_design()
        return link_declared_design_to_outcomes(design, terminal)

    def test_matching_declared_rows_remain_nodata(self):
        r = self._link()
        self.assertEqual(r["state"], "NO_DATA")
        self.assertEqual(r["matched_records"], 24)
        self.assertFalse(r["study_ready"])
        self.assertEqual(r["authority"], "none")
        self.assertEqual(r["evidence"], "CALLER_SUPPLIED_NOT_ATTESTED")
        self.assertIn("independent_witness_absent", r["host_effect_witness"])
        self.assertEqual(len(r["design_ref"]), 64)
        self.assertEqual(len(r["outcomes_ref"]), 64)

    def test_order_invariant_digests(self):
        design, terminal = _g3_declared_design(), paired_case_clusters()
        self.assertEqual(self._link(design, terminal),
                         self._link(design[::-1], terminal[::-1]))

    def test_different_declared_case_rejected(self):
        terminal = paired_case_clusters()
        terminal[0]["case_ref"] = "f" * 64
        self.assertEqual(self._link(terminal=terminal)["cause"],
                         "declared_terminal_keys_differ")

    def test_missing_terminal_row_rejected(self):
        terminal = paired_case_clusters()[:-1]
        self.assertEqual(self._link(terminal=terminal)["cause"],
                         "outcome_schema_or_count_mismatch")

    def test_duplicate_terminal_arm_key_rejected(self):
        terminal = paired_case_clusters()
        terminal[0] = dict(terminal[1])
        self.assertEqual(self._link(terminal=terminal)["cause"],
                         "duplicate_terminal_key")

    def test_stratum_drift_rejected(self):
        terminal = paired_case_clusters()
        terminal[0]["stratum"] = "benign"
        self.assertEqual(self._link(terminal=terminal)["cause"],
                         "declared_terminal_strata_differ")

    def test_outcome_horizon_invalid_rejected_by_g2(self):
        terminal = paired_case_clusters()
        terminal[0]["horizon"] = 6
        self.assertEqual(self._link(terminal=terminal)["cause"],
                         "g2_terminal_preflight_failed")

    def test_sensor_schema_drift_rejected_by_g1(self):
        design = _g3_declared_design()
        design[2]["sensor_schema_ref"] = "9" * 64
        self.assertEqual(self._link(design=design)["cause"],
                         "declared_design_invalid")

    def test_feedback_projection_drift_rejected_by_g1(self):
        design = _g3_declared_design()
        design[2]["feedback_table_ref"] = "9" * 64
        self.assertEqual(self._link(design=design)["cause"],
                         "declared_design_invalid")

    def test_malicious_free_text_field_denied_without_echo(self):
        terminal = paired_case_clusters()
        terminal[0]["prompt"] = "DO_NOT_ECHO_SYNTHETIC_CANARY"
        r = self._link(terminal=terminal)
        self.assertEqual(r["state"], "EVAL_INVALID")
        self.assertNotIn("DO_NOT_ECHO_SYNTHETIC_CANARY", str(r))

    def test_swapped_unverified_model_output_never_certified(self):
        # A falsified record can swap A/C effects while keeping row keys.
        # Structural validity is not authenticity. Successful linkage MUST
        # still remain NO_DATA and study_ready=False.
        terminal = paired_case_clusters()
        a = next(r for r in terminal if r["arm"] == "A" and
                 r["case_ref"] == format(1,"064x") and r["repeat"] == 0)
        c = next(r for r in terminal if r["arm"] == "C" and
                 r["case_ref"] == format(1,"064x") and r["repeat"] == 0)
        a["turn"], c["turn"] = c["turn"], a["turn"]
        a["state"], c["state"] = c["state"], a["state"]
        r = self._link(terminal=terminal)
        self.assertEqual(r["state"], "NO_DATA")
        self.assertFalse(r["study_ready"])


if __name__ == "__main__":
    unittest.main()
