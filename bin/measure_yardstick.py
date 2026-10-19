#!/usr/bin/env python3
"""Run the canonical LAB yardstick twice and emit a privacy-safe receipt."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import re
import subprocess
import sys
import time
from pathlib import Path


SCHEMA = "preceptoros.lab.yardstick-receipt/1"
DISPLAY_COMMAND = "python3 -m unittest discover -s tests -p 'test_*.py'"
UNITTEST_ARGS = ["-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
SUMMARY = re.compile(r"Ran (\d+) tests? in ([0-9.]+)s")
SKIPPED = re.compile(r"skipped=(\d+)")
FAILURES = re.compile(r"failures=(\d+)")
ERRORS = re.compile(r"errors=(\d+)")


def summarize(returncode: int, output: str, elapsed_s: float) -> dict:
    """Keep counts and outcome only; never persist test names or test output."""
    summary = SUMMARY.search(output)
    if summary is None:
        return {"state": "NO_DATA", "cause": "unittest summary missing",
                "elapsed_s": round(elapsed_s, 3)}
    tests = int(summary.group(1))
    skipped_match = SKIPPED.search(output)
    failures_match = FAILURES.search(output)
    errors_match = ERRORS.search(output)
    skipped = int(skipped_match.group(1)) if skipped_match else 0
    failures = int(failures_match.group(1)) if failures_match else 0
    errors = int(errors_match.group(1)) if errors_match else 0
    if tests == 0:
        state, cause = "NO_DATA", "yardstick discovered zero tests"
    elif returncode != 0 or failures or errors:
        state, cause = "RED", "unittest reported a nonzero exit or failures"
    else:
        state, cause = "GREEN", None
    return {"state": state, "tests": tests, "skipped": skipped,
            "failures": failures, "errors": errors,
            "passed": max(0, tests - skipped - failures - errors),
            "elapsed_s": round(elapsed_s, 3), "cause": cause}


def commit_id() -> str | None:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], check=True,
                                capture_output=True, text=True, timeout=2)
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    return value if re.fullmatch(r"[0-9a-f]{40,64}", value) else None


def tracked_tree_clean() -> bool | None:
    try:
        result = subprocess.run(["git", "diff", "--quiet", "HEAD", "--"],
                                timeout=2, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def run_once(timeout_s: float) -> dict:
    started = time.monotonic()
    try:
        result = subprocess.run([sys.executable, *UNITTEST_ARGS], capture_output=True,
                                text=True, timeout=timeout_s, check=False)
    except subprocess.TimeoutExpired:
        return {"state": "NO_DATA", "cause": "yardstick timeout",
                "elapsed_s": round(time.monotonic() - started, 3)}
    except OSError as error:
        return {"state": "NO_DATA", "cause": f"runner unavailable ({type(error).__name__})",
                "elapsed_s": round(time.monotonic() - started, 3)}
    return summarize(result.returncode, result.stdout + "\n" + result.stderr,
                     time.monotonic() - started)


def receipt(timeout_s: float = 300) -> dict:
    runs = [run_once(timeout_s), run_once(timeout_s)]
    state = "GREEN" if all(run["state"] == "GREEN" for run in runs) else "RED"
    if any(run["state"] == "NO_DATA" for run in runs):
        state = "NO_DATA"
    return {
        "schema": SCHEMA,
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "state": state,
        "command": DISPLAY_COMMAND,
        "runs": runs,
        "source_commit": commit_id() or "NO_DATA: not in a git worktree",
        "source_tracked_tree_clean": tracked_tree_clean(),
        "runtime": {"python": platform.python_version(),
                    "system": platform.system(), "machine": platform.machine()},
        "timeout_s_per_run": timeout_s,
        "privacy": "counts only; test names, stdout, stderr, prompts and answers omitted",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Measure the LAB yardstick twice")
    parser.add_argument("--timeout-seconds", type=float, default=300)
    parser.add_argument("--output", type=Path, help="optional path for the JSON receipt")
    args = parser.parse_args(argv)
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    payload = json.dumps(receipt(args.timeout_seconds), ensure_ascii=False,
                         sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0 if json.loads(payload)["state"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
