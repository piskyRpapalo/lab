"""F-01 offline synthetic tests. No real user or agent data."""
import importlib.util
from pathlib import Path
import json
import unittest
spec=importlib.util.spec_from_file_location("f01",Path(__file__).resolve().parents[1]/"bin"/"f01_weekly_draft.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def example():
 return {"week":"2026-W46","f08":{"signed":2,"pending":1,"verification":"NO_DATA: unverified_ref"},
 "f09":{"green":3,"red":1,"unknown":2,"verification":"NO_DATA: unverified_CI"}}
class TestF01(unittest.TestCase):
 def test_summarizes(self):
  x=m.compose(example());self.assertEqual((x["f08"]["signed"],x["f09"]["red"]),(2,1))
 def test_repeat_deterministic(self):self.assertEqual(m.compose(example()),m.compose(example()))
 def test_below_ceiling(self):self.assertLess(len(json.dumps(m.compose(example())).encode()),1024)
 def test_only_aggregates(self):
  self.assertNotIn("unverified_CI",str(m.compose(example())))
  self.assertNotIn("unverified_ref",str(m.compose(example())))
 def test_no_data(self):
  v=example();v["f08"]={"cause":"missing_receipt"};self.assertEqual(m.compose(v)["f08"]["state"],"NO_DATA")
 def test_no_data_requires_reason(self):
  v=example();v["f08"]={"cause":""}
  with self.assertRaises(ValueError):m.compose(v)
 def test_no_negative(self):
  v=example();v["f09"]["red"]=-1
  with self.assertRaises(ValueError):m.compose(v)
 def test_no_forged_verified(self):
  v=example();v["f08"]["verification"]="VERIFIED"
  with self.assertRaises(ValueError):m.compose(v)
 def test_reject_unknown(self):
  v=example();v["model_name"]="secret"
  with self.assertRaises(ValueError):m.compose(v)
 def test_no_private_notes(self):
  v=example();v["f09"]["id"]="private"
  with self.assertRaises(ValueError):m.compose(v)
 def test_week_format(self):
  v=example();v["week"]="2026-46"
  with self.assertRaises(ValueError):m.compose(v)
 def test_freeform_cause_is_rejected(self):
  v=example();v["f08"]={"cause":"private secret text"}
  with self.assertRaises(ValueError):m.compose(v)
 def test_reject_float(self):
  v=example();v["f08"]["signed"]=1.1
  with self.assertRaises(ValueError):m.compose(v)
