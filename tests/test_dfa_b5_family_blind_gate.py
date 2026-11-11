"""DFA-B5 refuses same-family judges and never certifies declared alternative models."""
import importlib.util
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / "bin" / "dfa_b5_family_blind_gate.py"
spec = importlib.util.spec_from_file_location("dfa_b5", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def pair(judge_family="gemma", n=60, held_out=True):
    return {"schema": m.SCHEMA,
            "manipulator": {"model": "qwen3:1.7b", "family": "qwen"},
            "judge": {"model": "gemma_candidate", "family": judge_family},
            "cases_per_class": n, "held_out": held_out}


class TestDfaB5PairGate(unittest.TestCase):
    def test_qwen_judge_denied(self):
        self.assertEqual(m.assess(pair("qwen"))["state"], "DENY")

    def test_gemma_candidate_nodata(self):
        r = m.assess(pair("gemma"))
        self.assertEqual(r["state"], "NO_DATA")
        self.assertTrue(r["model_presence"].startswith("NO_DATA"))

    def test_59_per_class_denied(self):
        self.assertEqual(m.assess(pair(n=59))["cause"], "insufficient_declared_cases_per_class")

    def test_exactly_60_not_certified(self):
        self.assertEqual(m.assess(pair(n=60))["state"], "NO_DATA")

    def test_no_heldout_denied(self):
        self.assertEqual(m.assess(pair(held_out=False))["state"], "DENY")

    def test_same_model_denied(self):
        p = pair()
        p["judge"] = dict(p["manipulator"])
        self.assertEqual(m.assess(p)["cause"], "judge_and_manipulator_same_model")

    def test_bool_not_class_count(self):
        with self.assertRaises(ValueError):
            m.assess(pair(n=True))

    def test_negative_case_count(self):
        with self.assertRaises(ValueError):
            m.assess(pair(n=-1))

    def test_extra_field_denied(self):
        p = pair()
        p["override"] = True
        with self.assertRaises(ValueError):
            m.assess(p)

    def test_no_private_name_in_output(self):
        p = pair()
        p["judge"]["model"] = "private_candidate"
        self.assertNotIn("private_candidate", str(m.assess(p)))

    def test_model_path_rejected(self):
        p = pair()
        p["judge"]["model"] = "/private/path"
        with self.assertRaises(ValueError):
            m.assess(p)

    def test_family_path_rejected(self):
        p = pair()
        p["judge"]["family"] = "/private"
        with self.assertRaises(ValueError):
            m.assess(p)

    def test_unknown_string_holdout_rejected(self):
        with self.assertRaises(ValueError):
            m.assess(pair(held_out="yes"))

    def test_no_auto_model_selection(self):
        self.assertTrue(m.assess(pair())["judge_selection"].startswith("NO_DATA"))

    def test_no_consent_claim(self):
        self.assertTrue(m.assess(pair())["consent"].startswith("NO_DATA"))

    def test_deterministic(self):
        self.assertEqual(m.assess(pair()), m.assess(pair()))


if __name__ == "__main__":
    unittest.main()
