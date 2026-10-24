#!/usr/bin/env python3
"""Verify a local WEB artifact tree against fetched origin/main without network."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import tarfile
from io import BytesIO
from pathlib import Path, PurePosixPath


SCHEMA = "preceptoros.lab.web-artifact-audit/1"
MANIFEST_SCHEMA = "preceptoros.lab.web-build-manifest/1"
GREEN, RED, NO_DATA = "GREEN", "RED", "NO_DATA"
MAIN_REF = "refs/remotes/origin/main"
FRAME_LIMIT = 1024
TEXT_SUFFIXES = {".html", ".css", ".js", ".mjs", ".json", ".webmanifest"}
URL_RE = re.compile(
    rb"(?i)(?:https?|wss?|ftp)://[^\s\"'<>)]*|(?<![A-Za-z0-9:])//[A-Za-z0-9.-]+(?:/[^\s\"'<>)]*)?"
)
NETWORK_CALL_RE = re.compile(
    r"\b(?:fetch|sendBeacon|EventSource|WebSocket|importScripts)\s*\(\s*([^,)]*)",
    re.IGNORECASE,
)
LITERAL_RE = re.compile(r"^(['\"])(.*?)\1$", re.DOTALL)


class AuditInputError(Exception):
    pass


def _git(repo: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AuditInputError(f"git unavailable: {type(exc).__name__}") from None
    if result.returncode:
        raise AuditInputError("git command failed: " + result.stderr.decode("utf-8", "replace").strip()[:240])
    return result.stdout


def _safe_rel(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise AuditInputError("manifest path is invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise AuditInputError("manifest path escapes artifact root")
    return path.as_posix()


def _main_public_tree(repo: Path) -> tuple[str, dict[str, bytes]]:
    raw = _git(repo, "rev-parse", "--verify", f"{MAIN_REF}^{{commit}}").decode().strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", raw):
        raise AuditInputError("origin/main commit is not a full object id")
    archive = _git(repo, "archive", "--format=tar", raw, "public")
    files: dict[str, bytes] = {}
    try:
        with tarfile.open(fileobj=BytesIO(archive), mode="r:") as tar:
            for member in tar.getmembers():
                if member.isdir():
                    continue
                if not member.isfile() or not member.name.startswith("public/"):
                    raise AuditInputError("main public tree contains an unsupported entry")
                rel = _safe_rel(member.name[len("public/"):])
                source = tar.extractfile(member)
                if source is None:
                    raise AuditInputError("main public file could not be read")
                files[rel] = source.read()
    except (tarfile.TarError, OSError) as exc:
        raise AuditInputError(f"main public archive is unreadable ({type(exc).__name__})") from None
    if not files:
        raise AuditInputError("origin/main has no public files")
    return raw, files


def _artifact_tree(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        raise AuditInputError("artifact root is missing")
    files: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise AuditInputError("artifact tree contains a symlink")
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            _safe_rel(rel)
            try:
                files[rel] = path.read_bytes()
            except OSError as exc:
                raise AuditInputError(f"artifact file is unreadable ({type(exc).__name__})") from None
    return files


def _manifest(path: Path, main_commit: str) -> dict[str, dict[str, object]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuditInputError(f"manifest unavailable or invalid ({type(exc).__name__})") from None
    if not isinstance(raw, dict) or raw.get("schema") != MANIFEST_SCHEMA:
        raise AuditInputError("manifest schema is missing or unsupported")
    if raw.get("source_commit") != main_commit:
        raise AuditInputError("manifest source commit does not equal fetched origin/main")
    rows = raw.get("files")
    if not isinstance(rows, list) or not rows:
        raise AuditInputError("manifest file list is missing or empty")
    result: dict[str, dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise AuditInputError("manifest row is not an object")
        rel = _safe_rel(row.get("path"))
        digest = row.get("sha256")
        size = row.get("size_bytes")
        kind = row.get("kind")
        if rel in result:
            raise AuditInputError("manifest contains a duplicate path")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise AuditInputError("manifest SHA-256 pin is invalid")
        if type(size) is not int or size < 0:
            raise AuditInputError("manifest byte-size pin is invalid")
        if kind not in {"asset", "bubble_frame"}:
            raise AuditInputError("manifest kind must be asset or bubble_frame")
        result[rel] = {"sha256": digest, "size_bytes": size, "kind": kind}
    return result


def _tree_digest(files: dict[str, bytes]) -> str:
    h = hashlib.sha256()
    for rel, body in sorted(files.items()):
        name = rel.encode("utf-8")
        h.update(len(name).to_bytes(4, "big"))
        h.update(name)
        h.update(len(body).to_bytes(8, "big"))
        h.update(hashlib.sha256(body).digest())
    return h.hexdigest()


def _external_scan(files: dict[str, bytes]) -> tuple[list[dict[str, str]], list[str]]:
    external: list[dict[str, str]] = []
    unresolved: list[str] = []
    for rel, body in files.items():
        if PurePosixPath(rel).suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = body.decode("utf-8", "replace")
        for match in URL_RE.finditer(body):
            external.append({"path": rel, "reference_sha256": hashlib.sha256(match.group(0)).hexdigest()})
        for match in NETWORK_CALL_RE.finditer(text):
            argument = match.group(1).strip()
            literal = LITERAL_RE.match(argument)
            if literal is None:
                unresolved.append(rel)
                continue
            value = literal.group(2).strip()
            if value and not value.startswith(("/", "./", "../", "?", "#", "data:")):
                if re.match(r"(?i)^(?:https?|wss?|ftp):", value):
                    continue  # counted as an absolute external URL above
                unresolved.append(rel)
    return external, sorted(set(unresolved))


def audit(
    *, web_repo: Path, artifact_root: Path, manifest_path: Path,
    max_file_bytes: int, max_total_bytes: int,
) -> dict[str, object]:
    if type(max_file_bytes) is not int or max_file_bytes <= 0:
        return {"state": NO_DATA, "cause": "max-file-bytes must be a positive measured limit"}
    if type(max_total_bytes) is not int or max_total_bytes <= 0:
        return {"state": NO_DATA, "cause": "max-total-bytes must be a positive measured limit"}
    try:
        main_commit, main_files = _main_public_tree(web_repo)
        pins = _manifest(manifest_path, main_commit)
        artifacts = _artifact_tree(artifact_root)
    except AuditInputError as exc:
        return {"state": NO_DATA, "cause": str(exc)}

    main_paths, pin_paths, artifact_paths = set(main_files), set(pins), set(artifacts)
    missing = sorted(main_paths - artifact_paths)
    extra = sorted(artifact_paths - main_paths)
    unpinned = sorted(main_paths - pin_paths)
    stale_pins = sorted(pin_paths - main_paths)
    mismatched: list[str] = []
    oversized: set[str] = set()
    total_bytes = sum(len(body) for body in artifacts.values())
    for rel, body in artifacts.items():
        kind = pins.get(rel, {}).get("kind")
        limit = FRAME_LIMIT if kind == "bubble_frame" else max_file_bytes
        if len(body) > limit:
            oversized.add(rel)
    details = []
    for rel in sorted(main_paths & artifact_paths & pin_paths):
        expected, actual, pin = main_files[rel], artifacts[rel], pins[rel]
        expected_hash = hashlib.sha256(expected).hexdigest()
        actual_hash = hashlib.sha256(actual).hexdigest()
        if expected != actual or pin["sha256"] != expected_hash or pin["size_bytes"] != len(expected):
            mismatched.append(rel)
        limit = FRAME_LIMIT if pin["kind"] == "bubble_frame" else max_file_bytes
        details.append({
            "path": rel,
            "kind": pin["kind"],
            "size_bytes": len(actual),
            "sha256": actual_hash,
            "limit_bytes": limit,
        })
    external, unresolved = _external_scan(artifacts)
    causes = []
    if missing:
        causes.append("missing build artifacts")
    if extra:
        causes.append("extra build artifacts")
    if unpinned or stale_pins:
        causes.append("integrity manifest path set differs from main")
    if mismatched:
        causes.append("artifact bytes or manifest integrity pins differ from main")
    if oversized:
        causes.append("byte ceiling exceeded")
    if total_bytes > max_total_bytes:
        causes.append("total build byte ceiling exceeded")
    if external:
        causes.append("external URL literal found")
    if unresolved:
        causes.append("dynamic network target cannot be resolved statically")
    state = NO_DATA if unresolved else (RED if causes else GREEN)
    receipt = {
        "schema": SCHEMA,
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "state": state,
        "source_ref": MAIN_REF,
        "source_commit": main_commit,
        "public_tree_sha256": _tree_digest(main_files),
        "files_checked": len(main_paths & artifact_paths & pin_paths),
        "main_file_count": len(main_paths),
        "artifact_file_count": len(artifact_paths),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "unpinned_count": len(unpinned),
        "stale_pin_count": len(stale_pins),
        "byte_mismatch_count": len(mismatched),
        "oversized_count": len(oversized),
        "total_over_limit": total_bytes > max_total_bytes,
        "total_bytes": total_bytes,
        "max_file_bytes": max_file_bytes,
        "max_total_bytes": max_total_bytes,
        "bubble_frame_max_bytes": FRAME_LIMIT,
        "external_reference_count": len(external),
        "dynamic_network_sink_count": len(unresolved),
        "external_scan": "static literals and recognized call sites",
        "runtime_network": "NO_DATA: static scan only",
        "files": details,
    }
    if state != GREEN:
        receipt["cause"] = "; ".join(causes)
    return receipt


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web-repo", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--max-file-bytes", type=int, required=True)
    parser.add_argument("--max-total-bytes", type=int, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    receipt = audit(
        web_repo=args.web_repo,
        artifact_root=args.artifact_root,
        manifest_path=args.manifest,
        max_file_bytes=args.max_file_bytes,
        max_total_bytes=args.max_total_bytes,
    )
    text = json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return {GREEN: 0, RED: 1, NO_DATA: 2}[receipt["state"]]


if __name__ == "__main__":
    raise SystemExit(main())
