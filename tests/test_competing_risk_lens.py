"""G0 synthetic-only verification; zero model, host-effect or GPU calls."""
from fractions import Fraction
import unittest

from meta_harness.competing_risk_lens import (
    descriptive_cif, wrong_one_minus_km_for_comparison, cohen_kappa_binary,
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


if __name__ == "__main__":
    unittest.main()
