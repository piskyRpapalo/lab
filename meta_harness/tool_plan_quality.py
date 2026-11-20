"""Offline quality review of a model's proposed tool plan, NOT admission.

The host supplies an independently sourced, allowlisted set of operations
that are both requested and currently eligible. A model may not extend it.
This diagnoses coverage, duplicates, out-of-scope choices and malformed output
before S1/Session/resource admission. It creates no grant, network call,
execution, cache transfer, training signal or persistent state.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import json

from .delegation import HEX, encode, sha

SCHEMA = "preceptoros.tool-plan-quality/1"
PROPOSAL_MAX_BYTES = 4096
MAX_TASKS = 8
RECORD_KEYS = frozenset({
    "schema", "state", "cause", "policy_ref", "proposal_ref",
    "expected_count", "selected_count", "missing_count",
    "out_of_scope_count", "duplicate_count", "execution_authorized",
    "kv_reuse_authorized", "training_authorized", "source_authority",
    "receipt_ref",
})


@dataclass(frozen=True)
class HostPolicy:
    """Host-owned expectation, not a model-origin grant or cryptographic proof.

    Eligible (node_ref, tool_ref) pairs must be independently checked by the
    injected host verifier as requested, permitted, fresh and correctly pinned.
    """
    task_ref: str
    source_ref: str
    tool_scope_ref: str
    model_ref: str
    base_ref: str
    head_ref: str | None
    generation: int
    permission_epoch: int
    eligible: tuple[tuple[str, str], ...]


def _hex(value):
    return type(value) is str and HEX.fullmatch(value) is not None


def _valid_policy(p):
    if type(p) is not HostPolicy:
        return False
    if not all(_hex(getattr(p, k)) for k in
               ("task_ref", "source_ref", "tool_scope_ref", "model_ref", "base_ref")):
        return False
    if p.head_ref is not None and not _hex(p.head_ref):
        return False
    if (type(p.generation) is not int or not 0 <= p.generation < 2**63
            or type(p.permission_epoch) is not int
            or not 0 <= p.permission_epoch < 2**63):
        return False
    if type(p.eligible) is not tuple or len(p.eligible) > MAX_TASKS:
        return False
    seen = set()
    for row in p.eligible:
        if (type(row) is not tuple or len(row) != 2
                or not all(_hex(v) for v in row) or row in seen):
            return False
        seen.add(row)
    return True


def _unique_object(pairs):
    record = {}
    for key, value in pairs:
        if key in record:
            raise ValueError("duplicate_json_key")
        record[key] = value
    return record


def _reject_constant(_):
    raise ValueError("nonfinite_json_number")


def _parse_proposal(payload):
    if (type(payload) is not str
            or len(payload.encode("utf-8")) > PROPOSAL_MAX_BYTES):
        raise ValueError("proposal_byte_bound")
    value = json.loads(payload, object_pairs_hook=_unique_object,
                       parse_constant=_reject_constant)
    if (type(value) is not dict or set(value) != {"tasks"}
            or type(value["tasks"]) is not list
            or len(value["tasks"]) > MAX_TASKS):
        raise ValueError("proposal_structure")
    rows = []
    for task in value["tasks"]:
        if (type(task) is not dict or set(task) != {"node_ref", "tool_ref"}
                or not _hex(task["node_ref"]) or not _hex(task["tool_ref"])):
            raise ValueError("proposal_task")
        rows.append((task["node_ref"], task["tool_ref"]))
    return rows


def _pack(state, cause, policy_ref, proposal_ref, *,
          expected=0, selected=0, missing=0, extra=0, duplicate=0):
    record = {
        "schema": SCHEMA, "state": state, "cause": cause,
        "policy_ref": policy_ref, "proposal_ref": proposal_ref,
        "expected_count": expected, "selected_count": selected,
        "missing_count": missing, "out_of_scope_count": extra,
        "duplicate_count": duplicate,
        "execution_authorized": False, "kv_reuse_authorized": False,
        "training_authorized": False, "source_authority": "NONE",
    }
    record["receipt_ref"] = sha(record)
    if len(encode(record)) >= 1024:
        raise ValueError("receipt_budget")
    return record


def review(policy, proposal_json, *, verify_policy=None):
    """Return a bounded non-authoritative result from independently pinned gold.

    The caller must build HostPolicy outside the model using a trusted
    requested-intent and permission source. The callback must recheck its
    current grant, task, policy, model, head and generation. A successful
    comparison NEVER replaces a real S1 grant or resource lease.
    """
    if not _valid_policy(policy):
        return _pack("NO_DATA", "host_policy_invalid", None, None)
    pinned = copy.deepcopy(asdict(policy))
    policy_ref = sha(pinned)
    if not callable(verify_policy):
        return _pack("NO_DATA", "host_witness_missing", policy_ref, None)
    try:
        before = verify_policy(copy.deepcopy(pinned)) is True
    except Exception:
        before = False
    if not before:
        return _pack("NO_DATA", "host_policy_not_witnessed", policy_ref, None)

    proposal_ref = sha(proposal_json) if type(proposal_json) is str else None
    try:
        selected = _parse_proposal(proposal_json)
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        return _pack("NO_DATA", "model_proposal_invalid", policy_ref, proposal_ref)

    try:
        after = verify_policy(copy.deepcopy(pinned)) is True
    except Exception:
        after = False
    if not after or sha(asdict(policy)) != policy_ref:
        return _pack("NO_DATA", "host_policy_changed", policy_ref, proposal_ref)

    distinct = set(selected)
    eligible = set(policy.eligible)
    extra = len(distinct - eligible)
    missing = len(eligible - distinct)
    duplicate = len(selected) - len(distinct)
    if extra or duplicate:
        state = "REJECTED"
        cause = ("out_of_scope_and_duplicate" if extra and duplicate
                 else "out_of_scope" if extra else "duplicate_model_tasks")
    elif missing:
        state, cause = "REVIEW_REQUIRED", "authorized_targets_omitted"
    else:
        state, cause = "EXACT", "matches_host_gold_not_authority"
    return _pack(state, cause, policy_ref, proposal_ref,
                 expected=len(eligible), selected=len(selected),
                 missing=missing, extra=extra, duplicate=duplicate)


def views(record):
    """Same observed status for text, speech/Acho, and machine consumers."""
    if (type(record) is not dict or set(record) != RECORD_KEYS
            or record.get("schema") != SCHEMA
            or record.get("receipt_ref") != sha({k: v for k, v in record.items()
                                                 if k != "receipt_ref"})
            or record.get("execution_authorized") is not False
            or record.get("kv_reuse_authorized") is not False
            or record.get("training_authorized") is not False
            or record.get("source_authority") != "NONE"):
        raise ValueError("quality_receipt_invalid")
    summaries = {
        "EXACT": "Plan matches independently witnessed expected scope. No tool is authorized.",
        "REVIEW_REQUIRED": "Some expected tool operations are missing. Review required.",
        "REJECTED": "Model proposed duplicate or out-of-scope operations. Refused.",
        "NO_DATA": "Plan quality is unverified. No execution is authorized.",
    }
    status = summaries.get(record.get("state"))
    if status is None:
        raise ValueError("quality_receipt_invalid")
    item = {"state_ref": record["receipt_ref"], "summary": status}
    return {"text": dict(item), "speech": dict(item),
            "machine": {"state_ref": record["receipt_ref"],
                        "summary": status, "record": copy.deepcopy(record)}}
