"""F-08 synthetic offline tests."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location("f08",Path(__file__).resolve().parents[1]/"bin"/"f08_receipt_latency.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def signed(i,at="2026-11-10T01:01:00Z"):
    return {"id":i,"opened_at":"2026-11-10T01:00:00Z","signed_at":at,"receipt_ref":"test-hash"}

class TestF08(unittest.TestCase):
    def test_two_results_equal(self):
        a={"events":[signed("a"),signed("b","2026-11-10T01:03:00Z")]}
        self.assertEqual(m.summary(a),m.summary(a))
        self.assertEqual(m.summary(a)["elapsed_seconds"],{"p50":60.0,"p90":180.0,"p99":180.0})
    def test_empty(self):self.assertEqual(m.summary({"events":[]})["cause"],"NO_DATA: no_signed_pairs")
    def test_pending(self):self.assertEqual(m.summary({"events":[{"id":"x","opened_at":"2026-11-10T01:00:00Z","cause":"human_pending"}]})["pending"],1)
    def test_no_pending_cause(self):
        with self.assertRaises(ValueError):m.summary({"events":[{"id":"x","opened_at":"2026-11-10T01:00:00Z"}]})
    def test_duplicate(self):
        with self.assertRaises(ValueError):m.summary({"events":[signed("x"),signed("x")]})
    def test_negative(self):
        with self.assertRaises(ValueError):m.summary({"events":[signed("x","2026-11-09T01:00:00Z")]})
    def test_missing_ref(self):
        x=signed("x");x.pop("receipt_ref")
        with self.assertRaises(ValueError):m.summary({"events":[x]})
    def test_utc(self):
        x=signed("x");x["opened_at"]="2026-11-10T01:00:00"
        with self.assertRaises(ValueError):m.summary({"events":[x]})
    def test_unknown(self):
        x=signed("x");x["magic"]=1
        with self.assertRaises(ValueError):m.summary({"events":[x]})
    def test_closed_top(self):
        with self.assertRaises(ValueError):m.summary({"events":[],"extra":1})
    def test_scrub(self):
        x=signed("secret_id");x["receipt_ref"]="secret_receipt"
        self.assertNotIn("secret",str(m.summary({"events":[x]})))
    def test_signed_cause_rejected(self):
        x=signed("x");x["cause"]="fake"
        with self.assertRaises(ValueError):m.summary({"events":[x]})
