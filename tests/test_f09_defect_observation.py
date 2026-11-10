"""F-09 synthetic closed-fixture tests."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location("f09",Path(__file__).resolve().parents[1]/"bin"/"f09_defect_observation.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def row(i,state="GREEN",attempted=False,seen=None):
    s={"attempted":attempted}
    if attempted:s["red_before_green"]=seen
    r={"id":i,"state":state,"sabotage":s}
    if state=="NO_DATA":r["cause"]="missing_CI"
    return r
class TestF09(unittest.TestCase):
    def test_counts(self):
        v=m.summarize({"observations":[row("a"),row("b","RED",True,True),row("c","NO_DATA")]})
        self.assertEqual((v["observed"],v["red_fraction"],v["sabotage_fraction"]),(2,[1,2],[1,1]))
    def test_two_runs_same(self):
        x={"observations":[row("a")]};self.assertEqual(m.summarize(x),m.summarize(x))
    def test_empty(self):
        x=m.summarize({"observations":[]});self.assertIsNone(x["red_fraction"]);self.assertIn("NO_DATA",x["cause_red_fraction"])
    def test_no_sabotage(self):self.assertIn("NO_DATA",m.summarize({"observations":[row("a")]})["cause_sabotage_fraction"])
    def test_unknown_without_cause(self):
        x=row("a","NO_DATA");x.pop("cause")
        with self.assertRaises(ValueError):m.summarize({"observations":[x]})
    def test_duplicate(self):
        with self.assertRaises(ValueError):m.summarize({"observations":[row("a"),row("a")]})
    def test_bad_state(self):
        with self.assertRaises(ValueError):m.summarize({"observations":[row("a","YELLOW")]})
    def test_missing_sabotage(self):
        x=row("a");x.pop("sabotage")
        with self.assertRaises(ValueError):m.summarize({"observations":[x]})
    def test_claim_without_attempt(self):
        x=row("a");x["sabotage"]["red_before_green"]=True
        with self.assertRaises(ValueError):m.summarize({"observations":[x]})
    def test_missing_red_measured(self):
        with self.assertRaises(ValueError):m.summarize({"observations":[row("a","GREEN",True,None)]})
    def test_sabotage_unknown_pr(self):
        with self.assertRaises(ValueError):m.summarize({"observations":[row("a","NO_DATA",True,True)]})
    def test_scrub(self):
        x=m.summarize({"observations":[row("private_sensitive_id")]})
        self.assertNotIn("private_sensitive_id",str(x))
    def test_no_extra(self):
        x=row("a");x["self_certified"]=True
        with self.assertRaises(ValueError):m.summarize({"observations":[x]})
