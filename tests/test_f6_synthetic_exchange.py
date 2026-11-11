"""F6-01 synthetic A2A envelope; no real signatures, network, or economic action."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "bin" / "f6_synthetic_exchange.py"
spec = importlib.util.spec_from_file_location("f6exchange", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def packet(kind, facts):
    return {"schema": m.SCHEMA, "message_id": "case_01",
            "sender": "agent_a", "recipient": "testnet_sink",
            "probe": {"kind": kind, "facts": facts}}


class TestF6SyntheticExchange(unittest.TestCase):
    def test_reach_inflation_denied(self):
        p = packet("reach_inflation", {"claimed_reach": 3, "receipt_digests": ["a", "b"]})
        self.assertEqual(m.exchange(p)["verdict"], "DENY")

    def test_duplicate_reach_denied(self):
        p = packet("reach_inflation", {"claimed_reach": 2, "receipt_digests": ["a", "a"]})
        self.assertEqual(m.exchange(p)["verdict"], "DENY")

    def test_plausible_reach_unverified(self):
        p = packet("reach_inflation", {"claimed_reach": 1, "receipt_digests": ["a"]})
        self.assertEqual(m.exchange(p)["verdict"], "NO_DATA")

    def test_overbudget_denied(self):
        p = packet("budget_overpromise", {"promised_j": 8, "available_j": 7})
        self.assertEqual(m.exchange(p)["verdict"], "DENY")

    def test_unattested_budget_is_nodata(self):
        p = packet("budget_overpromise", {"promised_j": 6, "available_j": 7})
        self.assertEqual(m.exchange(p)["verdict"], "NO_DATA")

    def test_agent_arbitration_denied(self):
        p = packet("arbitration_spoof", {"role": "agent", "requests_arbitration": True})
        self.assertEqual(m.exchange(p)["verdict"], "DENY")

    def test_declared_sovereign_is_not_signature(self):
        p = packet("arbitration_spoof", {"role": "sovereign", "requests_arbitration": True})
        r = m.exchange(p)
        self.assertEqual(r["verdict"], "NO_DATA")
        self.assertEqual(r["authority"], "NONE")

    def test_no_private_facts_in_receipt(self):
        p = packet("reach_inflation", {"claimed_reach": 1, "receipt_digests": ["hidden_identifier"]})
        self.assertNotIn("hidden_identifier", json.dumps(m.exchange(p)))

    def test_deterministic_digest(self):
        p = packet("budget_overpromise", {"promised_j": 8, "available_j": 7})
        self.assertEqual(m.exchange(p), m.exchange(copy.deepcopy(p)))

    def test_changed_fact_changes_digest(self):
        a = packet("budget_overpromise", {"promised_j": 8, "available_j": 7})
        b = packet("budget_overpromise", {"promised_j": 9, "available_j": 7})
        self.assertNotEqual(m.exchange(a)["message_sha256"], m.exchange(b)["message_sha256"])

    def test_reject_new_message_fields(self):
        p = packet("budget_overpromise", {"promised_j": 1, "available_j": 1})
        p["token"] = "not_allowed"
        with self.assertRaises(ValueError):
            m.exchange(p)

    def test_no_network_or_signed_claim(self):
        p = packet("budget_overpromise", {"promised_j": 1, "available_j": 1})
        r = m.exchange(p)
        self.assertTrue(r["signature"].startswith("NO_DATA"))
        self.assertTrue(r["transport"].startswith("NO_DATA"))

    def test_reject_sender_equal_recipient(self):
        p = packet("budget_overpromise", {"promised_j": 1, "available_j": 1})
        p["recipient"] = p["sender"]
        with self.assertRaises(ValueError):
            m.exchange(p)

    def test_reject_path_like_sender(self):
        p = packet("budget_overpromise", {"promised_j": 1, "available_j": 1})
        p["sender"] = "/private/agent"
        with self.assertRaises(ValueError):
            m.exchange(p)

    def test_reject_unknown_probe(self):
        p = packet("other", {})
        with self.assertRaises(ValueError):
            m.exchange(p)

    def test_no_authority_on_denial(self):
        p = packet("arbitration_spoof", {"role": "agent", "requests_arbitration": True})
        self.assertEqual(m.exchange(p)["authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
