#!/usr/bin/env python3
"""DFA-B4 local serialization-to-receiver clock, no network or trust claims."""
import argparse
import json
import math
from pathlib import Path
import sys
import time

from dfa06_evidence_bundle import build, encode, verify

SCHEMA = "preceptoros.lab.dfa-b4-offline/1"


def single(payload, clock=None, mutate=None):
    clock = clock or time.perf_counter_ns
    started = clock()
    envelope = build(payload)
    wire = encode(envelope)
    received = json.loads(wire)
    if mutate is not None:
        mutate(received)
    proof = verify(received)
    elapsed = clock() - started
    if type(elapsed) is not int or elapsed < 0:
        raise ValueError("nonmonotonic_clock")
    return {"state": proof["state"], "elapsed_ns": elapsed,
            "package_bytes": len(wire), "cause": proof.get("cause")}


def measure(payload, trials=5, clock=None):
    if type(trials) is not int or not 1 <= trials <= 100:
        raise ValueError("trial_count_out_of_range")
    readings = [single(payload, clock=clock) for _ in range(trials)]
    good = [r["elapsed_ns"] for r in readings if r["state"] == "VERIFIED_BYTES"]
    bad = len(readings) - len(good)
    good.sort()
    return {
        "schema": SCHEMA,
        "state": "OFFLINE_BYTES_VERIFIED" if good and not bad else "NO_DATA",
        "cause": "offline_only_no_remote_receiver",
        "trials": trials,
        "verified_bytes": len(good),
        "failed": bad,
        "package_bytes": readings[0]["package_bytes"],
        "latency_ms": {
            "p50": round(good[math.ceil(len(good) * .50) - 1] / 1e6, 3),
            "p90": round(good[math.ceil(len(good) * .90) - 1] / 1e6, 3),
        } if good else None,
        "threshold_evaluation": "NO_DATA: local_memory_transfer_not_network",
        "source_attestation": "NO_DATA: underlying_artifact_unverified",
        "signature_attestation": "NO_DATA: signing_not_performed",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("synthetic_manifest")
    p.add_argument("--trials", type=int, default=5)
    args = p.parse_args()
    try:
        with open(args.synthetic_manifest, encoding="utf-8") as f:
            result = measure(json.load(f), args.trials)
        code = 0 if result["state"] == "OFFLINE_BYTES_VERIFIED" else 1
    except (OSError, ValueError, TypeError) as exc:
        result = {"state": "NO_DATA", "cause": type(exc).__name__}
        code = 2
    print(encode(result).decode("utf-8"))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
