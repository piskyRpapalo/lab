#!/usr/bin/env python3
"""DFA-06 synthetic offline evidence envelope; validates bytes, never source truth."""
import argparse
import hashlib
import json
import re
from datetime import datetime

SCHEMA = "preceptoros.lab.dfa06-evidence/1"
ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,95}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
CAUSE = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
MAX_BYTES = 16384


def encode(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def valid_time(value):
    if not isinstance(value, str) or not re.fullmatch(
            r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", value):
        raise ValueError("utc_timestamp_required")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_timestamp") from exc
    return value


def validate_payload(payload):
    if not isinstance(payload, dict) or set(payload) != {"request_id", "observed_at", "artifacts"}:
        raise ValueError("closed_payload_required")
    if not isinstance(payload["request_id"], str) or not ID.fullmatch(payload["request_id"]):
        raise ValueError("invalid_request_id")
    valid_time(payload["observed_at"])
    items = payload["artifacts"]
    if not isinstance(items, list) or not 1 <= len(items) <= 16:
        raise ValueError("artifact_count_out_of_range")
    seen = set()
    for item in items:
        if not isinstance(item, dict) or set(item) - {"id", "sha256", "state", "cause"}:
            raise ValueError("closed_artifact_required")
        if not isinstance(item.get("id"), str) or not ID.fullmatch(item["id"]):
            raise ValueError("invalid_artifact_id")
        if item["id"] in seen:
            raise ValueError("duplicate_artifact_id")
        seen.add(item["id"])
        if not isinstance(item.get("sha256"), str) or not DIGEST.fullmatch(item["sha256"]):
            raise ValueError("invalid_artifact_digest")
        if item.get("state") == "MEASURED":
            if set(item) != {"id", "sha256", "state"}:
                raise ValueError("measured_artifact_has_cause")
        elif item.get("state") == "NO_DATA":
            if set(item) != {"id", "sha256", "state", "cause"} or not isinstance(
                    item["cause"], str) or not CAUSE.fullmatch(item["cause"]):
                raise ValueError("no_data_requires_cause")
        else:
            raise ValueError("unsupported_artifact_state")
    return payload


def build(payload):
    validate_payload(payload)
    copy = json.loads(encode(payload))
    envelope = {"schema": SCHEMA, "payload": copy,
                "payload_sha256": hashlib.sha256(encode(copy)).hexdigest(),
                "seal": "NO_DATA: signature_not_performed"}
    if len(encode(envelope)) >= MAX_BYTES:
        raise ValueError("package_byte_ceiling")
    return envelope


def verify(envelope):
    try:
        if not isinstance(envelope, dict) or set(envelope) != {
                "schema", "payload", "payload_sha256", "seal"}:
            raise ValueError("closed_envelope_required")
        if envelope["schema"] != SCHEMA or envelope["seal"] != "NO_DATA: signature_not_performed":
            raise ValueError("unknown_schema_or_seal")
        validate_payload(envelope["payload"])
        if len(encode(envelope)) >= MAX_BYTES:
            raise ValueError("package_byte_ceiling")
        digest = envelope["payload_sha256"]
        if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
            raise ValueError("digest_invalid")
        if hashlib.sha256(encode(envelope["payload"])).hexdigest() != digest:
            raise ValueError("payload_digest_mismatch")
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        return {"state": "FAIL", "cause": str(exc)}
    return {"state": "VERIFIED_BYTES",
            "source_attestation": "NO_DATA: source_artifacts_not_independently_verified",
            "signature_attestation": "NO_DATA: signature_not_performed",
            "package_bytes": len(encode(envelope))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify"))
    parser.add_argument("json_file")
    args = parser.parse_args()
    try:
        with open(args.json_file, encoding="utf-8") as stream:
            value = json.load(stream)
        result = build(value) if args.action == "build" else verify(value)
    except (OSError, ValueError, TypeError) as exc:
        result = {"state": "NO_DATA", "cause": type(exc).__name__}
    print(encode(result).decode("utf-8"))
    return 1 if result.get("state") in {"NO_DATA", "FAIL"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
