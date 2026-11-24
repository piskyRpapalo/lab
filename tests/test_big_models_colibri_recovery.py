"""Colibri historical metadata: never promote a design claim into measured inference."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "benchmarks" / "big-models-20261123"

class ColibriRecoveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.card = json.loads((CARD / "colibri-recovery-20261007.json").read_text(encoding="utf-8"))

    def test_historical_sources_not_physical(self):
        c = self.card
        self.assertEqual(c["status"], "HISTORICAL_DESIGN_RECOVERED_NOT_BENCHMARKED")
        self.assertEqual(c["physical_samples_colibri"], 0)
        self.assertEqual([x["date"] for x in c["source_record"]], ["2026-10-07", "2026-10-13", "2026-10-21"])
        self.assertTrue(all(c["gates"][k].startswith("NO_DATA(") for k in ("engine", "throughput", "disk_streaming", "eight_gb", "lora", "gold")))
        self.assertEqual(c["gates"]["promotion"], "NOT_PROMOTED")

    def test_protocol_not_executed_and_no_relabel(self):
        p = self.card["proposed_protocol"]
        self.assertEqual(p["state"], "PROPOSAL_NOT_EXECUTED")
        self.assertEqual([x["id"] for x in p["phases"]], ["C0", "C1", "C2", "C3"])
        for k in ("no_new_service", "no_new_training", "no_promotion"):
            self.assertIs(p[k], True)
        self.assertIn("not Colibri measurements", self.card["comparison"]["not_attribution"])
        for ref in self.card["comparison"]["historical_context"] + self.card["comparison"]["current_context"]:
            self.assertTrue((CARD / ref).is_file(), ref)
        for ref in p["reuse"][:4]:
            self.assertTrue((ROOT / ref).is_file(), ref)

    def test_canonical_index_and_private_boundary(self):
        self.assertIn("(colibri-recovery-20261007.json)", (CARD / "README.md").read_text(encoding="utf-8"))
        index = (ROOT / "benchmarks" / "README.md").read_text(encoding="utf-8")
        self.assertEqual(index.count("(big-models-20261123/README.md)"), 1)
        self.assertIn("no measured Colibrí samples", index)
        self.assertIn("private adaptation", self.card["scope"])
        def walk(v):
            if isinstance(v, dict):
                self.assertFalse({"prompt", "completion", "raw_output", "private_path", "answer_key"} & set(v))
                for x in v.values():
                    walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        walk(self.card)

if __name__ == "__main__":
    unittest.main()
