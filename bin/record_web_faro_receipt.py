#!/usr/bin/env python3
"""Turn a completed FARO transcript into a source-pinned freshness receipt."""
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
from pathlib import Path

GREEN, RED, NO_DATA = "GREEN", "RED", "NO_DATA"
MAIN_REF = "refs/remotes/origin/main"
LABELS = {
    "compared": r"ficheros comparados",
    "equal": r"LIVE iguales",
    "changed": r"DRIFT distintos",
    "missing": r"DRIFT ausentes",
    "network_errors": r"ERRORES de red",
}


def _git(repo: Path, *args: str) -> bytes:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=30)
    if proc.returncode:
        raise ValueError("git measurement failed")
    return proc.stdout


def _public_source(repo: Path, commit: str) -> tuple[dict[str, bytes], str]:
    raw = _git(repo, "archive", "--format=tar", commit, "public")
    files = {}
    with tarfile.open(fileobj=BytesIO(raw), mode="r:") as archive:
        for member in archive.getmembers():
            if member.isdir():
                continue
            if not member.isfile() or not member.name.startswith("public/"):
                raise ValueError("unsupported public tree entry")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError("unreadable public tree entry")
            files[member.name.removeprefix("public/")] = source.read()
    if not files:
        raise ValueError("main public tree is empty")
    h = hashlib.sha256()
    for path, body in sorted(files.items()):
        name = path.encode("utf-8")
        h.update(len(name).to_bytes(4, "big"))
        h.update(name)
        h.update(len(body).to_bytes(8, "big"))
        h.update(hashlib.sha256(body).digest())
    return files, h.hexdigest()


def _summary(text: str) -> dict[str, int]:
    result = {}
    for key, label in LABELS.items():
        match = re.search(r"(?im)^\s*" + label + r"\s*:\s*(\d+)\s*$", text)
        if match is None:
            raise ValueError("FARO summary is incomplete")
        result[key] = int(match.group(1))
    return result


def record(*, web_repo: Path, faro_output: Path, faro_exit_code: int,
           deployment: str, observed_at: str | None = None) -> dict[str, object]:
    try:
        if faro_exit_code not in {0, 1, 2}:
            raise ValueError("FARO exit code must be 0, 1, or 2")
        head = _git(web_repo, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
        main = _git(web_repo, "rev-parse", "--verify", f"{MAIN_REF}^{{commit}}").decode().strip()
        dirty = _git(web_repo, "status", "--porcelain", "--untracked-files=all").decode()
        if head != main:
            raise ValueError("checkout HEAD does not equal fetched origin/main")
        if dirty:
            raise ValueError("source checkout is not clean")
        files, tree_hash = _public_source(web_repo, main)
        faro_script = _git(web_repo, "show", f"{main}:atlas/faro.py")
        transcript = faro_output.read_bytes()
        text = transcript.decode("utf-8")
        counts = _summary(text)
    except (OSError, UnicodeError, subprocess.SubprocessError, ValueError, tarfile.TarError) as exc:
        return {"state": NO_DATA, "cause": str(exc)[:240]}

    expected = len(files)
    causes = []
    if faro_exit_code == 2:
        causes.append("FARO reported network or measurement errors")
    elif faro_exit_code == 1:
        causes.append("FARO reported live drift")
    elif faro_exit_code != 0:
        causes.append("FARO exit status is not green")
    if counts["compared"] != expected:
        causes.append("compared count differs from main public file count")
    if counts["equal"] != expected:
        causes.append("live equal count differs from main public file count")
    if counts["changed"] or counts["missing"] or counts["network_errors"]:
        causes.append("FARO summary contains drift or errors")
    state = GREEN if not causes else (NO_DATA if faro_exit_code == 2 else RED)
    return {
        "schema": "preceptoros.lab.web-faro-freshness/1",
        "state": state,
        "cause": "; ".join(causes) if causes else None,
        "observed_at": observed_at or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "deployment": deployment,
        "source_ref": MAIN_REF,
        "source_commit": main,
        "public_tree_sha256": tree_hash,
        "public_file_count": expected,
        "faro_script_sha256": hashlib.sha256(faro_script).hexdigest(),
        "faro_exit_code": faro_exit_code,
        **counts,
        "transcript_sha256": hashlib.sha256(transcript).hexdigest(),
        "yardstick": "atlas/faro.py byte comparison; this tool parses and records its completed output",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web-repo", type=Path, required=True)
    parser.add_argument("--faro-output", type=Path, required=True)
    parser.add_argument("--faro-exit-code", type=int, required=True)
    parser.add_argument("--deployment", required=True)
    parser.add_argument("--observed-at")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = record(web_repo=args.web_repo, faro_output=args.faro_output,
                    faro_exit_code=args.faro_exit_code, deployment=args.deployment,
                    observed_at=args.observed_at)
    rendered = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return {GREEN: 0, RED: 1, NO_DATA: 2}[result["state"]]


if __name__ == "__main__":
    raise SystemExit(main())
