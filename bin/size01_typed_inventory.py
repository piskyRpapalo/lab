#!/usr/bin/env python3
"""SIZE-01: measure tracked file sizes by explicitly declared artifact class."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

SCHEMA = "preceptoros.lab.size01-classified-bytes/1"
LIMITS = {"receipt_frame": (1024, False),
          "lexical_packet": (1024, False),
          "declared_piece": (16384, True),
          "raw_benchmark_artifact": (None, False)}


def _entry(root, name, kind):
    row = {"path_sha256": hashlib.sha256(name.encode("utf-8")).hexdigest()[:16],
           "category": kind or "UNCLASSIFIED"}
    rel = PurePosixPath(name)
    if not name or rel.is_absolute() or any(x in ("", ".", "..") for x in rel.parts) or "\\" in name:
        row.update(state="RED", cause="unsafe_path")
        return row
    try:
        path = root / name
        if any((root.joinpath(*rel.parts[:i])).is_symlink()
               for i in range(1, len(rel.parts) + 1)):
            raise ValueError("symbolic_link_disallowed")
        resolved = path.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
        if path.is_symlink() or not resolved.is_file():
            raise ValueError("not_regular_file")
        size = resolved.stat().st_size
    except (OSError, ValueError) as exc:
        row.update(state="NO_DATA", cause="missing_or_unsafe_file")
        return row
    row["bytes"] = size
    if kind not in LIMITS:
        row.update(state="NO_DATA", cause="explicit_classification_missing")
        return row
    ceiling, inclusive = LIMITS[kind]
    row["ceiling_bytes"] = ceiling
    if ceiling is None:
        row.update(state="OUT_OF_SCOPE", cause="artifact_frame_ceiling_not_applicable")
    elif size <= ceiling if inclusive else size < ceiling:
        row.update(state="GREEN", cause=None)
    else:
        row.update(state="RED", cause="declared_ceiling_exceeded")
    return row


def inspect(root, tracked, policy):
    if not isinstance(policy, dict) or set(policy) != {"schema", "assignments"} or policy["schema"] != SCHEMA:
        raise ValueError("closed_policy_required")
    assignments = policy["assignments"]
    if not isinstance(assignments, dict) or any(
            not isinstance(k, str) or not isinstance(v, str) or v not in LIMITS
            for k, v in assignments.items()):
        raise ValueError("invalid_policy_assignments")
    if not isinstance(tracked, list) or any(not isinstance(x, str) for x in tracked):
        raise ValueError("tracked_paths_required")
    if len(tracked) != len(set(tracked)):
        raise ValueError("duplicate_tracked_path")
    rows = [_entry(Path(root), name, assignments.get(name)) for name in tracked]
    missing = set(assignments) - set(tracked)
    tally = {state: sum(row["state"] == state for row in rows)
             for state in ("GREEN", "RED", "NO_DATA", "OUT_OF_SCOPE")}
    state = "RED" if tally["RED"] else "NO_DATA" if tally["NO_DATA"] or missing or not rows else "MEASURED_SCOPED"
    return {"schema": SCHEMA, "state": state, "files": len(rows),
            "classifications": len(assignments), "orphan_assignments": len(missing),
            "tally": tally, "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()
    try:
        policy = json.loads(args.policy.read_text(encoding="utf-8"))
        cmd = subprocess.run(["git", "ls-files", "-z"], cwd=args.repo, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, timeout=15, check=True)
        tracked = cmd.stdout.decode("utf-8").rstrip("\0").split("\0")
        result = inspect(args.repo, tracked, policy)
        if not args.details:
            result.pop("rows")
        code = 1 if result["state"] == "RED" else 2 if result["state"] == "NO_DATA" else 0
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        result = {"schema": SCHEMA, "state": "NO_DATA", "cause": type(exc).__name__}
        code = 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
