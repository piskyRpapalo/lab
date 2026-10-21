#!/usr/bin/env python3
"""Measure declared reading targets and fail closed on missing budgets."""
import argparse
import hashlib
import json
from pathlib import Path

PIECE_LIMIT = 16384


def inspect(manifest, roots):
    results = []
    for depth in manifest.get("depths", []):
        number = depth.get("depth")
        targets = depth.get("targets", [])
        total = 0
        digest = hashlib.sha256()
        cause = None
        for target in targets:
            repo = target.get("repo")
            relative = target.get("path")
            if repo not in roots or not isinstance(relative, str):
                cause = "target_root_or_path_missing"
                break
            root = roots[repo].resolve()
            path = (root / relative).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                cause = "target_escapes_repository"
                break
            if not path.is_file():
                cause = "target_missing"
                break
            data = path.read_bytes()
            size = len(data)
            total += size
            digest.update(repo.encode("utf-8") + b"/" + relative.encode("utf-8") + b"\0" + data)
            if size > PIECE_LIMIT:
                cause = "piece_limit_exceeded"
                break
        budget = depth.get("budget_bytes")
        if cause:
            status = "RED"
        elif not isinstance(number, int) or number < 0 or not targets:
            status, cause = "NO_DATA", "depth_or_targets_undeclared"
        elif budget is None:
            status, cause = "NO_DATA", depth.get("budget_cause", "aggregate_budget_undeclared")
        elif not isinstance(budget, int) or budget <= 0:
            status, cause = "RED", "invalid_budget"
        elif total > budget:
            status, cause = "RED", "aggregate_budget_exceeded"
        else:
            status = "LIVE"
        results.append({"policy": depth.get("policy", "NO_DATA"),
                        "depth": number, "status": status, "bytes": total,
                        "budget_bytes": budget, "cause": cause,
                        "targets": len(targets), "sha256": digest.hexdigest()})
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repo-root", action="append", default=[], metavar="NAME=PATH")
    parser.add_argument("--machine", required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    roots = {}
    for item in args.repo_root:
        name, separator, path = item.partition("=")
        if not separator or not name or name in roots:
            raise SystemExit("RED: invalid or duplicate repository root")
        roots[name] = Path(path)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SystemExit(f"NO_DATA: manifest_unreadable:{type(error).__name__}")
    if manifest.get("schema") != "declared-depth-targets/1":
        raise SystemExit("RED: unsupported manifest schema")
    results = inspect(manifest, roots)
    receipt = {"machine": args.machine, "date": args.date,
               "sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
               "depths": [[row["policy"], row["depth"], row["status"], row["bytes"],
                           row["budget_bytes"], row["targets"], row["sha256"], row["cause"]]
                          for row in results]}
    print(json.dumps(receipt, ensure_ascii=True, separators=(",", ":")))
    if any(result["status"] == "RED" for result in results):
        raise SystemExit(1)
    if any(result["status"] == "NO_DATA" for result in results):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
