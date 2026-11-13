#!/usr/bin/env python3
"""Adversarial false-success judge for synthetic receipts.

Detects patterns where a receipt or tool response appears successful but
should be rejected: unknown evidence claiming verified, wrong identity,
contradictory signals, missing proof, duplicate operations, privacy leaks,
and size-limit violations.

Pure offline, standard-library only.  No I/O beyond the CLI entry point.
"""

import hashlib
import json
import math
import re
import sys

# ---------------------------------------------------------------------------
# Private-path patterns that must never appear in a public projection
# ---------------------------------------------------------------------------

_PRIVATE_PATTERNS = [
    re.compile(r"/home/[a-zA-Z0-9_]+/\.ssh", re.IGNORECASE),
    re.compile(r"/home/[a-zA-Z0-9_]+/\.gnupg", re.IGNORECASE),
    re.compile(r"/home/[a-zA-Z0-9_]+/\.config/", re.IGNORECASE),
    re.compile(r"/root/", re.IGNORECASE),
    re.compile(r"/etc/shadow", re.IGNORECASE),
    re.compile(r"/etc/passwd", re.IGNORECASE),
    re.compile(r"private-mesa", re.IGNORECASE),
    re.compile(r"no-publicar", re.IGNORECASE),
    re.compile(r"credencial", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"api[_\-]?key", re.IGNORECASE),
]

_SENSITIVE_FIELDS = frozenset([
    "password", "secret", "token", "api_key", "apikey", "api-key",
    "credential", "credencial", "private_key", "private-key",
    "ssh_key", "ssh-key", "gnupg", "gpg_key",
])

_VERIFIED_STATUSES = frozenset([
    "VERIFIED", "VALIDO", "TESTED", "LIVE_SERVICE", "END_TO_END_VERIFIED",
])

_NO_DATA_STATUSES = frozenset(["NO_DATA", ""])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _norm(s):
    """Normalize a status string for comparison."""
    if not isinstance(s, str):
        return ""
    return s.strip().upper()


def _has_private_path(value):
    """Return True if *value* contains a private-path pattern."""
    if not isinstance(value, str):
        return False
    return any(p.search(value) for p in _PRIVATE_PATTERNS)


def _scan_private(value, _path=""):
    """Recursively collect privacy-leak descriptions."""
    leaks = []
    if isinstance(value, str):
        if _has_private_path(value):
            leaks.append(value[:80])
    elif isinstance(value, dict):
        for k, v in value.items():
            if isinstance(k, str) and k.lower() in _SENSITIVE_FIELDS:
                leaks.append("sensitive_field:" + k)
            leaks.extend(_scan_private(v, k))
    elif isinstance(value, (list, tuple)):
        for item in value:
            leaks.extend(_scan_private(item))
    return leaks


def _fingerprint(record):
    """Deterministic fingerprint for deduplication."""
    key_fields = ("task_id", "nodo", "node", "operation", "secuencia", "sequence")
    parts = []
    for f in key_fields:
        if f in record:
            parts.append(str(record[f]))
    if not parts:
        sanitized = {k: v for k, v in record.items()
                     if k not in ("timestamp", "medido_en", "emitido", "caduca")}
        raw = json.dumps(sanitized, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _ok(val):
    """Normalize ok/success to bool or None."""
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return None


# ---------------------------------------------------------------------------
# Case A  –  Unknown evidence
# ---------------------------------------------------------------------------

def case_a(record):
    """Reject interpretations that claim VERIFIED when estado is NO_DATA."""

    if not isinstance(record, dict):
        return {"state": "NO_DATA", "cause": "case_a requires a dict"}

    estado = _norm(record.get("estado"))
    interpretation = _norm(record.get("interpretation"))
    evidence = record.get("evidence")

    if estado in _NO_DATA_STATUSES:
        if interpretation in _VERIFIED_STATUSES:
            if not evidence:
                return {
                    "state": "FAIL",
                    "case": "A",
                    "cause": "false_positive: interpretation claims " + interpretation +
                             " but estado is NO_DATA with no independent evidence",
                }
            return {
                "state": "PASS",
                "case": "A",
                "cause": "independent evidence provided despite NO_DATA declaration",
            }
        return {"state": "PASS", "case": "A", "cause": "no false interpretation for NO_DATA"}

    return {"state": "PASS", "case": "A", "cause": "estado is " + estado + "; not a NO_DATA case"}


# ---------------------------------------------------------------------------
# Case B  –  Wrong identity
# ---------------------------------------------------------------------------

def case_b(record):
    """Detect identity mismatches between declared node and external ID."""

    if not isinstance(record, dict):
        return {"state": "NO_DATA", "cause": "case_b requires a dict"}

    declared = record.get("nodo", "")
    ext_id = record.get("external_id", "")
    registry = record.get("id_registry", {})

    if not declared or not isinstance(declared, str):
        return {"state": "FAIL", "case": "B", "cause": "missing declared node identity"}
    if not ext_id or not isinstance(ext_id, str):
        return {"state": "FAIL", "case": "B", "cause": "missing external identifier"}
    if ext_id not in registry:
        return {"state": "FAIL", "case": "B", "cause": "external_id not in registry: " + ext_id}

    registered = registry[ext_id]
    if registered != declared:
        return {
            "state": "FAIL",
            "case": "B",
            "cause": "identity_mismatch: receipt declares '" + declared +
                     "' but external_id maps to '" + registered + "'",
        }

    return {"state": "PASS", "case": "B", "cause": "identity consistent: " + declared}


# ---------------------------------------------------------------------------
# Case C  –  Contradictory execution
# ---------------------------------------------------------------------------

def case_c(record):
    """Reject when ok=true but rc != 0 (or vice-versa)."""

    if not isinstance(record, dict):
        return {"state": "NO_DATA", "cause": "case_c requires a dict"}

    ok = _ok(record.get("ok", record.get("success")))
    rc_raw = record.get("rc", record.get("exit_code"))
    error_msg = record.get("error", "")

    if rc_raw is not None:
        try:
            rc = int(rc_raw)
        except (ValueError, TypeError):
            return {"state": "FAIL", "case": "C", "cause": "unparseable return code: " + str(rc_raw)}
    else:
        rc = None

    if ok is True and rc is not None and rc != 0:
        return {
            "state": "FAIL",
            "case": "C",
            "cause": "contradictory_execution: ok=true but rc=" + str(rc) +
                     (", error: " + str(error_msg)[:80] if error_msg else ""),
        }

    if ok is False and rc is not None and rc == 0:
        return {
            "state": "FAIL",
            "case": "C",
            "cause": "contradictory_execution: ok=false but rc=0",
        }

    if ok is True and error_msg and rc is None:
        return {
            "state": "FAIL",
            "case": "C",
            "cause": "contradictory_execution: ok=true but error present: " + str(error_msg)[:80],
        }

    return {"state": "PASS", "case": "C", "cause": "execution signals consistent"}


# ---------------------------------------------------------------------------
# Case D  –  Missing execution proof
# ---------------------------------------------------------------------------

def case_d(record):
    """Reject when a request has no valid completion receipt."""

    if not isinstance(record, dict):
        return {"state": "NO_DATA", "cause": "case_d requires a dict"}

    req_id = record.get("request_id", "")
    receipts = record.get("receipts", [])
    required = record.get("receipt_required", True)

    if not req_id or not isinstance(req_id, str):
        return {"state": "FAIL", "case": "D", "cause": "missing request_id"}
    if not required:
        return {"state": "PASS", "case": "D", "cause": "receipt not required"}
    if not receipts or not isinstance(receipts, list):
        return {"state": "FAIL", "case": "D", "cause": "no completion receipt for request: " + req_id}

    valid_statuses = frozenset(["VALIDO", "VERIFIED", "COMPLETED", "SUCCESS"])
    for r in receipts:
        if isinstance(r, dict):
            r_id = r.get("request_id", r.get("id", ""))
            r_status = _norm(r.get("estado", r.get("status", "")))
            if r_id == req_id and r_status in valid_statuses:
                return {"state": "PASS", "case": "D", "cause": "valid receipt for request: " + req_id}

    return {
        "state": "FAIL",
        "case": "D",
        "cause": "no valid completion receipt for request: " + req_id +
                 " (found " + str(len(receipts)) + " receipts, none valid)",
    }


# ---------------------------------------------------------------------------
# Case E  –  Duplicate operation
# ---------------------------------------------------------------------------

def case_e(record):
    """Detect duplicate task completions."""

    if not isinstance(record, dict):
        return {"state": "NO_DATA", "cause": "case_e requires a dict"}

    ops = record.get("operations", [])
    if not ops or not isinstance(ops, list):
        return {"state": "PASS", "case": "E", "cause": "no operations to check"}
    if len(ops) < 2:
        return {"state": "PASS", "case": "E", "cause": "single operation; no duplicate possible"}

    fps = []
    for op in ops:
        if isinstance(op, dict):
            fps.append(_fingerprint(op))

    seen = set()
    dups = 0
    for fp in fps:
        if fp in seen:
            dups += 1
        seen.add(fp)

    if dups:
        return {
            "state": "FAIL",
            "case": "E",
            "cause": "duplicate_operation: " + str(dups) +
                     " duplicate(s) among " + str(len(ops)) + " operations",
        }

    return {"state": "PASS", "case": "E", "cause": "no duplicates among " + str(len(ops)) + " operations"}


# ---------------------------------------------------------------------------
# Case F  –  Privacy boundary
# ---------------------------------------------------------------------------

def case_f(record):
    """Detect private paths or sensitive fields in public projections."""

    if not isinstance(record, dict):
        return {"state": "NO_DATA", "cause": "case_f requires a dict"}

    projection = record.get("public_projection", {})
    if not isinstance(projection, dict):
        projection = {"data": projection}

    leaks = _scan_private(projection)
    if leaks:
        return {
            "state": "FAIL",
            "case": "F",
            "cause": "privacy_leak: " + str(len(leaks)) +
                     " sensitive item(s): " + ", ".join(leaks[:5]),
        }

    return {"state": "PASS", "case": "F", "cause": "no privacy leaks in public projection"}


# ---------------------------------------------------------------------------
# Case G  –  Receipt limits
# ---------------------------------------------------------------------------

def case_g(record):
    """Reject when payload exceeds declared byte limit."""

    if not isinstance(record, dict):
        return {"state": "NO_DATA", "cause": "case_g requires a dict"}

    payload = record.get("payload", "")
    limit = record.get("declared_limit")
    encoding = record.get("encoding", "utf-8")

    if limit is None:
        return {"state": "PASS", "case": "G", "cause": "no declared limit"}

    try:
        limit = int(limit)
    except (ValueError, TypeError):
        return {"state": "FAIL", "case": "G", "cause": "unparseable declared_limit: " + str(limit)}

    if limit < 0:
        return {"state": "FAIL", "case": "G", "cause": "negative declared_limit: " + str(limit)}

    if isinstance(payload, dict):
        payload = json.dumps(payload, ensure_ascii=False)
    if not isinstance(payload, str):
        payload = str(payload)

    size = len(payload.encode(encoding))
    if size > limit:
        return {
            "state": "FAIL",
            "case": "G",
            "cause": "size_exceeded: " + str(size) + " bytes > " + str(limit) + " byte limit",
        }

    return {"state": "PASS", "case": "G", "cause": str(size) + " bytes within " + str(limit) + " byte limit"}


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_CASE_MAP = {
    "A": case_a, "B": case_b, "C": case_c, "D": case_d,
    "E": case_e, "F": case_f, "G": case_g,
}


def judge(case_id, record):
    """Run the named adversarial case on *record*."""
    fn = _CASE_MAP.get(case_id.upper())
    if fn is None:
        return {"state": "NO_DATA", "cause": "unknown case: " + str(case_id)}
    return fn(record)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 2:
        print("usage: judge_adversarial.py FILE.json", file=sys.stderr)
        return 1
    try:
        with open(sys.argv[1], encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"state": "NO_DATA", "cause": str(exc)}))
        return 1

    if isinstance(data, dict) and "case" in data and "record" in data:
        result = judge(data["case"], data["record"])
    elif isinstance(data, list):
        results = []
        for item in data:
            if isinstance(item, dict) and "case" in item and "record" in item:
                results.append(judge(item["case"], item["record"]))
            else:
                results.append({"state": "NO_DATA", "cause": "item missing case or record"})
        result = {"results": results}
    else:
        result = {"state": "NO_DATA", "cause": "input must be {case, record} or [{case, record}, ...]"}

    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("state") == "PASS" else (1 if result.get("state") == "FAIL" else 2)


if __name__ == "__main__":
    sys.exit(main())
