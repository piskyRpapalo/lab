#!/usr/bin/env python3
"""Measure the app voice installer dry-run without changing the app home."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path

SCHEMA = "preceptoros.lab.a11y-install/1"
CEILING = 1024
FILE_LIMIT = 16384
FILES = ("bin/instalar-pc", "bin/instalar-pc-voz")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(app_root):
    root = Path(app_root)
    paths = [root / name for name in FILES]
    if not root.is_dir() or any(not path.is_file() for path in paths):
        return {"schema": SCHEMA, "state": "NO_DATA", "cause": "app root or voice installer missing"}
    causes = []
    files = []
    for path in paths:
        size = path.stat().st_size
        executable = os.access(path, os.X_OK)
        syntax = subprocess.run(["bash", "-n", str(path)], capture_output=True, timeout=5).returncode == 0
        files.append({"bytes": size, "sha256": _digest(path)})
        if size >= FILE_LIMIT or not executable or not syntax:
            causes.append("installer file failed size, executable, or shell syntax check")
    writes = None
    marker = False
    exit_code = None
    with tempfile.TemporaryDirectory(prefix="a11y-install-check-") as home:
        env = dict(os.environ, HOME=home, PRECEPTOROS_VOICE_SILENT="1")
        try:
            run = subprocess.run([str(paths[0]), "--voz", "--dry-run"], cwd=root,
                                 env=env, capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            causes.append("voice dry-run unavailable or timed out")
        else:
            exit_code = run.returncode
            marker = "DRY_RUN" in run.stdout
            writes = any(Path(home).rglob("*"))
            if exit_code != 0 or not marker:
                causes.append("voice dry-run did not return its explicit marker")
            if writes:
                causes.append("voice dry-run wrote into its isolated home")
    state = "RED" if causes else "GREEN"
    result = {"schema": SCHEMA, "state": state, "files": files,
              "checks": {"syntax_executable_size": not any("installer file" in c for c in causes),
                         "dry_run_exit": exit_code, "dry_run_marker": marker,
                         "writes": None if writes is None else int(bool(writes))},
              "runtime": {"machine": platform.machine(), "python": platform.python_version()},
              "observed_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    if causes:
        result["cause"] = "; ".join(causes)
    if len(canonical(result).encode("utf-8")) >= CEILING:
        return {"schema": SCHEMA, "state": "RED", "cause": "receipt reached 1,024-byte ceiling"}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", required=True, type=Path)
    args = parser.parse_args(argv)
    result = verify(args.app_root)
    print(canonical(result))
    return 0 if result["state"] == "GREEN" else 1 if result["state"] == "RED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
