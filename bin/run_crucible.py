#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "bin" / "verify_llms_tree.py"
PROBES = {
    "P4": (
        "INDEX: README.md\nDEPTH: 0\nBUDGET: 1\n",
        "over depth budget: INDEX totals 18 B > 1 B",
    ),
    "P5": (
        "INDEX: README.md; absent.md\nDEPTH: 1\nBUDGET: 1024\n",
        "missing or outside tree: absent.md",
    ),
}


def invoke_verifier(root: Path) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(VERIFIER), "--root", str(root)],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip()


def run_probe(probe: str) -> dict:
    index, expected = PROBES[probe]
    readme = "Measured fixture.\n"
    digest = hashlib.sha256((index + readme).encode("utf-8")).hexdigest()
    with tempfile.TemporaryDirectory(prefix="lab-crucible-") as temp:
        root = Path(temp)
        (root / "llms.txt").write_text(index, encoding="utf-8")
        (root / "README.md").write_text(readme, encoding="utf-8")
        returncode, output = invoke_verifier(root)
    detected = returncode != 0 and expected in output
    cause = None if detected else (
        "guardian accepted adversarial input" if returncode == 0
        else "guardian failed for an unexpected reason"
    )
    return {
        "schema": "preceptoros.lab.crucible-receipt/1",
        "probe": probe,
        "state": "SIMULATED" if detected else "RED",
        "detected": detected,
        "probes": 1,
        "machine": platform.machine() or "NO_DATA",
        "date_utc": dt.datetime.now(dt.timezone.utc).date().isoformat(),
        "command": f"python3 bin/run_crucible.py --probe {probe}",
        "fixture_sha256": digest,
        **({"cause": cause} if cause else {}),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", choices=tuple(PROBES), required=True)
    args = parser.parse_args(argv)
    receipt = run_probe(args.probe)
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
    print(encoded)
    if len(encoded.encode("utf-8")) >= 1024:
        return 2
    return 0 if receipt["detected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
