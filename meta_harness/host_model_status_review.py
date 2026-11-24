"""Offline HOST review of model-suggested status; never a grant or witness.

A model response is untrusted. The caller supplies independently observed,
immutable HOST evidence and a verifier that checks it against the live source.
Even exact alignment authorizes neither execution nor model promotion.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import copy
import json
import re

from .delegation import HEX, encode, sha

SCHEMA = "preceptoros.lab.host-model-status-review/1"
MODEL_LIMIT_BYTES = 2048
STATUS = frozenset({"NO_DATA", "SIMULATED", "STALE", "LIVE"})
CAUSE = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
MODEL_KEYS = frozenset({"status", "cause", "answer"})
RECORD_KEYS = frozenset({
    "schema", "verdict", "cause", "host_ref", "model_ref", "proposal_ref",
    "expected_state", "observed_epoch", "execution_authorized",
    "training_authorized", "promotion_authorized", "source_authority",
    "receipt_ref",
})


@dataclass(frozen=True)
class HostExpectation:
    """Host-origin expectation, not a credential or an independent attestation."""
    source_ref: str
    model_ref: str
    status: str
    cause: str
    answer: str
    observed_epoch: int
    permission_epoch: int


def _is_hex(v):
    return type(v) is str and HEX.fullmatch(v) is not None


def _valid_expected(h):
    return (type(h) is HostExpectation
            and _is_hex(h.source_ref) and _is_hex(h.model_ref)
            and type(h.status) is str and h.status in STATUS and type(h.cause) is str
            and CAUSE.fullmatch(h.cause) is not None
            and type(h.answer) is str and len(h.answer.encode("utf-8")) <= 256
            and type(h.observed_epoch) is int and 0 <= h.observed_epoch < 2**63
            and type(h.permission_epoch) is int and 0 <= h.permission_epoch < 2**63)


def _unique_object(pairs):
    out = {}
    for key, val in pairs:
        if key in out:
            raise ValueError("duplicate_key")
        out[key] = val
    return out


def _reject_constant(_):
    raise ValueError("nonfinite_value")


def _parse(raw):
    if type(raw) is not str or len(raw.encode("utf-8")) > MODEL_LIMIT_BYTES:
        raise ValueError("invalid_response_size")
    payload = json.loads(raw, object_pairs_hook=_unique_object,
                         parse_constant=_reject_constant)
    if (type(payload) is not dict or set(payload) != MODEL_KEYS
            or payload["status"] not in STATUS
            or type(payload["cause"]) is not str
            or CAUSE.fullmatch(payload["cause"]) is None
            or type(payload["answer"]) is not str
            or len(payload["answer"].encode("utf-8")) > 256):
        raise ValueError("invalid_response_structure")
    return payload


def _receipt(verdict, cause, host_ref, model_ref, proposal_ref,
             expected_state, observed_epoch):
    value = {
        "schema": SCHEMA, "verdict": verdict, "cause": cause,
        "host_ref": host_ref, "model_ref": model_ref,
        "proposal_ref": proposal_ref, "expected_state": expected_state,
        "observed_epoch": observed_epoch,
        "execution_authorized": False, "training_authorized": False,
        "promotion_authorized": False, "source_authority": "NONE",
    }
    value["receipt_ref"] = sha(value)
    if len(encode(value)) >= 1024:
        raise ValueError("review_receipt_exceeds_channel")
    return value


def review(expected, proposal, *, verify_host=None):
    """Compare raw model JSON with HOST evidence; refuse without HOST verifier.

    verify_host must independently recompute the source/epoch/permissions.
    A callback returning True is only trusted in an actual host integration;
    this pure LAB helper cannot attest real-world authority.
    """
    try:
        valid = _valid_expected(expected)
    except (UnicodeError, TypeError, ValueError, OverflowError):
        valid = False
    if not valid:
        return _receipt("NO_DATA", "host_expectation_invalid", None, None,
                        None, "NO_DATA", None)
    host_snapshot = copy.deepcopy(asdict(expected))
    host_ref = sha(host_snapshot)
    proposal_ref = (sha(proposal) if type(proposal) is str
                    and len(proposal.encode("utf-8", errors="replace")) <= MODEL_LIMIT_BYTES
                    else None)
    if not callable(verify_host):
        return _receipt("NO_DATA", "host_verifier_missing", host_ref,
                        expected.model_ref, proposal_ref, "NO_DATA", None)
    try:
        first = verify_host(copy.deepcopy(host_snapshot)) is True
    except Exception:
        first = False
    if not first:
        return _receipt("NO_DATA", "host_evidence_not_witnessed", host_ref,
                        expected.model_ref, proposal_ref, "NO_DATA", None)
    try:
        parsed = _parse(proposal)
    except (UnicodeError, ValueError, TypeError, OverflowError, RecursionError):
        parsed = None
    try:
        last = verify_host(copy.deepcopy(host_snapshot)) is True
    except Exception:
        last = False
    if not last or sha(asdict(expected)) != host_ref:
        return _receipt("NO_DATA", "host_evidence_changed", host_ref,
                        expected.model_ref, proposal_ref, "NO_DATA", None)
    if parsed is None:
        return _receipt("REJECTED", "model_format_invalid", host_ref,
                        expected.model_ref, proposal_ref,
                        expected.status, expected.observed_epoch)
    match = (parsed["status"] == expected.status
             and parsed["cause"] == expected.cause
             and parsed["answer"] == expected.answer)
    return _receipt("EXACT" if match else "REJECTED",
                    "matches_host_expectation_not_authority" if match
                    else "model_semantic_mismatch", host_ref,
                    expected.model_ref, proposal_ref,
                    expected.status, expected.observed_epoch)


def views(record):
    """Use the same bounded record for visual, speech/Acho and machine paths."""
    if (type(record) is not dict or set(record) != RECORD_KEYS
            or record.get("schema") != SCHEMA
            or record.get("receipt_ref") != sha({k: v for k, v in record.items()
                                               if k != "receipt_ref"})
            or record.get("execution_authorized") is not False
            or record.get("training_authorized") is not False
            or record.get("promotion_authorized") is not False
            or record.get("source_authority") != "NONE"
            or len(encode(record)) >= 1024):
        raise ValueError("invalid_review_receipt")
    narrative = {
        "EXACT": "Model fields matched independently checked HOST expectations; no action is authorized.",
        "REJECTED": "Model output rejected by HOST review; no action is authorized.",
        "NO_DATA": "HOST evidence is not verified; no model state is authoritative.",
    }.get(record.get("verdict"))
    if narrative is None:
        raise ValueError("invalid_review_receipt")
    shared = {"state_ref": record["receipt_ref"], "summary": narrative}
    return {"text": copy.deepcopy(shared), "speech": copy.deepcopy(shared),
            "machine": {**shared, "record": copy.deepcopy(record)}}


def verify_views(packet, expected, proposal, *, verify_host=None):
    """Self-digest alone is insufficient: compare with a fresh HOST readback."""
    try:
        return packet == views(review(expected, proposal, verify_host=verify_host))
    except Exception:
        return False
