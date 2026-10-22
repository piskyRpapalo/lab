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
READING_PROBES = {
    "P4": (
        "INDEX: README.md\nDEPTH: 0\nBUDGET: 1\n",
        "over depth budget: INDEX totals 18 B > 1 B",
    ),
    "P5": (
        "INDEX: README.md; absent.md\nDEPTH: 1\nBUDGET: 1024\n",
        "missing or outside tree: absent.md",
    ),
}


UNWIRED_PROBES = {
    "P1": ("state packet with undeclared field", "reject the whole packet", "APP contract guardian is not wired"),
    "P2": ("many unsigned tray proposals", "measure requested and given signatures", "tray counters are not available here"),
    "P3": ("out-of-doctrine text sent for sign-off", "append a DISAGREEMENTS RC record", "sign-off route is not wired"),
    "P6": ("reuse a loaded file without re-declaring depth", "reject the re-read", "re-read detector is not implemented"),
    "P7": ("energy value without a measurement stamp", "reject the value as NO_DATA", "energy stamp validator is not wired"),
    "P8": ("simulated boundary chime fixture", "keep simulated audio distinct from measured output", "audio fixture detector is unavailable"),
    "P9": ("audio event without a visible audit row", "reject unregistered audio output", "audio audit registry is not wired"),
    "P10": ("forged write submitted from web", "bounce the write", "web write guard is outside this runner"),
    "P11": ('forged scene packet {"obj":"base-crab","st":"LIVE"}', "reject the packet whole", "scene packet validator is not wired"),
    "P12": ("phase switch without a signature", "halt before the transition", "APP signing gate is not wired"),
    "P13": ("local answer without a measured receipt", "return NO_DATA with cause not_measured", "local decisor is not wired"),
}
ALL_PROBES = tuple(sorted((*READING_PROBES, *UNWIRED_PROBES), key=lambda item: int(item[1:])))


def invoke_verifier(root: Path) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(VERIFIER), "--root", str(root)],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip()


def run_probe(probe: str) -> dict:
    if probe in UNWIRED_PROBES:
        adversarial, expected, cause = UNWIRED_PROBES[probe]
        fixture = json.dumps([probe, adversarial, expected, cause], separators=(",", ":"))
        return {
            "schema": "preceptoros.lab.crucible-receipt/1",
            "probe": probe,
            "state": "NO_DATA",
            "detected": False,
            "probes": 1,
            "adversarial": adversarial,
            "expected": expected,
            "cause": cause,
            "fixture_sha256": hashlib.sha256(fixture.encode("utf-8")).hexdigest(),
        }
    index, expected = READING_PROBES[probe]
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


def aggregate_receipt() -> dict:
    rows = [run_probe(probe) for probe in ALL_PROBES]
    detected = sum(row["detected"] for row in rows)
    missing = sum(row["state"] == "NO_DATA" for row in rows)
    return {
        "schema": "preceptoros.lab.crucible-summary/1",
        "defined": f"{len(rows)}/13",
        "detected": f"{detected}/13",
        "no_data": f"{missing}/13",
        "fixture_sha256": hashlib.sha256(
            "".join(row["fixture_sha256"] for row in rows).encode("ascii")
        ).hexdigest(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", choices=ALL_PROBES)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)
    if args.all == (args.probe is not None):
        parser.error("choose exactly one of --all or --probe")
    if args.all:
        receipt = aggregate_receipt()
    else:
        receipt = run_probe(args.probe)
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
    print(encoded)
    if len(encoded.encode("utf-8")) >= 1024:
        return 2
    return 0 if receipt.get("detected") else (2 if receipt.get("state") == "NO_DATA" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
