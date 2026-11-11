"""DFA-B2: scorer does not fabricate human gold or promote abstentions to passes."""
import importlib.util
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / "bin" / "dfa_b2_clarity_labels.py"
spec = importlib.util.spec_from_file_location("dfa_b2", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    return {"schema": m.SCHEMA, "reference_provenance": "SYNTHETIC",
            "cases": [{"id": "clause_01", "reference": "SI", "prediction": "SI"},
                      {"id": "clause_02", "reference": "NO", "prediction": "NO_DATA",
                       "cause": "model_abstained"},
                      {"id": "clause_03", "reference": "CUANDO", "prediction": "NO"}]}


class TestDfaB2Clarity(unittest.TestCase):
    def test_denominator_includes_abstentions(self):
        r = m.score(fixture())
        self.assertEqual(r["agreement_fraction"], [1, 3])

    def test_coverage_excludes_abstentions(self):
        r = m.score(fixture())
        self.assertEqual(r["non_abstention_fraction"], [2, 3])

    def test_synthetic_not_human_proof(self):
        r = m.score(fixture())
        self.assertEqual(r["state"], "SYNTHETIC_SCORE")
        self.assertTrue(r["threshold_evaluation"].startswith("NO_DATA"))

    def test_unverified_human_is_nodata(self):
        p = fixture()
        p["reference_provenance"] = "HUMAN_UNVERIFIED"
        self.assertEqual(m.score(p)["state"], "NO_DATA")

    def test_rejected_duplicate(self):
        p = fixture()
        p["cases"][1]["id"] = p["cases"][0]["id"]
        with self.assertRaises(ValueError):
            m.score(p)

    def test_rejected_unknown_label(self):
        p = fixture()
        p["cases"][0]["prediction"] = "YES"
        with self.assertRaises(ValueError):
            m.score(p)

    def test_rejected_unknown_reference(self):
        p = fixture()
        p["cases"][0]["reference"] = "YES"
        with self.assertRaises(ValueError):
            m.score(p)

    def test_no_data_requires_cause(self):
        p = fixture()
        p["cases"][1].pop("cause")
        with self.assertRaises(ValueError):
            m.score(p)

    def test_no_data_requires_scrubbed_cause(self):
        p = fixture()
        p["cases"][1]["cause"] = "/private/hint"
        with self.assertRaises(ValueError):
            m.score(p)

    def test_no_secret_in_public_result(self):
        p = fixture()
        p["cases"][0]["id"] = "secret_case"
        self.assertNotIn("secret_case", str(m.score(p)))

    def test_rejected_extra_field(self):
        p = fixture()
        p["cases"][0]["raw_clause"] = "private"
        with self.assertRaises(ValueError):
            m.score(p)

    def test_rejected_causes_for_measured_labels(self):
        p = fixture()
        p["cases"][0]["cause"] = "unused"
        with self.assertRaises(ValueError):
            m.score(p)

    def test_rejected_empty(self):
        p = fixture()
        p["cases"] = []
        with self.assertRaises(ValueError):
            m.score(p)

    def test_rejected_more_than_1000(self):
        p = fixture()
        p["cases"] = [{"id": "i" + str(i), "reference": "NO", "prediction": "NO"}
                      for i in range(1001)]
        with self.assertRaises(ValueError):
            m.score(p)

    def test_deterministic(self):
        self.assertEqual(m.score(fixture()), m.score(fixture()))


if __name__ == "__main__":
    unittest.main()
