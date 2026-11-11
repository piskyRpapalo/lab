#!/usr/bin/env python3
"""DFA-B7 pilot: scoped, offline red-before-green mutations of existing F6 probes."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = (
    ("reach_boundary", 'f["claimed_reach"]>len(set(hashes))',
     'f["claimed_reach"]>=len(set(hashes))'),
    ("budget_boundary", 'f["promised_j"]>f["available_j"]',
     'f["promised_j"]>=f["available_j"]'),
    ("arbitration_role", 'f["role"]!="sovereign"',
     'f["role"]=="sovereign"'),
)
SOURCE = ROOT / "bin" / "f6_economic_probes.py"
TESTS = ("test_f6_economic_probes.py", "test_f6_economic_edges.py")


def _run(source_code):
    with tempfile.TemporaryDirectory(prefix="dfa_b7_pilot_") as dirname:
        tmp = Path(dirname)
        (tmp / "bin").mkdir()
        (tmp / "tests").mkdir()
        (tmp / "bin" / "f6_economic_probes.py").write_text(source_code, encoding="utf-8")
        for name in TESTS:
            (tmp / "tests" / name).write_bytes((ROOT / "tests" / name).read_bytes())
        args = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests",
                "-p", "test_f6_economic*.py"]
        p = subprocess.run(args, cwd=tmp, capture_output=True, text=True,
                           timeout=15, check=False)
        return p.returncode == 0


def pilot():
    original = SOURCE.read_text(encoding="utf-8")
    if not _run(original):
        return {"state": "NO_DATA", "cause": "original_suite_not_green"}
    results = []
    for name, before, after in MUTANTS:
        if original.count(before) != 1:
            return {"state": "NO_DATA", "cause": "mutation_anchor_mismatch"}
        mutant = original.replace(before, after, 1)
        results.append({"id": name, "killed": not _run(mutant)})
    killed = sum(x["killed"] for x in results)
    return {"schema": "preceptoros.lab.dfa-b7-mutation-pilot/1",
            "state": "MEASURED_SCOPED", "scope": "F6_FIXTURES_ONLY",
            "baseline": "GREEN", "killed": killed, "mutants": len(MUTANTS),
            "mutation_ratio": [killed, len(MUTANTS)], "details": results,
            "suite_at_large": "NO_DATA: dfa_family_not_yet_runnable"}


def main():
    result = pilot()
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["state"] == "MEASURED_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
