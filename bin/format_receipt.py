#!/usr/bin/env python3
"""Format a measured receipt into a privacy-safe ~150-word plain-text log.

The receipt is the post (ideas20oct §2): silicon drafts from measured
figures only; the Sovereign reviews, signs (FIRMO), and publishes.
Usage:
  python3 bin/format_receipt.py RECEIPT.json [--words 150]
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

CEILING_WORDS = 150


def _first_sentence(text: str, limit: int = 400) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def format_harness_receipt(r: dict) -> str:
    suite = r.get("suite", "NO_DATA")
    verdict = r.get("verdict", "NO_DATA")
    cov = r.get("coverage", 0)
    total = r.get("total", 0)
    det = r.get("determinism", False)
    weight = r.get("weight_b", 0)
    speed = r.get("speed_s", 0)
    sha = r.get("sha256", "NO_DATA")
    machine = r.get("runtime", {}).get("machine", "NO_DATA")
    date = r.get("observed_at", "NO_DATA")
    py = r.get("runtime", {}).get("python", "NO_DATA")
    det_txt = "deterministic across both runs" if det else "NOT deterministic"
    return (
        f"Harness receipt · {suite} · verdict {verdict} · {date}. "
        f"Coverage {cov}/{total} tests passed. {det_txt}. "
        f"Weight {weight} B. Runtime {speed} s per pass. "
        f"Machine {machine} · Python {py}. "
        f"Schema {r.get('schema', 'NO_DATA')}. "
        f"Receipt sha256 {sha}. "
        f"Privacy: counts only; no test names, no output, no prompts. "
        f"Drafted by silicon from measured figures; pending Sovereign sign-off (FIRMO)."
    )


def format_yardstick_receipt(r: dict) -> str:
    state = r.get("state", "NO_DATA")
    runs = r.get("runs", [])
    date = r.get("observed_at", "NO_DATA")
    cmd = r.get("command", "NO_DATA")
    machine = r.get("runtime", {}).get("machine", "NO_DATA")
    py = r.get("runtime", {}).get("python", "NO_DATA")
    parts = []
    for i, run in enumerate(runs):
        parts.append(
            f"run {i + 1}: {run.get('state', 'NO_DATA')} "
            f"{run.get('passed', 0)}/{run.get('tests', 0)} passed "
            f"in {run.get('elapsed_s', 0)} s"
        )
    runs_txt = "; ".join(parts) if parts else "NO_DATA"
    cause = r.get("cause")
    cause_txt = f" Cause: {cause}." if cause else ""
    return (
        f"Yardstick receipt · state {state} · {date}. "
        f"Command: {cmd}. {runs_txt}.{cause_txt} "
        f"Machine {machine} · Python {py}. "
        f"Schema {r.get('schema', 'NO_DATA')}. "
        f"Privacy: counts only; test names, stdout, stderr, prompts and answers omitted. "
        f"Drafted by silicon from measured figures; pending Sovereign sign-off (FIRMO)."
    )


def format_receipt(path: str) -> str:
    r = json.loads(Path(path).read_text(encoding="utf-8"))
    schema = r.get("schema", "")
    if "harness-receipt" in schema:
        return format_harness_receipt(r)
    if "yardstick-receipt" in schema:
        return format_yardstick_receipt(r)
    return (
        f"Receipt · schema {schema or 'NO_DATA'} · observed {r.get('observed_at', 'NO_DATA')}. "
        f"State {r.get('state', r.get('verdict', 'NO_DATA'))}. "
        f"Drafted by silicon; pending Sovereign sign-off (FIRMO)."
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("receipt", help="path to a JSON receipt")
    ap.add_argument("--words", type=int, default=CEILING_WORDS,
                    help="soft ceiling for the drafted log (default 150)")
    args = ap.parse_args(argv)
    text = format_receipt(args.receipt)
    words = len(text.split())
    print(text)
    print(f"\n---\nwords: {words} (soft ceiling {args.words})", file=__import__("sys").stderr)
    return 0 if words <= args.words * 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
