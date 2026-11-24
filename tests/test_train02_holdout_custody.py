"""Custody evidence tests: never synthesize an independent GOLD claim."""
from dataclasses import replace
import json
from pathlib import Path
import unittest
import copy

from meta_harness.delegation import sha, encode
from meta_harness.train02_holdout_custody import (
    CustodySeal, FamilyRoot, FAMILIES, review, views,
)

PREREG = Path(__file__).resolve().parents[1] / "benchmarks" / "big-models-20261123" / "train02-2v4-blind-prereg-20261123.json"


def fixture():
    m = json.loads(PREREG.read_text(encoding="utf-8"))
    rows = tuple(FamilyRoot(row["id"], row["cases"], row["es"], row["pt"],
                            sha("separate-source-family-" + row["id"]))
                 for row in m["holdout"]["families"])
    return m, CustodySeal(
        case_root_sha256=sha("fixture-private-case-root"),
        answer_key_sha256=sha("fixture-private-host-answer-key"),
        source_lineage_sha256=sha("fixture-lineage"),
        case_order_sha256=sha("fixture-shuffle"),
        source_exclusion_sha256=sha("fixture-source-audit"),
        custodian_ref=sha("fixture-independent-custodian"),
        signature_ref=sha("fixture-unverified-signature"),
        sealed_at_utc="2026-11-24T12:00:00Z",
        owner_permission_epoch=11, families=rows)


def tested(prereg=None, claim=None, *, start="2026-11-24T12:01:00Z",
           external=None, overlap=None):
    m,c=fixture()
    return review(m if prereg is None else prereg,
                  c if claim is None else claim, run_start_utc=start,
                  verify_external=external, verify_contamination=overlap)


class CustodyAdmissionTests(unittest.TestCase):
    def test_no_external_signature_never_ready(self):
        r=tested()
        self.assertEqual((r["state"],r["cause"]),("NO_DATA","independent_custodian_missing"))
        self.assertFalse(r["independent_gold_proven"])
        self.assertFalse(r["inference_authorized"])

    def test_no_source_exclusion_audit_never_ready(self):
        r=tested(external=lambda _:True)
        self.assertEqual(r["cause"],"independent_overlap_audit_missing")

    def test_both_injected_checks_yield_review_not_gold(self):
        r=tested(external=lambda _:True,overlap=lambda _:True)
        self.assertEqual(r["state"],"READY_FOR_OWNER_REVIEW")
        self.assertFalse(r["independent_gold_proven"])
        self.assertFalse(r["inference_authorized"])
        self.assertFalse(r["promotion_authorized"])
        self.assertLess(len(encode(r)),1024)

    def test_unverified_or_exception_attestor_fails_closed(self):
        for witness in (lambda _:False,lambda _: (_ for _ in ()).throw(RuntimeError("/owner/secret"))):
            r=tested(external=witness,overlap=lambda _:True)
            self.assertEqual(r["cause"],"custodian_attestation_unverified")
            self.assertNotIn("/owner/",json.dumps(r))

    def test_source_overlap_auditor_must_attest(self):
        r=tested(external=lambda _:True,overlap=lambda _:False)
        self.assertEqual(r["cause"],"train_dev_exclusion_unverified")

    def test_later_revoke_between_double_witness_checks_fails_closed(self):
        count={"n":0}
        def witness(_):
            count["n"]+=1
            return count["n"]==1
        r=tested(external=witness,overlap=lambda _:True)
        self.assertEqual(r["cause"],"source_witness_changed")
        self.assertFalse(r["inference_authorized"])

    def test_root_hash_count_duplicate_and_lang_tamper_denied(self):
        m,c=fixture()
        samples=(replace(c,case_root_sha256="bad"),
                 replace(c,answer_key_sha256=sha("fixture-private-case-root")[:30]),
                 replace(c,families=(c.families[0],)*6),
                 replace(c,families=(replace(c.families[0],es=5),)+c.families[1:]),
                 replace(c,families=(replace(c.families[0],source_family_sha256="invalid"),)+c.families[1:]),
                 replace(c,owner_permission_epoch=True))
        for x in samples:
            with self.subTest(change=x):
                self.assertEqual(tested(claim=x,external=lambda _:True,overlap=lambda _:True)["state"],"NO_DATA")

    def test_requires_seal_preceding_model_access(self):
        for start in (None,"2026-11-24T12:00:00Z","2026-11-24T11:59:59Z","bad"):
            with self.subTest(start=start):
                self.assertEqual(tested(start=start,external=lambda _:True,overlap=lambda _:True)["cause"],
                                 "seal_not_before_model_access")

    def test_pinned_seal_before_run_changes_receipt(self):
        m,c=fixture()
        x=tested(external=lambda _:True,overlap=lambda _:True)
        y=tested(claim=replace(c,case_order_sha256=sha("new-order")),external=lambda _:True,overlap=lambda _:True)
        self.assertNotEqual(x["receipt_ref"],y["receipt_ref"])

    def test_tampered_prereg_fails_without_owner_authority(self):
        m,c=fixture()
        m["holdout"]["total_unique_cases"]=47
        r=tested(prereg=m,claim=c,external=lambda _:True,overlap=lambda _:True)
        self.assertEqual((r["state"],r["cause"]),("NO_DATA","custody_structure_invalid"))

    def test_acho_parity_and_forged_self_attestation_rejected(self):
        record=tested(external=lambda _:True,overlap=lambda _:True)
        bundle=views(record)
        self.assertEqual(bundle["text"],bundle["speech"])
        self.assertEqual(bundle["text"]["summary"],bundle["machine"]["summary"])
        self.assertEqual(bundle["text"]["state_ref"],bundle["machine"]["state_ref"])
        for change in (("source_authority","OWNER"),
                       ("inference_authorized",True),
                       ("receipt_ref",sha("forged"))):
            bad=copy.deepcopy(record)
            bad[change[0]]=change[1]
            with self.assertRaises(ValueError):
                views(bad)

    def test_no_case_or_answer_key_public_text_leak(self):
        import inspect
        from meta_harness import train02_holdout_custody
        src=inspect.getsource(train02_holdout_custody)
        self.assertNotIn("open(",src)
        self.assertNotIn("urllib",src)
        self.assertNotIn("requests",src)
        self.assertNotIn("subprocess",src)
        m,c=fixture()
        r=tested(external=lambda _:True,overlap=lambda _:True)
        self.assertNotIn("fixture-private",json.dumps(r))


if __name__=="__main__":
    unittest.main()
