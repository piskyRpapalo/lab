#!/usr/bin/env python3
"""Build an offline, source-pasted receipt for one LAB GitHub Actions run."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

LIMIT = 4 * 1024 * 1024
NO_DATA = "NO_DATA"
SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
RAN_RE = re.compile(r"^Ran (\d+) tests?\b", re.I)
FAILED_RE = re.compile(r"^FAILED(?:\s*\((.*)\))?\s*$")


def _header(text: str) -> dict[str, object]:
    stripped_text = text.lstrip()
    if stripped_text.startswith("{"):
        try:
            obj, _ = json.JSONDecoder().raw_decode(stripped_text)
        except json.JSONDecodeError:
            obj = None
        if isinstance(obj, dict) and ("databaseId" in obj or "run_id" in obj):
            return {"run_id": obj.get("databaseId", obj.get("run_id")),
                    "head_sha": obj.get("headSha", obj.get("head_sha")),
                    "status": obj.get("status"), "conclusion": obj.get("conclusion")}
    for line in text.splitlines():
        candidate = line.strip()
        if candidate.startswith("RUN "):
            result = {}
            for item in candidate[4:].split():
                if "=" not in item:
                    raise ValueError("malformed RUN metadata")
                key, value = item.split("=", 1)
                if key in result:
                    raise ValueError("duplicate RUN metadata field")
                result[key] = value
            return {"run_id": int(result["id"]), "head_sha": result["head_sha"],
                    "status": result["status"], "conclusion": result.get("conclusion")}
        if candidate.startswith("{"):
            try:
                obj = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and ("databaseId" in obj or "run_id" in obj):
                return {"run_id": obj.get("databaseId", obj.get("run_id")),
                        "head_sha": obj.get("headSha", obj.get("head_sha")),
                        "status": obj.get("status"), "conclusion": obj.get("conclusion")}
    return {}


def consume(raw: str | bytes, *, expected_run_id: int | None = None,
            metadata: dict[str, object] | None = None) -> dict[str, object]:
    try:
        if isinstance(raw, bytes):
            if len(raw) > LIMIT:
                raise ValueError("pasted log exceeds 4 MiB")
            text = raw.decode("utf-8", errors="strict")
        elif isinstance(raw, str):
            if len(raw.encode("utf-8")) > LIMIT:
                raise ValueError("pasted log exceeds 4 MiB")
            text = raw
        else:
            raise ValueError("input must be UTF-8 text")
    except UnicodeError:
        return _no_data("pasted log is not valid UTF-8")
    except ValueError as exc:
        return _no_data(str(exc))
    if not text.strip():
        return _no_data("pasted run log is absent or empty")

    try:
        info = _header(text)
    except (ValueError, KeyError, TypeError) as exc:
        return _no_data("run metadata is malformed: " + str(exc))
    for key, value in (metadata or {}).items():
        if key in info and info[key] is not None and str(info[key]) != str(value):
            return _no_data("supplied run metadata conflicts with pasted summary")
        info[key] = value
    run_id = info.get("run_id")
    head_sha = info.get("head_sha")
    status = str(info.get("status") or "").lower()
    conclusion = info.get("conclusion")
    conclusion = str(conclusion).lower() if conclusion is not None else None
    if run_id is None or not str(run_id).isdecimal():
        return _no_data("run id missing; pass it from the measured gh run view result")
    run_id = int(run_id)
    if expected_run_id is not None and run_id != expected_run_id:
        return _no_data("run id does not match the requested run")
    if not isinstance(head_sha, str) or not SHA_RE.fullmatch(head_sha):
        return _no_data("head SHA missing or invalid")
    if status in {"queued", "requested", "waiting", "pending", "in_progress"}:
        return _no_data("run is still in flight", run_id, head_sha, status, conclusion)
    if status != "completed":
        return _no_data("run status is absent or unsupported", run_id, head_sha, status, conclusion)
    if conclusion == "cancelled":
        return _no_data("run was cancelled before a complete gate result", run_id, head_sha, "cancelled", conclusion)
    if conclusion not in {"success", "failure"}:
        return _no_data("completed run conclusion is absent or unsupported", run_id, head_sha, status, conclusion)

    gates: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    contexts: dict[str, dict[str, object]] = {}
    for original in text.splitlines():
        fields = original.split("\t", 3)
        job = fields[0] if len(fields) == 4 else "pasted"
        line = fields[3] if len(fields) == 4 else original
        stripped = line.strip()
        ctx = contexts.setdefault(job, {"gate": "unclassified", "latest": None,
                                        "failure": None, "sequenced": False,
                                        "pass": None, "pass_set": set()})
        gate_marker = re.match(r"^GATE\s+([A-Za-z0-9_.-]+)\s*$", stripped)
        if gate_marker:
            ctx["gate"] = gate_marker.group(1)
            ctx["latest"] = None
            continue
        if re.search(r"\btanda\s+([12])/2\b", stripped, re.I):
            marker = re.search(r"\btanda\s+([12])/2\b", stripped, re.I)
            ctx["sequenced"] = True
            ctx["pass"] = int(marker.group(1))
            ctx["pass_set"].add(int(marker.group(1)))
            ctx["gate"] = "unittest"
            ctx["latest"] = None
            continue
        if not ctx["sequenced"]:
            for command, name in (("python3 -m unittest discover", "unittest"),
                                  ("python3 test_llms.py", "test_llms"),
                                  ("python3 bin/verify_llms_tree.py", "verify_llms_tree")):
                if command in line:
                    ctx["gate"] = name
                    ctx["latest"] = None
        current_gate = str(ctx["gate"])
        latest_gate = ctx["latest"]
        ran = RAN_RE.match(stripped)
        if ran:
            if ctx["failure"]:
                failures.append({"job": job, "gate": current_gate,
                                 "verbatim": "\n".join(ctx["failure"])})
                ctx["failure"] = None
            latest_gate = {"job": job, "name": current_gate,
                           "pass": ctx["pass"], "tests_run": int(ran.group(1)),
                           "skipped": None, "failures": 0, "errors": 0,
                           "outcome": "NO_DATA"}
            gates.append(latest_gate)
            ctx["latest"] = latest_gate
            continue
        if current_gate == "verify_llms_tree" and latest_gate is None and stripped.startswith(("LIVE", "OK")):
            latest_gate = {"job": job, "name": current_gate, "pass": ctx["pass"],
                           "tests_run": None, "checks_observed": None, "skipped": 0,
                           "failures": 0, "errors": 0, "outcome": "GREEN"}
            check_count = re.search(r"(\d+) indexed paths", stripped)
            if check_count:
                latest_gate["checks_observed"] = int(check_count.group(1))
            gates.append(latest_gate)
            ctx["latest"] = latest_gate
            if ctx["sequenced"]:
                ctx["sequenced"] = False
            continue
        failed = FAILED_RE.match(stripped)
        if failed:
            if latest_gate is not None:
                latest_gate["outcome"] = "RED"
                details = failed.group(1) or ""
                match = re.search(r"failures=(\d+)", details)
                if match:
                    latest_gate["failures"] = int(match.group(1))
                match = re.search(r"errors=(\d+)", details)
                if match:
                    latest_gate["errors"] = int(match.group(1))
            if ctx["failure"]:
                ctx["failure"].append(original)
                failures.append({"job": job, "gate": current_gate,
                                 "verbatim": "\n".join(ctx["failure"])})
                ctx["failure"] = None
            continue
        if stripped.startswith("OK") and latest_gate is not None:
            latest_gate["outcome"] = "GREEN"
            skipped = re.search(r"skipped=(\d+)", stripped)
            latest_gate["skipped"] = int(skipped.group(1)) if skipped else 0
            if ctx["sequenced"]:
                if current_gate == "unittest":
                    ctx["gate"] = "test_llms"
                    ctx["latest"] = None
                elif current_gate == "test_llms":
                    ctx["gate"] = "verify_llms_tree"
                    ctx["latest"] = None
        if stripped.startswith(("FAIL:", "ERROR:")) or stripped.startswith("Traceback (most recent call last):"):
            if ctx["failure"] is None:
                ctx["failure"] = []
            ctx["failure"].append(original)
        elif ctx["failure"] is not None:
            ctx["failure"].append(original)

    for job, ctx in contexts.items():
        if ctx["failure"]:
            failures.append({"job": job, "gate": str(ctx["gate"]),
                             "verbatim": "\n".join(ctx["failure"])})
    if not gates:
        return _no_data("no per-gate test summaries were found in pasted log", run_id, head_sha, status, conclusion)
    required = {"unittest", "test_llms", "verify_llms_tree"}
    incomplete = [gate for gate in gates if gate["outcome"] == "NO_DATA"]
    observed_jobs = {str(gate["job"]) for gate in gates}
    missing_by_job = {}
    for job in observed_jobs:
        observed = {str(gate["name"]) for gate in gates if gate["job"] == job}
        missing = sorted(required - observed)
        if missing:
            missing_by_job[job] = missing
    missing_passes = {}
    for job in observed_jobs:
        ctx = contexts.get(job, {})
        if ctx.get("pass_set") and ctx["pass_set"] != {1, 2}:
            missing_passes[job] = sorted({1, 2} - ctx["pass_set"])
    incomplete_run = bool(incomplete or missing_by_job or missing_passes)
    if incomplete_run and conclusion == "success":
        return {**_no_data("pasted log is incomplete: gate/pass summaries are missing",
                            run_id, head_sha, status, conclusion),
                "gates": gates, "missing_gates_by_job": missing_by_job,
                "missing_passes_by_job": missing_passes,
                "input_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    if conclusion == "failure" or failures or any(g["outcome"] == "RED" for g in gates):
        state, cause = "RED", "completed run contains a failed conclusion or gate"
        if incomplete_run:
            cause += "; remaining gate coverage is incomplete"
    else:
        state, cause = "GREEN", None
    failure_details_state = ("VERBATIM_CAPTURED" if failures else
                             ("NO_DATA · failure text is absent from pasted input" if conclusion == "failure" else "NOT_APPLICABLE"))
    return {"schema": "preceptoros.lab.remote-ci-run/1", "state": state,
            "cause": cause, "run_id": run_id, "head_sha": head_sha,
            "status": status, "conclusion": conclusion, "gates": gates,
            "failures": failures, "failure_details_state": failure_details_state,
            "missing_gates_by_job": missing_by_job, "missing_passes_by_job": missing_passes,
            "input_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "network_used": False}


def _no_data(cause: str, run_id=None, head_sha=None, status=None, conclusion=None):
    return {"schema": "preceptoros.lab.remote-ci-run/1", "state": NO_DATA,
            "cause": cause, "run_id": run_id, "head_sha": head_sha,
            "status": status, "conclusion": conclusion,
            "gates": [], "failures": [], "network_used": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="pasted log; stdin when omitted")
    parser.add_argument("--run-id", type=int, help="id from gh run view")
    parser.add_argument("--head-sha", help="head from gh run view --json")
    parser.add_argument("--status", help="status from gh run view --json")
    parser.add_argument("--conclusion", help="conclusion from gh run view --json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.input:
            with args.input.open("rb") as source:
                raw = source.read(LIMIT + 1)
        else:
            raw = sys.stdin.buffer.read(LIMIT + 1)
    except OSError as exc:
        result = _no_data("input read failed: " + type(exc).__name__)
    else:
        supplied = {k: v for k, v in {"run_id": args.run_id, "head_sha": args.head_sha,
                                      "status": args.status, "conclusion": args.conclusion}.items()
                    if v is not None}
        result = consume(raw, expected_run_id=args.run_id, metadata=supplied)
    rendered = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return {"GREEN": 0, "RED": 1, NO_DATA: 2}[result["state"]]


if __name__ == "__main__":
    raise SystemExit(main())
