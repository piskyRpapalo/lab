"""TRAIN-02 independent holdout custody *admission*, not a GOLD maker.

Never manufactures cases, an answer key, signature, or authority. Only a
separately collected private corpus with independently checked source and
contamination witnesses can pass the metadata gate. Passing still does not
authorize model inference, S1 effects, promotion or an owner signature.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import copy
import re

from .delegation import HEX, sha, encode

SCHEMA = "hexelion.train02.custody-preflight/1"
FAMILIES = ("math_h02", "no_data_causal", "forged_live_authority",
            "revoked_mcp_error", "tool_grant_intersection", "acho_multichannel")
STAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")


@dataclass(frozen=True)
class FamilyRoot:
    family: str
    cases: int
    es: int
    pt: int
    source_family_sha256: str


@dataclass(frozen=True)
class CustodySeal:
    """Untrusted claim until verified by a real independent custodian."""
    case_root_sha256: str
    answer_key_sha256: str
    source_lineage_sha256: str
    case_order_sha256: str
    source_exclusion_sha256: str
    custodian_ref: str
    signature_ref: str
    sealed_at_utc: str
    owner_permission_epoch: int
    families: tuple[FamilyRoot, ...]


def _hex(x):
    return type(x) is str and HEX.fullmatch(x) is not None


def _stamp(s):
    if type(s) is not str or STAMP.fullmatch(s) is None:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _structural(packet, prereg):
    if type(packet) is not CustodySeal or type(prereg) is not dict:
        return False
    if prereg.get("schema") != "hexelion.train02.blind-2v4-prereg/1":
        return False
    holdout = prereg.get("holdout")
    if type(holdout) is not dict or holdout.get("total_unique_cases") != 48:
        return False
    if (not all(_hex(getattr(packet, field)) for field in (
            "case_root_sha256", "answer_key_sha256", "source_lineage_sha256",
            "case_order_sha256", "source_exclusion_sha256", "custodian_ref",
            "signature_ref"))):
        return False
    if type(packet.owner_permission_epoch) is not int or not 0 <= packet.owner_permission_epoch < 2**63:
        return False
    if _stamp(packet.sealed_at_utc) is None:
        return False
    if type(packet.families) is not tuple or len(packet.families) != 6:
        return False
    expected = {row["id"]: (row["cases"], row["es"], row["pt"])
                for row in holdout.get("families", [])
                if type(row) is dict and type(row.get("id")) is str}
    if set(expected) != set(FAMILIES):
        return False
    roots = []
    for row in packet.families:
        if type(row) is not FamilyRoot or row.family not in expected:
            return False
        if any(type(v) is not int for v in (row.cases, row.es, row.pt)):
            return False
        if (row.cases, row.es, row.pt) != expected[row.family] or not _hex(row.source_family_sha256):
            return False
        roots.append(row.source_family_sha256)
    if len(set(row.family for row in packet.families)) != 6 or len(set(roots)) != 6:
        return False
    return sum(row.es for row in packet.families) == 24 and sum(row.pt for row in packet.families) == 24


def _receipt(state, cause, prereg_ref, claim_ref, witness_epoch):
    r = {
        "schema": SCHEMA, "state": state, "cause": cause,
        "prereg_ref": prereg_ref, "claim_ref": claim_ref,
        "witness_epoch": witness_epoch,
        "independent_gold_proven": False, "inference_authorized": False,
        "training_authorized": False, "promotion_authorized": False,
        "source_authority": "NONE",
    }
    r["receipt_ref"] = sha(r)
    if len(encode(r)) >= 1024:
        raise ValueError("custody_receipt_budget")
    return r


def review(prereg, packet, *, run_start_utc=None,
           verify_external=None, verify_contamination=None):
    """Provisional metadata review: no raw corpus, keys or model calls.

    Callbacks must independently validate the real signed custodian, sealed
    case/key roots and access chronology, and the full TRAIN/DEV overlap and
    near-duplicate audit. Returning True in a unit test is NOT an attestation.
    """
    try:
        prereg_ref = sha(prereg) if type(prereg) is dict else None
        valid = _structural(packet, prereg)
        claim_ref = sha(asdict(packet)) if valid else None
    except (TypeError, ValueError, UnicodeError, OverflowError):
        prereg_ref, valid, claim_ref = None, False, None
    if not valid:
        return _receipt("NO_DATA", "custody_structure_invalid", prereg_ref, None, None)
    seal_time = _stamp(packet.sealed_at_utc)
    start_time = _stamp(run_start_utc)
    if start_time is None or seal_time >= start_time:
        return _receipt("NO_DATA", "seal_not_before_model_access", prereg_ref,
                        claim_ref, packet.owner_permission_epoch)
    if not callable(verify_external):
        return _receipt("NO_DATA", "independent_custodian_missing", prereg_ref,
                        claim_ref, packet.owner_permission_epoch)
    if not callable(verify_contamination):
        return _receipt("NO_DATA", "independent_overlap_audit_missing", prereg_ref,
                        claim_ref, packet.owner_permission_epoch)
    claim = copy.deepcopy(asdict(packet))
    def check(callback):
        try:
            return callback(copy.deepcopy(claim)) is True
        except Exception:
            return False
    if not check(verify_external):
        return _receipt("NO_DATA", "custodian_attestation_unverified", prereg_ref,
                        claim_ref, packet.owner_permission_epoch)
    if not check(verify_contamination):
        return _receipt("NO_DATA", "train_dev_exclusion_unverified", prereg_ref,
                        claim_ref, packet.owner_permission_epoch)
    if not check(verify_external) or not check(verify_contamination):
        return _receipt("NO_DATA", "source_witness_changed", prereg_ref,
                        claim_ref, packet.owner_permission_epoch)
    if sha(asdict(packet)) != claim_ref or sha(prereg) != prereg_ref:
        return _receipt("NO_DATA", "custody_evidence_changed", prereg_ref,
                        claim_ref, packet.owner_permission_epoch)
    return _receipt("READY_FOR_OWNER_REVIEW", "sealed_metadata_structurally_witnessed_not_gold",
                    prereg_ref, claim_ref, packet.owner_permission_epoch)


def views(record):
    """Acho text, speech and machine show the exact same review state."""
    if (type(record) is not dict or record.get("schema") != SCHEMA
            or record.get("receipt_ref") != sha({k: v for k, v in record.items()
                                               if k != "receipt_ref"})
            or record.get("source_authority") != "NONE"
            or any(record.get(x) is not False for x in (
                "independent_gold_proven", "inference_authorized",
                "training_authorized", "promotion_authorized"))
            or len(encode(record)) >= 1024):
        raise ValueError("invalid_custody_review_receipt")
    message = {
        "NO_DATA": "Independent sealed holdout custody is not verified; no inference is authorized.",
        "READY_FOR_OWNER_REVIEW": "Independent custody metadata passed injected checks; owner review and authorization remain required.",
    }.get(record.get("state"))
    if message is None:
        raise ValueError("invalid_custody_review_receipt")
    s = {"state_ref": record["receipt_ref"], "summary": message}
    return {"text": copy.deepcopy(s), "speech": copy.deepcopy(s),
            "machine": {**s, "record": copy.deepcopy(record)}}
