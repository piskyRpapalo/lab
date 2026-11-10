"""DFA-06 deterministic, purely synthetic envelope acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "bin" / "dfa06_evidence_bundle.py"
spec = importlib.util.spec_from_file_location("dfa06", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def payload():
    return {"request_id": "synthetic_01", "observed_at": "2026-11-10T21:00:00Z",
            "artifacts": [{"id": "fixture_01", "sha256": "a" * 64, "state": "MEASURED"},
                          {"id": "fixture_02", "sha256": "b" * 64,
                           "state": "NO_DATA", "cause": "unverified_receiver"}]}


class TestDFA06Evidence(unittest.TestCase):
    def test_roundtrip(self):
        self.assertEqual(m.verify(m.build(payload()))["state"], "VERIFIED_BYTES")

    def test_determinism(self):
        self.assertEqual(m.encode(m.build(payload())), m.encode(m.build(payload())))

    def test_canonical_order(self):
        p = payload()
        p2 = dict(reversed(list(p.items())))
        self.assertEqual(m.encode(m.build(p)), m.encode(m.build(p2)))

    def test_tamper_detected(self):
        e = m.build(payload())
        e["payload"]["artifacts"][0]["sha256"] = "c" * 64
        self.assertEqual(m.verify(e)["cause"], "payload_digest_mismatch")

    def test_missing_digest_rejected(self):
        p = payload()
        del p["artifacts"][0]["sha256"]
        with self.assertRaises(ValueError):
            m.build(p)

    def test_duplicate_id_rejected(self):
        p = payload()
        p["artifacts"][1]["id"] = p["artifacts"][0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            m.build(p)

    def test_path_rejected(self):
        p = payload()
        p["artifacts"][0]["id"] = "/private/secret"
        with self.assertRaises(ValueError):
            m.build(p)

    def test_extra_field_rejected(self):
        p = payload()
        p["artifacts"][0]["author"] = "hidden"
        with self.assertRaises(ValueError):
            m.build(p)

    def test_extra_envelope_field_rejected(self):
        e = m.build(payload())
        e["identity"] = "hidden"
        self.assertEqual(m.verify(e)["state"], "FAIL")

    def test_bad_datetime_rejected(self):
        p = payload()
        p["observed_at"] = "2026-13-40T22:00:00Z"
        with self.assertRaises(ValueError):
            m.build(p)

    def test_offset_date_rejected(self):
        p = payload()
        p["observed_at"] = "2026-11-10T22:00:00+00:00"
        with self.assertRaises(ValueError):
            m.build(p)

    def test_no_data_requires_cause(self):
        p = payload()
        p["artifacts"][1].pop("cause")
        with self.assertRaises(ValueError):
            m.build(p)

    def test_measured_has_no_cause(self):
        p = payload()
        p["artifacts"][0]["cause"] = "because"
        with self.assertRaises(ValueError):
            m.build(p)

    def test_no_data_cause_scrub(self):
        p = payload()
        p["artifacts"][1]["cause"] = "bad: /private/path"
        with self.assertRaises(ValueError):
            m.build(p)

    def test_max_artifacts_rejected(self):
        p = payload()
        p["artifacts"] = [{"id": str(i), "sha256": "a" * 64, "state": "MEASURED"} for i in range(17)]
        with self.assertRaises(ValueError):
            m.build(p)

    def test_signature_never_claimed(self):
        result = m.verify(m.build(payload()))
        self.assertTrue(result["signature_attestation"].startswith("NO_DATA"))

    def test_source_proof_never_claimed(self):
        result = m.verify(m.build(payload()))
        self.assertTrue(result["source_attestation"].startswith("NO_DATA"))

    def test_byte_ceiling(self):
        e = m.build(payload())
        self.assertLess(len(m.encode(e)), 16384)

    def test_empty_artifacts_rejected(self):
        p = payload()
        p["artifacts"] = []
        with self.assertRaises(ValueError):
            m.build(p)

    def test_bad_type(self):
        self.assertEqual(m.verify(None)["state"], "FAIL")


if __name__ == "__main__":
    unittest.main()
