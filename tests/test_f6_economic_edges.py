"""Conservative equal-boundary behavior for the existing F6 synthetic rules."""
import importlib.util
from pathlib import Path
import unittest

target = Path(__file__).resolve().parents[1] / "bin" / "f6_economic_probes.py"
spec = importlib.util.spec_from_file_location("f6_edges", target)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TestF6Edges(unittest.TestCase):
    def test_exact_reach_not_denied_without_signatures(self):
        p = {"kind": "reach_inflation",
             "facts": {"claimed_reach": 1, "receipt_digests": ["digest_a"]}}
        self.assertEqual(m.assess(p)["verdict"], "NO_DATA")

    def test_exact_budget_not_denied_without_attestation(self):
        p = {"kind": "budget_overpromise",
             "facts": {"promised_j": 10, "available_j": 10}}
        self.assertEqual(m.assess(p)["verdict"], "NO_DATA")

    def test_zero_budget_is_still_unattested(self):
        p = {"kind": "budget_overpromise",
             "facts": {"promised_j": 0, "available_j": 0}}
        self.assertEqual(m.assess(p)["verdict"], "NO_DATA")

    def test_agent_cannot_request_arbitration(self):
        p = {"kind": "arbitration_spoof",
             "facts": {"role": "agent", "requests_arbitration": True}}
        self.assertEqual(m.assess(p)["verdict"], "DENY")


if __name__ == "__main__":
    unittest.main()
