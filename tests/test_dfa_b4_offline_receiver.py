"""DFA-B4 bounded local measurement, no assertion of network delivery."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

BINDIR = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BINDIR))
spec = importlib.util.spec_from_file_location("dfa_b4", BINDIR / "dfa_b4_offline_receiver.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def manifest():
    return {"request_id": "synthetic_01", "observed_at": "2026-11-10T21:00:00Z",
            "artifacts": [{"id": "fixture_01", "sha256": "a" * 64, "state": "MEASURED"}]}


class Clock:
    def __init__(self):
        self.v = 0

    def __call__(self):
        self.v += 1_000_000
        return self.v


class TestDfaB4OfflineReceiver(unittest.TestCase):
    def test_round_trip(self):
        self.assertEqual(m.single(manifest())["state"], "VERIFIED_BYTES")

    def test_measured_positive_bytes(self):
        self.assertGreater(m.single(manifest())["package_bytes"], 0)

    def test_fake_clock_one_ms(self):
        self.assertEqual(m.single(manifest(), clock=Clock())["elapsed_ns"], 1_000_000)

    def test_repeated_runs(self):
        self.assertEqual(m.measure(manifest(), trials=3, clock=Clock())["verified_bytes"], 3)

    def test_p50_p90(self):
        r = m.measure(manifest(), trials=5, clock=Clock())
        self.assertEqual(r["latency_ms"]["p50"], 1.0)
        self.assertEqual(r["latency_ms"]["p90"], 1.0)

    def test_explicit_offline_scope(self):
        r = m.measure(manifest(), clock=Clock())
        self.assertTrue(r["threshold_evaluation"].startswith("NO_DATA"))
        self.assertTrue(r["source_attestation"].startswith("NO_DATA"))

    def test_tamper_rejected(self):
        def tamper(pkg):
            pkg["payload"]["request_id"] = "altered"
        self.assertEqual(m.single(manifest(), mutate=tamper)["state"], "FAIL")

    def test_tampered_source_digest_rejected(self):
        def tamper(pkg):
            pkg["payload"]["artifacts"][0]["sha256"] = "b" * 64
        self.assertEqual(m.single(manifest(), mutate=tamper)["state"], "FAIL")

    def test_no_time_travel(self):
        class Back:
            def __init__(self):
                self.x = 10
            def __call__(self):
                self.x -= 1
                return self.x
        with self.assertRaises(ValueError):
            m.single(manifest(), clock=Back())

    def test_zero_trials(self):
        with self.assertRaises(ValueError):
            m.measure(manifest(), 0)

    def test_too_many_trials(self):
        with self.assertRaises(ValueError):
            m.measure(manifest(), 101)

    def test_bool_trials_rejected(self):
        with self.assertRaises(ValueError):
            m.measure(manifest(), True)

    def test_invalid_metadata_rejected(self):
        p = manifest()
        p["artifacts"][0]["id"] = "/private/data"
        with self.assertRaises(ValueError):
            m.measure(p)

    def test_no_raw_input_in_summary(self):
        p = manifest()
        p["request_id"] = "private_pseudonym"
        self.assertNotIn("private_pseudonym", json.dumps(m.measure(p, clock=Clock())))

    def test_byte_ceiling_inherited(self):
        r = m.measure(manifest(), clock=Clock())
        self.assertLess(r["package_bytes"], 16384)

    def test_no_signature_claim(self):
        r = m.measure(manifest(), clock=Clock())
        self.assertTrue(r["signature_attestation"].startswith("NO_DATA"))


if __name__ == "__main__":
    unittest.main()
