"""F-11 synthetic provenance and split sabotage tests."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location("f11",Path(__file__).resolve().parents[1]/"bin"/"f11_origin_admission.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def digest(i):return format(i,"064x")
def row(i,origin,split="train",class_="same"):return {"sample_sha256":digest(i),"origin_sha256":digest(origin),"split":split,"class":class_}
class TestF11(unittest.TestCase):
 def test_empty_no_data(self):self.assertEqual(m.admit({"samples":[]})["state"],"NO_DATA")
 def test_below_threshold(self):self.assertIn("training_sample_and_six_eval_per_class_required",m.admit({"samples":[row(1,1,"eval") ]})["cause"])
 def test_six_each(self):
  a=[row(i+1,1,"eval","same") for i in range(6)]+[row(i+7,2,"eval","cross") for i in range(6)]
  a.insert(0,row(13,3,"train"))
  self.assertEqual(m.admit({"samples":a})["state"],"READY_FOR_EVAL_FIXTURE_ONLY")
 def test_no_train_cannot_be_ready(self):
  a=[row(i+1,1,"eval","same") for i in range(6)]+[row(i+7,2,"eval","cross") for i in range(6)]
  self.assertEqual(m.admit({"samples":a})["state"],"NO_DATA")
 def test_origin_leak(self):
  with self.assertRaisesRegex(ValueError,"origin_leakage"):m.admit({"samples":[row(1,8),row(2,8,"eval")]})
 def test_sample_duplicate(self):
  with self.assertRaisesRegex(ValueError,"duplicate_sample"):m.admit({"samples":[row(1,8),row(1,9,"eval")]})
 def test_bad_hash(self):
  x=row(1,1);x["sample_sha256"]="abc"
  with self.assertRaises(ValueError):m.admit({"samples":[x]})
 def test_uppercase_hash_rejected(self):
  x=row(10,1);x["sample_sha256"]="A"*64
  with self.assertRaises(ValueError):m.admit({"samples":[x]})
 def test_unknown_field(self):
  x=row(1,1);x["prompt"]="private"
  with self.assertRaises(ValueError):m.admit({"samples":[x]})
 def test_unknown_split(self):
  with self.assertRaises(ValueError):m.admit({"samples":[row(1,1,"holdout")]})
 def test_unknown_class(self):
  with self.assertRaises(ValueError):m.admit({"samples":[row(1,1,"eval","mixed")]})
 def test_closed_root(self):
  with self.assertRaises(ValueError):m.admit({"samples":[],"policy":"override"})
 def test_scrub(self):
  x=m.admit({"samples":[row(1,999,"eval")]})
  self.assertNotIn(digest(999),str(x))
 def test_deterministic(self):
  x={"samples":[row(1,5,"train"),row(2,6,"eval")]}
  self.assertEqual(m.admit(x),m.admit(x))
 def test_ready_is_not_benchmark(self):
  a=[row(i+1,1,"eval","same") for i in range(6)]+[row(i+7,2,"eval","cross") for i in range(6)]
  a.insert(0,row(13,3,"train"))
  v=m.admit({"samples":a})
  self.assertIn("NO_DATA: model_judgments",v["cause"])
