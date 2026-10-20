#!/usr/bin/env python3
"""Evaluate a test harness: coverage, determinism, weight, speed. Emit a receipt < 1,024 B.

preceptoros.lab.harness-receipt/1 · pure stdlib · privacy-safe (counts only).
Usage:
  python3 bin/eval_harness.py --suite tests --pattern 'test_*.py' [--runs 2] [--timeout 300]
  python3 bin/eval_harness.py --compare RECEIPT_A.json RECEIPT_B.json
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

SCHEMA = "preceptoros.lab.harness-receipt/1"
CEILING = 1024
SUMMARY = re.compile(r"Ran (\d+) tests? in ([0-9.]+)s")
SKIPPED = re.compile(r"skipped=(\d+)")
FAILURES = re.compile(r"failures=(\d+)")
ERRORS = re.compile(r"errors=(\d+)")


def _run_once(suite: str, pattern: str, timeout: int) -> dict:
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", suite, "-p", pattern]
    t0 = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = proc.stdout + proc.stderr
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        return {"state": "NO_DATA", "cause": "timeout", "elapsed_s": timeout}
    elapsed = round(time.monotonic() - t0, 3)
    m = SUMMARY.search(out)
    if not m:
        return {"state": "NO_DATA", "cause": "unittest summary missing", "elapsed_s": elapsed}
    tests = int(m.group(1))
    sk = SKIPPED.search(out)
    fa = FAILURES.search(out)
    er = ERRORS.search(out)
    skipped = int(sk.group(1)) if sk else 0
    failures = int(fa.group(1)) if fa else 0
    errors = int(er.group(1)) if er else 0
    passed = tests - skipped - failures - errors
    if tests == 0:
        state, cause = "NO_DATA", "zero tests discovered"
    elif rc != 0 or failures or errors:
        state, cause = "RED", None
    else:
        state, cause = "GREEN", None
    return {"state": state, "cause": cause, "tests": tests, "passed": passed,
            "skipped": skipped, "failures": failures, "errors": errors,
            "elapsed_s": elapsed}


def _weight_bytes(suite: str, pattern: str) -> int:
    root = Path(suite)
    if not root.is_dir():
        return 0
    total = 0
    for p in sorted(root.rglob(pattern.replace("*", "*"))):
        if p.is_file():
            total += p.stat().st_size
    return total


def evaluate(suite: str, pattern: str, runs: int, timeout: int) -> dict:
    runs_out = [_run_once(suite, pattern, timeout) for _ in range(max(1, runs))]
    states = [r["state"] for r in runs_out]
    determinism = all(r.get("tests") == runs_out[0].get("tests") for r in runs_out) \
        and all(r.get("passed") == runs_out[0].get("passed") for r in runs_out)
    coverage = runs_out[0].get("passed", 0)
    total = runs_out[0].get("tests", 0)
    speed = round(runs_out[0].get("elapsed_s", 0), 3)
    weight = _weight_bytes(suite, pattern)
    if "RED" in states:
        verdict = "RED"
    elif "NO_DATA" in states:
        verdict = "NO_DATA"
    elif determinism:
        verdict = "GREEN"
    else:
        verdict = "WHEN"
    receipt = {
        "schema": SCHEMA,
        "suite": suite,
        "observed_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runtime": {"machine": platform.machine(), "python": platform.python_version(),
                    "system": platform.system()},
        "runs": runs_out,
        "coverage": coverage,
        "total": total,
        "determinism": determinism,
        "weight_b": weight,
        "speed_s": speed,
        "verdict": verdict,
    }
    return receipt


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def attach_hash(receipt: dict) -> dict:
    body = {k: v for k, v in receipt.items() if k != "sha256"}
    receipt["sha256"] = hashlib.sha256(_canon(body).encode()).hexdigest()[:16]
    return receipt


def check_ceiling(receipt: dict) -> tuple[bool, int]:
    blob = _canon(receipt).encode()
    return len(blob) < CEILING, len(blob)


def compare(a_path: str, b_path: str) -> dict:
    a = json.loads(Path(a_path).read_text())
    b = json.loads(Path(b_path).read_text())
    def score(r):
        if r.get("verdict") != "GREEN":
            return -1
        cov = r.get("coverage", 0)
        det = 1 if r.get("determinism") else 0
        w = r.get("weight_b", 0)
        s = r.get("speed_s", 0)
        return cov * 1000 + det * 100 - (w // 1024) - (int(s * 10) if s else 0)
    sa, sb = score(a), score(b)
    if sa > sb:
        winner = "A"
    elif sb > sa:
        winner = "B"
    else:
        winner = "TIE"
    return {"schema": SCHEMA + ".compare", "a": a.get("suite"), "b": b.get("suite"),
            "score_a": sa, "score_b": sb, "winner": winner,
            "verdict_a": a.get("verdict"), "verdict_b": b.get("verdict")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--suite", default="tests")
    ap.add_argument("--pattern", default="test_*.py")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--compare", nargs=2, metavar=("A.json", "B.json"))
    args = ap.parse_args(argv)

    if args.compare:
        result = compare(args.compare[0], args.compare[1])
        blob = _canon(result)
        print(blob)
        return 0 if result["winner"] != "NO_DATA" else 1

    receipt = attach_hash(evaluate(args.suite, args.pattern, args.runs, args.timeout))
    ok, size = check_ceiling(receipt)
    if not ok:
        receipt["verdict"] = "NO_DATA"
        receipt["cause"] = f"receipt over ceiling: {size} B >= {CEILING} B"
    blob = _canon(receipt)
    if args.output:
        args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(blob)
    if receipt["verdict"] == "GREEN" and ok:
        return 0
    if receipt["verdict"] == "RED":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
