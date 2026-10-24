#!/usr/bin/env python3
"""Measure already-fetched MVP origin refs without touching their worktrees."""
import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

try:
    from mvp_regression import CONTRAST, validate
except ModuleNotFoundError:
    from bin.mvp_regression import CONTRAST, validate

WEB_SOURCE = "docs/rebuild/examples"
APP_SOURCE = "interface/face"
WEB_MANIFEST = "docs/rebuild/mvp-origin-evidence.json"
APP_MANIFEST = "interface/mvp-origin-evidence.json"
WEB_PATHS = (WEB_SOURCE, "public/game", "public/assets", WEB_MANIFEST)
APP_PATHS = (APP_SOURCE, APP_MANIFEST)
CONTRAST_LINE = re.compile(r"^(basic|atlantis|zombie) \([^\n]+?\): .*?contrast fg/bg ([0-9.]+), accent ([0-9.]+); PASS$", re.M)
FRAME_SIZE = re.compile(r"worst frame (\d+)(?: UTF-8 bytes of 1,024| B)")
NETWORK = re.compile(r"\b(?:fetch\s*\(|XMLHttpRequest\b|WebSocket\b|EventSource\b)|(?:require\s*\(|from\s*)['\"](?:node:)?(?:http|https|net|dgram)['\"]")
GATES = ("narration_viewports", "zoom_bounds", "contrast_pairs", "byte_budget_post_export", "task_level_parity")


def git(repo, *args, timeout=20):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, timeout=timeout).stdout.decode().strip()


def unpack_ref(repo, ref, paths, destination):
    if not ref.startswith("refs/remotes/origin/"):
        raise ValueError("ref must be an already-fetched origin tracking ref")
    included = []
    for path in paths:
        try:
            git(repo, "cat-file", "-e", ref + ":" + path)
            included.append(path)
        except subprocess.SubprocessError:
            pass
    raw = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", ref, *included], check=True, capture_output=True, timeout=30).stdout
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        for member in archive.getmembers():
            rel = Path(member.name)
            if rel.is_absolute() or ".." in rel.parts:
                raise ValueError("unsafe archive path")
            target = destination / rel
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError("archive body unavailable")
                target.write_bytes(stream.read())
            else:
                raise ValueError("archive contains a non-regular entry")


def read_manifest(root, path, tree):
    file = root / path
    if not file.is_file():
        return None, "manifest absent from origin ref"
    try:
        doc = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "manifest is unreadable or invalid JSON"
    if not isinstance(doc, dict) or doc.get("schema") != "preceptoros.mvp-regression-evidence/1":
        return None, "manifest schema mismatch"
    if doc.get("source_tree_oid") != tree:
        return None, "manifest source_tree_oid does not match origin tree"
    return doc, None


def validator_dependencies(web):
    entry = web / WEB_SOURCE / "validate.mjs"
    pending, seen = [entry], set()
    require = re.compile(r"\brequire\(\s*['\"]([^'\"]+)['\"]\s*\)")
    imported = re.compile(r"\bfrom\s*['\"]([^'\"]+)['\"]")
    side_effect_import = re.compile(r"\bimport\s*['\"]([^'\"]+)['\"]")
    while pending:
        path = pending.pop()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        source = path.read_text(encoding="utf-8", errors="replace")
        imports = imported.findall(source) + side_effect_import.findall(source)
        for module in require.findall(source) + imports:
            if module.startswith("."):
                child = (path.parent / module).resolve()
                if child.suffix == "":
                    child = child.with_suffix(".js")
                pending.append(child)
    return seen


def run_validator(web, app, scratch):
    code = validator_dependencies(web) - {web / WEB_SOURCE / "validate.mjs"}
    if any(NETWORK.search(p.read_text(encoding="utf-8", errors="replace")) for p in code):
        return None, "validator source contains a network API; execution refused"
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "APP_DIR": str(app), "NO_PROXY": "*", "no_proxy": "*"}
    command = ["node", "--permission", "--allow-fs-read=" + str(scratch), str(web / WEB_SOURCE / "validate.mjs")]
    try:
        p = subprocess.run(command, cwd=web, env=env, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "validator unavailable: " + type(exc).__name__
    return {"exit_code": p.returncode, "output": p.stdout + p.stderr}, None


def merged_manifest_result(web_doc, app_doc, web_tree, app_tree):
    if not web_doc or not app_doc:
        return None
    if not all(k in web_doc for k in ("narration", "zoom", "contrast", "export")) or "task_parity" not in app_doc:
        return None
    fixture = json.loads((Path(__file__).resolve().parents[1] / "fixtures/mvp-regression/baseline.synthetic.json").read_text())
    combined = dict(fixture)
    combined.update({k: web_doc[k] for k in ("narration", "zoom", "contrast", "export")})
    combined["task_parity"] = app_doc["task_parity"]
    combined["source"] = {"kind": "pinned origin manifests", "web_tree": web_tree, "app_tree": app_tree}
    return validate(combined)


def run(web_repo, web_ref, app_repo, app_ref):
    for repo, ref in ((web_repo, web_ref), (app_repo, app_ref)):
        if not ref.startswith("refs/remotes/origin/"):
            raise ValueError("refs must be already-fetched origin tracking refs")
    web_head = git(web_repo, "rev-parse", "--verify", web_ref + "^{commit}")
    app_head = git(app_repo, "rev-parse", "--verify", app_ref + "^{commit}")
    web_tree = git(web_repo, "rev-parse", web_ref + ":" + WEB_SOURCE)
    app_tree = git(app_repo, "rev-parse", app_ref + ":" + APP_SOURCE)
    result = {"schema": "lab.mvp-origin-gates/2", "network_used": False, "read_only": True,
              "refs": {"web": {"ref": web_ref, "head": web_head, "tree": web_tree},
                       "app": {"ref": app_ref, "head": app_head, "tree": app_tree}}, "gates": {}}
    with tempfile.TemporaryDirectory(prefix="mvp-origin-static-") as temp:
        scratch = Path(temp); web, app = scratch / "web", scratch / "app"
        web.mkdir(); app.mkdir()
        unpack_ref(web_repo, web_ref, WEB_PATHS, web)
        unpack_ref(app_repo, app_ref, APP_PATHS, app)
        web_doc, web_cause = read_manifest(web, WEB_MANIFEST, web_tree)
        app_doc, app_cause = read_manifest(app, APP_MANIFEST, app_tree)
        result["manifests"] = {"web": {"state": "MEASURED" if web_doc else "NO_DATA", "cause": web_cause},
                               "app": {"state": "MEASURED" if app_doc else "NO_DATA", "cause": app_cause}}
        measured, validator_cause = run_validator(web, app, scratch)
        output = measured["output"] if measured else ""
        result["validator"] = {"exit_code": measured.get("exit_code") if measured else None,
                               "cause": validator_cause or ("validator assertions failed" if measured and measured["exit_code"] else None)}
        css = (web / WEB_SOURCE / "face.css").read_text(encoding="utf-8")
        tpl = (web / WEB_SOURCE / "tools/face.tpl.html").read_text(encoding="utf-8")
        narration_structure = "height:100dvh" in css and "overflow:hidden" in css and 'role="status" aria-live="polite"' in tpl
        result["gates"]["narration_viewports"] = {"verdict": "NO_DATA", "static_structure": "GREEN" if narration_structure else "RED",
            "cause": "no measured viewport/orientation/height manifest; source inspection cannot prove visible rendering and zero scroll"}
        zoom = (web / "public/game/map_zoom.js").read_text(encoding="utf-8")
        bounds = re.search(r"var MIN\s*=\s*([0-9.]+),\s*MAX\s*=\s*([0-9.]+)", zoom)
        clamp = "Math.max(MIN, Math.min(MAX, v))" in zoom
        actual_bounds = [float(bounds.group(1)), float(bounds.group(2))] if bounds else None
        result["gates"]["zoom_bounds"] = {"verdict": "NO_DATA", "static_bounds": "GREEN" if actual_bounds == [0.6, 3.0] and clamp else "RED",
            "bounds": actual_bounds, "cause": "no samples establish interactive-object size invariance across zoom"}
        contrasts = {name: [float(a), float(b)] for name, a, b in CONTRAST_LINE.findall(output)}
        expected = {name: [values["primary"], values["secondary"]] for name, values in CONTRAST.items()}
        drift = {name: {"expected": expected[name], "measured": contrasts[name]} for name in contrasts
                 if any(abs(a-b) > 0.01 for a, b in zip(expected[name], contrasts[name]))}
        result["gates"]["contrast_pairs"] = {"verdict": "NO_DATA" if len(contrasts) != 3 else "RED" if drift else "GREEN",
            "measured": contrasts, "drift": drift, "standards_certification": False,
            "cause": "offline contrast measurements missing" if len(contrasts) != 3 else None}
        frame_sizes = [int(value) for value in FRAME_SIZE.findall(output)]
        max_frame = max(frame_sizes) if frame_sizes else None
        result["gates"]["byte_budget_post_export"] = {"verdict": "NO_DATA", "pre_export_model": "GREEN" if measured and measured["exit_code"] == 0 and max_frame is not None and max_frame <= 1024 else "RED" if measured and measured["exit_code"] else "NO_DATA",
            "maximum_generated_frame_utf8_bytes": max_frame, "ceiling_bytes": 1024,
            "cause": "no post-export artifact/hash manifest; validator measures deterministic model frames"}
        app_parity = "app parity:" in output and "PASS" in output
        result["gates"]["task_level_parity"] = {"verdict": "NO_DATA", "static_face_parity": "GREEN" if app_parity else "NO_DATA",
            "cause": "no shared task fixture receipt comparing state, messages, errors, controls and contract outputs"}
        complete = merged_manifest_result(web_doc, app_doc, web_tree, app_tree)
        if complete:
            mapping = {"narration_viewports": ("viewport", "narration"),
                       "zoom_bounds": ("zoom", "interactive object"),
                       "contrast_pairs": ("contrast",),
                       "byte_budget_post_export": ("frame", "export", "state inventory"),
                       "task_level_parity": ("parity", "task output")}
            for gate in GATES:
                errors = complete["errors"]
                relevant = [e for e in errors if any(needle in e.lower() for needle in mapping[gate])]
                manifest_verdict = "RED" if relevant else "GREEN"
                result["gates"][gate]["manifest_verdict"] = manifest_verdict
                result["gates"][gate]["manifest_errors"] = relevant
                if manifest_verdict == "RED" or result["gates"][gate]["verdict"] == "RED":
                    result["gates"][gate]["verdict"] = "RED"
                else:
                    result["gates"][gate]["verdict"] = "GREEN"
        result["validator_output_tail"] = output[-1200:]
    if any(g["verdict"] == "RED" or g.get("static_structure") == "RED" or g.get("static_bounds") == "RED" for g in result["gates"].values()) or result["validator"].get("exit_code") not in (0, None):
        result["verdict"] = "RED"
    elif all(g["verdict"] == "GREEN" for g in result["gates"].values()):
        result["verdict"] = "GREEN"
    else:
        result["verdict"] = "NO_DATA"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web-repo", type=Path, required=True)
    parser.add_argument("--web-ref", required=True)
    parser.add_argument("--app-repo", type=Path, required=True)
    parser.add_argument("--app-ref", required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args.web_repo, args.web_ref, args.app_repo, args.app_ref)
    except (ValueError, OSError, subprocess.SubprocessError, tarfile.TarError) as exc:
        result = {"schema": "lab.mvp-origin-gates/2", "verdict": "NO_DATA", "network_used": False,
                  "read_only": True, "cause": type(exc).__name__ + ": " + str(exc)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["verdict"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
