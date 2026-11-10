"""F6 synthetic economic probes: no financial actions or identity verification."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location("f6",Path(__file__).resolve().parents[1]/"bin"/"f6_economic_probes.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fixture(k,f):return {"kind":k,"facts":f}
class TestF6(unittest.TestCase):
 def test_inflated_reach_denied(self):
  self.assertEqual(m.assess(fixture("reach_inflation",{"claimed_reach":3,"receipt_digests":["a","b"]}))["verdict"],"DENY")
 def test_repeat_receipt_does_not_inflate(self):
  self.assertEqual(m.assess(fixture("reach_inflation",{"claimed_reach":2,"receipt_digests":["same","same"]}))["verdict"],"DENY")
 def test_sufficient_receipts_not_authorized(self):
  self.assertEqual(m.assess(fixture("reach_inflation",{"claimed_reach":2,"receipt_digests":["a","b"]}))["verdict"],"NO_DATA")
 def test_overbudget_denied(self):
  self.assertEqual(m.assess(fixture("budget_overpromise",{"promised_j":11,"available_j":10}))["verdict"],"DENY")
 def test_budget_not_attested(self):
  self.assertEqual(m.assess(fixture("budget_overpromise",{"promised_j":1,"available_j":10}))["verdict"],"NO_DATA")
 def test_non_sovereign_arbitration_denied(self):
  self.assertEqual(m.assess(fixture("arbitration_spoof",{"role":"agent","requests_arbitration":True}))["verdict"],"DENY")
 def test_declared_sovereign_not_enough(self):
  self.assertEqual(m.assess(fixture("arbitration_spoof",{"role":"sovereign","requests_arbitration":True}))["verdict"],"NO_DATA")
 def test_determinism(self):
  x=fixture("budget_overpromise",{"promised_j":11,"available_j":10});self.assertEqual(m.assess(x),m.assess(x))
 def test_no_sensitive_values_output(self):
  s=str(m.assess(fixture("reach_inflation",{"claimed_reach":2,"receipt_digests":["private_1","private_2"]})))
  self.assertNotIn("private",s)
 def test_negative_budget(self):
  with self.assertRaises(ValueError):m.assess(fixture("budget_overpromise",{"promised_j":-1,"available_j":1}))
 def test_float_budget(self):
  with self.assertRaises(ValueError):m.assess(fixture("budget_overpromise",{"promised_j":1.2,"available_j":2}))
 def test_unknown_extra_field(self):
  with self.assertRaises(ValueError):m.assess(fixture("budget_overpromise",{"promised_j":1,"available_j":2,"override":True}))
 def test_no_magic_role(self):
  with self.assertRaises(ValueError):m.assess(fixture("arbitration_spoof",{"role":"agent","requests_arbitration":"yes"}))
 def test_no_unknown_probe(self):
  with self.assertRaises(ValueError):m.assess(fixture("payment",{}))
