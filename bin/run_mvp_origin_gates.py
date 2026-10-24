#!/usr/bin/env python3
"""Validate MVP evidence stored in already-fetched origin branch objects; never fetch."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

try:
    from mvp_regression import validate
except ModuleNotFoundError:  # imported by the test suite as bin.run_mvp_origin_gates
    from bin.mvp_regression import validate

GATES = ("narration_viewports", "zoom_bounds", "contrast_pairs",
         "byte_budget_post_export", "task_level_parity")
WEB_PATH = "docs/rebuild/mvp-origin-evidence.json"
APP_PATH = "interface/mvp-origin-evidence.json"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, timeout=10).stdout.decode().strip()


def read_blob(repo, ref, path, source_path):
    if not ref.startswith("refs/remotes/origin/"):
        raise ValueError("ref must be an already-fetched origin tracking ref")
    try:
        head = git(repo, "rev-parse", "--verify", ref + "^{commit}")
        raw = subprocess.run(["git", "-C", str(repo), "show", ref + ":" + path],
                             check=True, capture_output=True, timeout=10).stdout
    except (subprocess.SubprocessError, OSError):
        return None, None, None
    tree = git(repo, "rev-parse", ref + ":" + source_path)
    return head, tree, raw


def _gate_errors(errors):
    groups = {
        "narration_viewports": ("viewport", "narration"),
        "zoom_bounds": ("zoom", "interactive object"),
        "contrast_pairs": ("contrast",),
        "byte_budget_post_export": ("frame", "export", "state inventory"),
        "task_level_parity": ("parity", "task output"),
    }
    return {gate: [e for e in errors if any(token in e.lower() for token in tokens)]
            for gate, tokens in groups.items()}


def run(web_repo, web_ref, app_repo, app_ref):
    result = {"schema": "lab.mvp-origin-gates/1", "network_used": False,
              "refs": {}, "gates": {}}
    web_head, web_tree, web_raw = read_blob(web_repo, web_ref, WEB_PATH, "docs/rebuild/examples")
    app_head, app_tree, app_raw = read_blob(app_repo, app_ref, APP_PATH, "interface/face")
    result["refs"] = {"web": {"ref": web_ref, "head": web_head},
                       "app": {"ref": app_ref, "head": app_head}}
    docs = {}
    for label, tree, raw in (("web", web_tree, web_raw), ("app", app_tree, app_raw)):
        if raw is None:
            docs[label] = None
            continue
        try:
            docs[label] = json.loads(raw)
        except (UnicodeError, json.JSONDecodeError):
            docs[label] = {"_invalid": True}
        if not isinstance(docs[label], dict):
            docs[label] = {"_invalid": True}
        result["refs"][label]["evidence_sha256"] = hashlib.sha256(raw).hexdigest()
        result["refs"][label]["evidence_tree"] = tree

    sections = {"narration_viewports": ("web", "narration"),
                "zoom_bounds": ("web", "zoom"),
                "contrast_pairs": ("web", "contrast"),
                "byte_budget_post_export": ("web", "export"),
                "task_level_parity": ("app", "task_parity")}
    baseline = Path(__file__).resolve().parents[1] / "fixtures/mvp-regression/baseline.synthetic.json"
    base = json.loads(baseline.read_text(encoding="utf-8"))
    combined = json.loads(json.dumps(base))
    missing = set()
    for gate, (label, section) in sections.items():
        evidence = docs[label]
        if evidence is None:
            missing.add(gate)
        elif evidence.get("_invalid"):
            result["gates"][gate] = {"verdict": "RED", "cause": "evidence JSON malformed"}
        elif not isinstance(evidence.get(section), dict):
            missing.add(gate)
        else:
            combined[section] = evidence[section]
            combined["source"][label + "_head"] = result["refs"][label]["head"]
            expected_tree = evidence.get("source_tree_oid")
            if expected_tree != result["refs"][label]["evidence_tree"]:
                result["gates"][gate] = {"verdict": "RED", "cause": "evidence source tree does not match branch"}
    if docs.get("web") and docs["web"].get("_invalid"):
        for gate, (label, _) in sections.items():
            if label == "web" and gate not in result["gates"]:
                result["gates"][gate] = {"verdict": "RED", "cause": "evidence JSON malformed"}
    if docs.get("app") and docs["app"].get("_invalid") and "task_level_parity" not in result["gates"]:
        result["gates"]["task_level_parity"] = {"verdict": "RED", "cause": "evidence JSON malformed"}
    combined["source"] = {"kind": "origin branch evidence", "web_head": web_head, "app_head": app_head}
    checked = validate(combined)
    by_gate = _gate_errors(checked["errors"])
    counts = checked["checks"]
    for gate in GATES:
        if gate in result["gates"]:
            continue
        if gate in missing:
            result["gates"][gate] = {"verdict": "NO_DATA", "cause": "required branch evidence section is absent"}
        else:
            errs = by_gate[gate]
            check_key = {"narration_viewports": "narration_viewports",
                         "zoom_bounds": "zoom_samples",
                         "contrast_pairs": "contrast_pairs",
                         "byte_budget_post_export": "post_export_frames",
                         "task_level_parity": "shared_task_cases"}[gate]
            result["gates"][gate] = {"verdict": "RED" if errs else "GREEN",
                                      "checks": {check_key: counts.get(check_key, 0)},
                                      "errors": errs}
    result["verdict"] = ("RED" if any(v["verdict"] == "RED" for v in result["gates"].values())
                         else "NO_DATA" if any(v["verdict"] == "NO_DATA" for v in result["gates"].values())
                         else "GREEN")
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--web-repo", type=Path, required=True)
    p.add_argument("--web-ref", required=True)
    p.add_argument("--app-repo", type=Path, required=True)
    p.add_argument("--app-ref", required=True)
    a = p.parse_args(argv)
    try:
        out = run(a.web_repo, a.web_ref, a.app_repo, a.app_ref)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        out = {"schema": "lab.mvp-origin-gates/1", "verdict": "NO_DATA",
               "network_used": False, "cause": type(exc).__name__}
    print(json.dumps(out, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if out["verdict"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
