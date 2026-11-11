#!/usr/bin/env python3
"""F6-01: local synthetic A2A exchange envelope; not a live testnet."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import runpy

ASSESS = runpy.run_path(str(Path(__file__).with_name("f6_economic_probes.py")))["assess"]
SCHEMA = "preceptoros.lab.f6-synthetic-exchange/1"
IDENT = re.compile(r"[a-z][a-z0-9_-]{0,47}\Z")


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def exchange(message):
    if not isinstance(message, dict) or set(message) != {
            "schema", "message_id", "sender", "recipient", "probe"}:
        raise ValueError("closed_message_required")
    if message["schema"] != SCHEMA:
        raise ValueError("invalid_schema")
    if any(not isinstance(message[field], str) or not IDENT.fullmatch(message[field])
           for field in ("message_id", "sender", "recipient")):
        raise ValueError("invalid_pseudonym_or_id")
    if message["sender"] == message["recipient"]:
        raise ValueError("sender_must_differ_from_receiver")
    if len(_canonical(message)) > 4096:
        raise ValueError("message_byte_ceiling")
    # The only judge is the existing F6 fixture implementation. Never duplicate its rules.
    decision = ASSESS(message["probe"])
    return {"schema": "preceptoros.lab.f6-exchange-receipt/1",
            "message_id": message["message_id"],
            "message_sha256": hashlib.sha256(_canonical(message)).hexdigest(),
            "kind": decision["kind"],
            "verdict": decision["verdict"],
            "cause": decision["cause"],
            "scope": "SYNTHETIC_ONLY",
            "authority": "NONE",
            "signature": "NO_DATA: signature_not_verified",
            "transport": "NO_DATA: offline_no_network"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("synthetic_request_file")
    args = parser.parse_args()
    try:
        with open(args.synthetic_request_file, encoding="utf-8") as stream:
            decision = exchange(json.load(stream))
        code = 0
    except (ValueError, OSError, TypeError, OverflowError) as exc:
        decision = {"state": "NO_DATA", "cause": type(exc).__name__}
        code = 2
    print(_canonical(decision).decode("utf-8"))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
