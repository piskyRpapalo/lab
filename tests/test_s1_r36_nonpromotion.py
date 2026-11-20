"""R36/S1 legacy receipt non-promotion against the canonical LAB gate.

Synthetic local boundary tests, not a new S1->LAB adapter. Historical p0x R36
is deliberately NOT imported or trusted.
"""
import copy
import unittest
from meta_harness.delegation import Session, TokenBudget, sha, verify
from meta_harness.self_improvement import propose
from tests.test_meta_delegation import STAMP, grant, result, task

def untrusted_r36():
    record = {
        "schema": "preceptoros.lab.receipt/1",
        "adapter": "hexelion.s1-lab-adapter/1",
        "state": "MEASURED",
        "origin": "MEASURED",
        "witnessed": False,
        "origin_evidence": "NO_DATA(no_independent_witness)",
        "proof_of_auth": None,
        "stages": {},
        "s1_fields": {"estado": "OK", "origen": "modelo"},
    }
    record["sha256"] = sha(record)
    return record

class S1LegacyNonPromotionTests(unittest.TestCase):
    def test_ok_without_phases_cannot_become_a_meta_receipt(self):
        r = untrusted_r36()
        self.assertEqual(r["state"], "MEASURED")
        self.assertEqual(r["stages"], {})
        self.assertFalse(verify(r))

    def test_self_declared_witness_hash_is_not_authority(self):
        r = untrusted_r36()
        r["witnessed"] = True
        r["origin_evidence"] = "MEASURED"
        r["proof_of_auth"] = "model_says_authorized"
        r["sha256"] = sha({k: v for k, v in r.items() if k != "sha256"})
        self.assertFalse(verify(r))

    def test_schema_relabel_and_rehash_cannot_bypass_closed_contract(self):
        r = untrusted_r36()
        r["schema"] = "preceptoros.meta-receipt/1"
        r["receipt_ref"] = sha({k: v for k, v in r.items() if k != "receipt_ref"})
        self.assertFalse(verify(r))

    def test_optimizer_rejects_legacy_measured_success(self):
        r = untrusted_r36()
        proposal = propose([r], verify_source=lambda _r: True)
        self.assertEqual(proposal["state"], "NO_DATA")
        self.assertFalse(proposal["execution_authorized"])
        self.assertEqual(proposal["suggestions"], [])

    def test_valid_hash_does_not_replace_exact_session_witness(self):
        t = task()
        host = Session(grant, TokenBudget(64))
        receipt = host.execute(t, result, observed_at=STAMP)
        self.assertTrue(verify(receipt))
        self.assertTrue(host.attests(receipt, t))
        other = Session(grant, TokenBudget(64))
        self.assertFalse(other.attests(receipt, t))
        forged = copy.deepcopy(receipt)
        forged["source"] = "untrusted"
        forged["receipt_ref"] = sha({k: v for k, v in forged.items()
                                      if k != "receipt_ref"})
        self.assertTrue(verify(forged))  # self-consistent, not authenticated
        self.assertFalse(host.attests(forged, t))
