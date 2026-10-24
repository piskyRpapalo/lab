#!/usr/bin/env python3
"""Read-only snapshot of local worktree metadata and listening process state."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=False).stdout


def _git(root, *args):
    return _run(["git", "-C", str(root), *args])


def _count_paths(blob):
    return len([part for part in blob.split(b"\0") if part])


def _valid_oid(value):
    return (isinstance(value, str) and len(value) in (40, 64)
            and all(char in "0123456789abcdefABCDEF" for char in value))


def _worktree(root, prior=None):
    prior = prior if isinstance(prior, dict) else None
    head = _git(root, "rev-parse", "HEAD").decode("ascii").strip()
    try:
        branch = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD").decode("utf-8").strip()
    except subprocess.CalledProcessError:
        branch = "DETACHED"
    staged = _count_paths(_git(root, "diff", "--cached", "--name-only", "-z"))
    unstaged = _count_paths(_git(root, "diff", "--name-only", "-z"))
    untracked = _count_paths(_git(root, "ls-files", "--others", "--exclude-standard", "-z"))
    if not prior:
        since = {"status": "NO_DATA", "cause": "no previous observation receipt"}
    else:
        old = prior.get("head")
        if not _valid_oid(old):
            since = {"status": "NO_DATA", "cause": "previous receipt has no valid object id"}
            return {"branch": branch or "DETACHED", "head": head,
                    "commits_since_previous": since, "staged_count": staged,
                    "unstaged_count": unstaged, "untracked_count": untracked}
        try:
            subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", old, head],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            commits = [row for row in _git(root, "rev-list", "--reverse", f"{old}..{head}")
                       .decode("ascii").splitlines() if row]
            since = {"status": "MEASURED", "from_head": old,
                     "count": len(commits), "commit_ids": commits}
        except (subprocess.CalledProcessError, ValueError, UnicodeDecodeError):
            since = {"status": "NO_DATA", "cause": "previous head is unavailable or not an ancestor"}
    return {"branch": branch or "DETACHED", "head": head,
            "commits_since_previous": since, "staged_count": staged,
            "unstaged_count": unstaged, "untracked_count": untracked}


def _log_state(path, prior=None):
    try:
        data = Path(path).read_bytes()
    except OSError:
        return {"status": "NO_DATA", "cause": "session log is unavailable or unreadable",
                "current": {"status": "NO_DATA", "cause": "session log is unavailable or unreadable"},
                "new_bytes": 0, "new_lines": 0, "text": ""}
    current = {"byte_length": len(data), "line_count": data.count(b"\n"),
               "sha256": hashlib.sha256(data).hexdigest()}
    if not isinstance(prior, dict) or not prior:
        return {"status": "NO_DATA", "cause": "no previous observation receipt",
                "current": current, "new_bytes": 0, "new_lines": 0, "text": ""}
    old = prior
    old_len = old.get("byte_length")
    if not isinstance(old_len, int) or old_len < 0 or old_len > len(data):
        return {"status": "NO_DATA", "cause": "previous log length is unavailable or log was shortened",
                "current": current, "new_bytes": 0, "new_lines": 0, "text": ""}
    prefix = data[:old_len]
    if hashlib.sha256(prefix).hexdigest() != old.get("sha256"):
        return {"status": "NO_DATA", "cause": "previous log bytes are not a prefix",
                "current": current, "new_bytes": 0, "new_lines": 0, "text": ""}
    suffix = data[old_len:]
    try:
        text = suffix.decode("utf-8")
    except UnicodeDecodeError:
        return {"status": "NO_DATA", "cause": "appended bytes are not valid UTF-8",
                "current": current, "new_bytes": len(suffix),
                "new_lines": suffix.count(b"\n"), "text": ""}
    return {"status": "MEASURED", "current": current, "new_bytes": len(suffix),
            "new_lines": suffix.count(b"\n"), "sha256": hashlib.sha256(suffix).hexdigest(),
            "text": text}


def _listener_ports(ports):
    try:
        lines = _run(["ss", "-H", "-ltn"]).decode("utf-8", "replace").splitlines()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return {str(port): {"status": "NO_DATA", "cause": "ss listener listing unavailable"}
                for port in ports}
    result = {}
    for port in ports:
        found = any(len(fields := row.split()) >= 5
                    and fields[-2].rsplit(":", 1)[-1] == str(port)
                    for row in lines)
        result[str(port)] = {"status": "MEASURED", "listening": found}
    return result


def _process_count(name):
    try:
        lines = _run(["ps", "-eo", "comm="]).decode("utf-8", "replace").splitlines()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return {"status": "NO_DATA", "cause": "process listing unavailable"}
    return {"status": "MEASURED", "count": sum(row.strip() == name for row in lines)}


def observe(web, app, claude_log, previous=None):
    previous = previous if isinstance(previous, dict) else {}
    prior_trees = previous.get("worktrees", {})
    if not isinstance(prior_trees, dict):
        prior_trees = {}
    log_result = _log_state(claude_log, previous.get("log"))
    trees = {}
    for label, root in (("web", web), ("app", app)):
        try:
            trees[label] = _worktree(root, prior_trees.get(label))
        except (OSError, subprocess.CalledProcessError, UnicodeError):
            trees[label] = {"status": "NO_DATA",
                            "cause": "worktree path or Git metadata is unavailable"}
    return {
        "schema": "lab.agent-observation/1",
        "observer": {"machine_role": "rack host; hostname withheld",
                     "inputs": "Git metadata, log bytes, ps and ss tables"},
        "observed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "worktrees": trees,
        "log": log_result["current"],
        "log_append": {key: value for key, value in log_result.items() if key != "current"},
        "preview_listeners": _listener_ports((18765, 18766)),
        "adb_bridges": {
            "processes": _process_count("adb"),
            "listeners": _listener_ports((5037, 5038)),
        },
        "fences": {"read_only": True, "network_used": False,
                   "connections_attempted": False, "worktree_writes": False},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web-worktree", required=True)
    parser.add_argument("--app-worktree", required=True)
    parser.add_argument("--claude-log", required=True)
    parser.add_argument("--previous-receipt", help="prior JSON receipt; read only")
    args = parser.parse_args()
    previous = json.loads(Path(args.previous_receipt).read_text(encoding="utf-8")) if args.previous_receipt else None
    result = observe(args.web_worktree, args.app_worktree, args.claude_log, previous)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
