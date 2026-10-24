#!/usr/bin/env python3
"""Verify a cold-install receipt offline; no hosts or network are contacted."""
import argparse
import hashlib
import json
import re
from pathlib import Path

HEX = re.compile(r"^[0-9a-f]{64}$")
PHASES = ("install_online", "first_launch", "task_flow", "offline_launch",
          "offline_surfaces", "offline_restart")
CLIENTS = ("web", "app")


def sha(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def verify(doc):
    red, missing, checks = [], [], {}
    if not isinstance(doc, dict) or doc.get("schema") != "lab.cold-install-receipt/1":
        return {"schema": "lab.cold-install-verdict/1", "verdict": "RED",
                "errors": ["unsupported receipt schema"], "no_data": []}
    if doc.get("evidence_kind") not in ("measured", "synthetic-test"):
        missing.append("evidence_kind must identify measured or synthetic-test evidence")
    if doc.get("fresh_install") != {"profile_cleared": True, "service_worker_cleared": True,
                                     "browser_cache_cleared": True}:
        missing.append("fresh profile, service worker and browser cache measurements required")
    allowed = doc.get("allowed_origin_sha256")
    if not isinstance(allowed, list) or not allowed or any(not HEX.fullmatch(str(x)) for x in allowed):
        missing.append("same-origin hash allowlist is absent or invalid")
        allowed = []
    artifacts = doc.get("artifacts")
    if not isinstance(artifacts, dict):
        missing.append("web/app artifact receipt is absent")
        artifacts = {}
    for client in CLIENTS:
        row = artifacts.get(client)
        if not isinstance(row, dict):
            missing.append(f"{client} artifact hashes missing")
            continue
        expected, installed, size = row.get("expected_sha256"), row.get("installed_sha256"), row.get("size_bytes")
        if not isinstance(expected, str) or not HEX.fullmatch(expected) or not isinstance(installed, str) or not HEX.fullmatch(installed):
            missing.append(f"{client} artifact hash invalid or absent")
        elif expected != installed:
            red.append(f"{client} installed artifact differs from pinned artifact")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            missing.append(f"{client} artifact size missing")
    required = doc.get("required_surface_ids")
    if not isinstance(required, list) or not required or any(not isinstance(x, str) or not x for x in required) or len(set(required)) != len(required):
        missing.append("unique required surface inventory is absent")
        required = []
    surface_doc = doc.get("surfaces")
    if not isinstance(surface_doc, dict):
        missing.append("surface results are absent")
        surface_doc = {}
    for client in CLIENTS:
        rows = surface_doc.get(client)
        if not isinstance(rows, list):
            missing.append(f"{client} surface results absent")
            continue
        ids = [r.get("id") for r in rows if isinstance(r, dict)]
        if len(ids) != len(rows) or len(set(ids)) != len(ids) or set(ids) != set(required):
            missing.append(f"{client} surface coverage differs from required inventory")
        if any(r.get("visible") is not True or r.get("message_complete") is not True for r in rows if isinstance(r, dict)):
            red.append(f"{client} has an invisible or incomplete surface")
    phases = doc.get("phases")
    if not isinstance(phases, dict):
        missing.append("phase captures absent")
        phases = {}
    total = 0
    for phase in PHASES:
        data = phases.get(phase)
        if not isinstance(data, dict):
            missing.append(f"{phase} capture absent")
            continue
        requests = data.get("requests")
        if data.get("capture_complete") is not True or not isinstance(requests, list):
            missing.append(f"{phase} request capture incomplete")
            continue
        total += len(requests)
        if data.get("request_count") != len(requests):
            red.append(f"{phase} request count does not match captured rows")
        if data.get("request_log_sha256") != sha(canonical(requests)):
            red.append(f"{phase} request log hash mismatch")
        for request in requests:
            if not isinstance(request, dict) or request.get("transport") not in ("network", "cache", "local"):
                missing.append(f"{phase} has an unclassified request")
                continue
            origin = request.get("origin_sha256")
            if request["transport"] == "network" and origin not in allowed:
                red.append(f"{phase} contacted an origin outside the same-origin allowlist")
            if phase.startswith("offline_") and request["transport"] == "network":
                red.append(f"{phase} used network transport while offline")
    checks.update({"phases": len(PHASES), "required_surfaces": len(required),
                   "captured_requests": total, "clients": len(CLIENTS)})
    verdict = "RED" if red else "NO_DATA" if missing else "GREEN"
    return {"schema": "lab.cold-install-verdict/1", "verdict": verdict,
            "evidence_kind": doc.get("evidence_kind"), "checks": checks,
            "errors": list(dict.fromkeys(red)), "no_data": list(dict.fromkeys(missing)),
            "claim": "GREEN verifies this receipt only; it is not an accessibility certification"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        doc = json.loads(args.receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        result = {"schema": "lab.cold-install-verdict/1", "verdict": "NO_DATA",
                  "errors": [], "no_data": [f"receipt unreadable: {type(exc).__name__}"]}
    else:
        result = verify(doc)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["verdict"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
