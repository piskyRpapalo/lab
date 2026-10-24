#!/usr/bin/env python3
"""Classify pasted FARO fetch/run evidence; this parser never makes network requests."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

CLASSIFIED, NO_DATA = "CLASSIFIED", "NO_DATA"
EXPECTED_CI_RUN = 40110583184
LIMIT = 4 * 1024 * 1024
SHA = re.compile(r"^[0-9a-f]{64}$")
SECTIONS = {"=== GESTURE A ===", "=== GESTURE B ===", "=== GESTURE C ==="}


def _fields(line: str, prefix: str) -> dict[str, str]:
    if not line.startswith(prefix + " "):
        raise ValueError("record prefix mismatch")
    result = {}
    for item in line[len(prefix) + 1:].split():
        if "=" not in item:
            raise ValueError("malformed evidence field")
        key, value = item.split("=", 1)
        if key in result or not value:
            raise ValueError("duplicate or empty evidence field")
        result[key] = value
    return result


def _route(value: str) -> str:
    if (not value.startswith("/") or len(value) > 256 or "\\" in value
            or any(ch.isspace() for ch in value) or "?" in value or "#" in value):
        raise ValueError("route must be a local absolute path without query or fragment")
    path = PurePosixPath(value)
    if any(part in {".", ".."} for part in path.parts):
        raise ValueError("route path traversal is not accepted")
    normalized = path.as_posix()
    return normalized + "/" if value.endswith("/") and normalized != "/" else normalized


def _digest(value: str) -> str:
    if not SHA.fullmatch(value):
        raise ValueError("SHA-256 must be 64 lowercase hexadecimal characters")
    return value


def _redirected(row: dict[str, str]) -> bool:
    chain = row["redirects"]
    if chain == "-" or row["final_path"] == row["route"]:
        return False
    parts = chain.split(">")
    if len(parts) < 3 or len(parts) % 2 == 0 or parts[0] != row["route"] or parts[-1] != row["final_path"]:
        return False
    return all(re.fullmatch(r"30[12378]", parts[i]) for i in range(1, len(parts), 2))


def _sections(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in SECTIONS:
            key = stripped.split()[2]
            if key in result:
                raise ValueError("duplicate gesture section")
            result[key] = []
            current = key
        elif current:
            result[current].append(line)
    if set(result) != {"A", "B", "C"}:
        raise ValueError("one or more gesture sections are missing")
    return result


def parse_evidence(raw: str | bytes) -> dict[str, object]:
    try:
        if isinstance(raw, bytes):
            if len(raw) > LIMIT:
                raise ValueError("input exceeds 4 MiB")
            text = raw.decode("utf-8", errors="strict")
        elif isinstance(raw, str):
            if len(raw.encode("utf-8")) > LIMIT:
                raise ValueError("input exceeds 4 MiB")
            text = raw
        else:
            raise ValueError("input must be UTF-8 text")
        sections = _sections(text)
        local_rows: dict[str, dict[str, str]] = {}
        local_conflicts: set[str] = set()
        ci_rows: dict[str, str | None] = {}
        for section, prefix in (("A", "A_ROUTE"), ("B", "B_ROUTE")):
            seen_in_section: set[str] = set()
            for line in sections[section]:
                if not line.strip().startswith(prefix + " "):
                    continue
                row = _fields(line.strip(), prefix)
                required = {"route", "main_sha256", "local_sha256", "status", "final_path", "redirects"}
                if set(row) != required:
                    raise ValueError(prefix + " has missing or unknown fields")
                route = _route(row["route"])
                if route in seen_in_section:
                    raise ValueError("duplicate local route observation")
                seen_in_section.add(route)
                row["route"] = route
                row["main_sha256"] = _digest(row["main_sha256"])
                row["local_sha256"] = _digest(row["local_sha256"])
                row["final_path"] = _route(row["final_path"])
                if not re.fullmatch(r"[1-5][0-9]{2}", row["status"]):
                    raise ValueError("route HTTP status must be a three-digit status")
                chain = row["redirects"]
                if chain != "-" and ("http://" in chain.lower() or "https://" in chain.lower()):
                    raise ValueError("redirect chain must contain paths, never hosts")
                if route in local_rows and local_rows[route] != row:
                    local_conflicts.add(route)
                else:
                    local_rows[route] = row
        summary = None
        for line in sections["B"]:
            if line.strip().startswith("B_SUMMARY "):
                if summary is not None:
                    raise ValueError("duplicate B_SUMMARY")
                summary = _fields(line.strip(), "B_SUMMARY")
        if summary is None or set(summary) != {"source_sha", "compared", "equal", "changed", "missing", "network_errors"}:
            raise ValueError("B summary is incomplete")
        if not re.fullmatch(r"[0-9a-f]{40,64}", summary["source_sha"]):
            raise ValueError("B summary source commit is invalid")
        if any(not value.isdecimal() for key, value in summary.items() if key != "source_sha"):
            raise ValueError("B summary counts must be nonnegative integers")
        ci_run = None
        for line in sections["C"]:
            if line.strip().startswith("RUN "):
                if ci_run is not None:
                    raise ValueError("duplicate CI RUN")
                ci_run = _fields(line.strip(), "RUN")
        if ci_run is None or set(ci_run) != {"id", "head_sha", "status", "conclusion"}:
            raise ValueError("CI run metadata is incomplete")
        if not ci_run["id"].isdecimal() or not re.fullmatch(r"[0-9a-f]{40,64}", ci_run["head_sha"]):
            raise ValueError("CI run id or head SHA is invalid")
        if int(ci_run["id"]) != EXPECTED_CI_RUN:
            raise ValueError("CI run id does not match the forensic target")
        if ci_run["status"] != "completed" or ci_run["conclusion"] not in {"failure", "success"}:
            raise ValueError("CI run is not a completed success/failure observation")
        for line in sections["C"]:
            if line.strip().startswith("CI_DISTINCT "):
                row = _fields(line.strip(), "CI_DISTINCT")
                if set(row) - {"route", "sha256"} or "route" not in row:
                    raise ValueError("CI_DISTINCT has missing or unknown fields")
                route = _route(row["route"])
                if route in ci_rows:
                    raise ValueError("duplicate CI_DISTINCT")
                ci_rows[route] = _digest(row["sha256"]) if "sha256" in row else None
        routes = sorted(set(local_rows) | set(ci_rows))
        if len(routes) != 11:
            raise ValueError("expected an 11-route union from local and CI observations")
        b_healthy = (int(summary["compared"]) > 0
                     and int(summary["equal"]) == int(summary["compared"])
                     and all(int(summary[key]) == 0 for key in ("changed", "missing", "network_errors")))
        results = []
        for route in routes:
            local = local_rows.get(route)
            ci_hash = ci_rows.get(route)
            row: dict[str, object] = {"route": route, "sha_in": local.get("main_sha256") if local else None,
                                      "sha_out": local.get("local_sha256") if local else None,
                                      "ci_sha256": ci_hash, "classification": NO_DATA,
                                      "verdict": NO_DATA, "recommended_fix": None}
            if route in local_conflicts:
                row["cause"] = "local route observations from A and B conflict"
            elif local is None:
                row["cause"] = "local fetch evidence missing for route"
            elif route not in ci_rows:
                row["cause"] = "CI distinct-route evidence missing for route"
            elif summary["source_sha"] != ci_run["head_sha"]:
                row["cause"] = "CI head differs from the source commit measured locally"
            elif _redirected(local):
                row.update(classification="REDIRECT_ARTIFACT", verdict="REDIRECT_ARTIFACT",
                           recommended_fix="compare the canonical pretty URL; retain raw-route evidence")
            elif local["local_sha256"] != local["main_sha256"]:
                row.update(classification="REAL_DRIFT", verdict="REAL_DRIFT",
                           recommended_fix="investigate the content source; do not change the FARO transport contract")
            elif ci_run["conclusion"] == "failure":
                if b_healthy:
                    row.update(classification="EDGE_STALE", verdict="EDGE_STALE",
                               recommended_fix="measure and remediate the serving edge/PoP; preserve the CI run evidence")
                    row["interpretation"] = "consistent with an edge response mismatch; a specific PoP cause is not proven"
                else:
                    row["cause"] = "full local FARO summary is not byte-clean; edge classification is not supported"
            else:
                row["cause"] = "CI run does not report a failed comparison"
            results.append(row)
        state = CLASSIFIED if all(row["classification"] != NO_DATA for row in results) else NO_DATA
        receipt = {"schema": "preceptoros.lab.faro-forensic/1", "state": state,
                   "cause": None if state == CLASSIFIED else "one or more route observations are incomplete",
                   "ci_run": ci_run, "source_commit": summary["source_sha"],
                   "local_faro_summary": {k: int(v) for k, v in summary.items() if k != "source_sha"},
                   "route_count": len(results), "routes": results,
                   "input_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                   "network_used": False}
        return receipt
    except UnicodeError:
        return {"schema": "preceptoros.lab.faro-forensic/1", "state": NO_DATA,
                "cause": "input is not valid UTF-8", "routes": [], "network_used": False}
    except ValueError as exc:
        return {"schema": "preceptoros.lab.faro-forensic/1", "state": NO_DATA,
                "cause": str(exc)[:240], "routes": [], "network_used": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="pasted evidence text; stdin when omitted")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.input:
            with args.input.open("rb") as source:
                raw = source.read(LIMIT + 1)
        else:
            raw = sys.stdin.buffer.read(LIMIT + 1)
    except OSError as exc:
        result = {"schema": "preceptoros.lab.faro-forensic/1", "state": NO_DATA,
                  "cause": "input read failed: " + type(exc).__name__, "routes": [], "network_used": False}
    else:
        result = parse_evidence(raw)
    rendered = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if result["state"] == CLASSIFIED else 2


if __name__ == "__main__":
    raise SystemExit(main())
