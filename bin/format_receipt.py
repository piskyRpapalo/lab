#!/usr/bin/env python3
"""Format a measured receipt into a privacy-safe ~150-word plain-text log.

The receipt is the post (ideas20oct §2): silicon drafts from measured
figures only; the Sovereign reviews, signs (FIRMO), and publishes.
Usage:
  python3 bin/format_receipt.py RECEIPT.json [--words 150]
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path

CEILING_WORDS = 150


def _enum(value, allowed):
    return value if type(value) is str and value in allowed else 'NO_DATA'


def _number(value):
    return value if type(value) in (int, float) and 0 <= value <= 10**12 and math.isfinite(value) else 'NO_DATA'


def _verified_harness_hash(r):
    claimed = r.get('sha256')
    if type(claimed) is not str or not re.fullmatch(r'[0-9a-f]{16}', claimed):
        return 'NO_DATA'
    try:
        body = {k: v for k, v in r.items() if k != 'sha256'}
        canonical = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        actual = hashlib.sha256(canonical.encode()).hexdigest()[:16]
        return actual if actual == claimed else 'NO_DATA'
    except (TypeError, ValueError, RecursionError):
        return 'NO_DATA'


def _date(value):
    if type(value) is not str or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', value):
        return 'NO_DATA'
    try:
        datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        return value
    except ValueError:
        return 'NO_DATA'


def _runtime(r):
    runtime = r.get('runtime') if type(r.get('runtime')) is dict else {}
    machine = _enum(runtime.get('machine'), {'x86_64', 'aarch64', 'arm64', 'AMD64'})
    py = runtime.get('python')
    py = py if type(py) is str and re.fullmatch(r'\d{1,2}\.\d{1,2}\.\d{1,3}', py) else 'NO_DATA'
    return machine, py


def _first_sentence(text: str, limit: int = 400) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def format_harness_receipt(r: dict) -> str:
    if type(r) is not dict or r.get('schema') != 'preceptoros.lab.harness-receipt/1':
        return 'Receipt · schema NO_DATA. Drafted by silicon; pending Sovereign sign-off (FIRMO).'
    suite = _enum(r.get('suite'), {'tests'})
    verdict = _enum(r.get('verdict'), {'GREEN', 'RED', 'WHEN', 'NO_DATA'})
    cov, total = _number(r.get('coverage')), _number(r.get('total'))
    det = r.get('determinism')
    weight, speed = _number(r.get('weight_b')), _number(r.get('speed_s'))
    sha = _verified_harness_hash(r)
    machine, py = _runtime(r)
    date = _date(r.get('observed_at'))
    det_txt = 'deterministic across both runs' if det is True else 'NOT deterministic' if det is False else 'determinism NO_DATA'
    return (
        f"Harness receipt · {suite} · verdict {verdict} · {date}. "
        f"Coverage {cov}/{total} tests passed. {det_txt}. "
        f"Weight {weight} B. Runtime {speed} s per pass. "
        f"Machine {machine} · Python {py}. "
        f"Schema preceptoros.lab.harness-receipt/1. "
        f"Receipt sha256 {sha}. "
        f"Privacy: counts only; no test names, no output, no prompts. "
        f"Source-reported draft; authenticity not established; pending Sovereign sign-off (FIRMO)."
    )


def format_yardstick_receipt(r: dict) -> str:
    if type(r) is not dict or r.get('schema') != 'preceptoros.lab.yardstick-receipt/1':
        return 'Receipt · schema NO_DATA. Drafted by silicon; pending Sovereign sign-off (FIRMO).'
    state = _enum(r.get('state'), {'GREEN', 'RED', 'NO_DATA'})
    runs = r.get('runs') if type(r.get('runs')) is list and len(r['runs']) <= 8 else []
    date = _date(r.get('observed_at'))
    cmd = _enum(r.get('command'), {'python3 -m unittest discover -s tests',
                                  "python3 -m unittest discover -s tests -p 'test_*.py'"})
    machine, py = _runtime(r)
    parts = []
    for i, run in enumerate(runs):
        if type(run) is not dict:
            continue
        cause = _enum(run.get('cause'), {'unittest summary missing', 'yardstick discovered zero tests',
                                         'unittest reported a nonzero exit or failures', 'yardstick timeout'})
        parts.append(
            f"run {i + 1}: {_enum(run.get('state'), {'GREEN', 'RED', 'NO_DATA'})} "
            f"{_number(run.get('passed'))}/{_number(run.get('tests'))} passed "
            f"in {_number(run.get('elapsed_s'))} s" + (f" (cause: {cause})" if run.get('cause') else '')
        )
    runs_txt = "; ".join(parts) if parts else "NO_DATA"
    cause_txt = ' Cause: NO_DATA.' if r.get('cause') is not None else ''
    return (
        f"Yardstick receipt · state {state} · {date}. "
        f"Command: {cmd}. {runs_txt}.{cause_txt} "
        f"Machine {machine} · Python {py}. "
        f"Schema preceptoros.lab.yardstick-receipt/1. "
        f"Privacy: counts only; test names, stdout, stderr, prompts and answers omitted. "
        f"Source-reported draft; authenticity not established; pending Sovereign sign-off (FIRMO)."
    )


def format_receipt(path: str) -> str:
    raw = Path(path).read_bytes()
    if len(raw) >= 16384:
        raise ValueError('receipt_limit')
    r = json.loads(raw)
    if type(r) is not dict:
        raise ValueError('receipt_shape')
    schema = r.get("schema", "")
    if schema == 'preceptoros.lab.harness-receipt/1':
        return format_harness_receipt(r)
    if schema == 'preceptoros.lab.yardstick-receipt/1':
        return format_yardstick_receipt(r)
    return (
        f"Receipt · schema NO_DATA · observed {_date(r.get('observed_at'))}. "
        f"State NO_DATA. "
        f"Drafted by silicon; pending Sovereign sign-off (FIRMO)."
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("receipt", help="path to a JSON receipt")
    ap.add_argument("--words", type=int, default=CEILING_WORDS,
                    help="soft ceiling for the drafted log (default 150)")
    args = ap.parse_args(argv)
    try:
        text = format_receipt(args.receipt)
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
        print('NO_DATA(receipt_unavailable_or_invalid)')
        return 1
    words = len(text.split())
    print(text)
    print(f"\n---\nwords: {words} (soft ceiling {args.words})", file=__import__("sys").stderr)
    return 0 if words <= args.words * 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
