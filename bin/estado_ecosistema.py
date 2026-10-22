#!/usr/bin/env python3
"""Emit a bounded, read-only ecosystem state receipt from supplied checkouts."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

BAN_WORDS = ("oraculo", "notario", "depin", "token", "moneda", "clearing", "magia")
CEILING_FILES = ("AGENTS.md", "docs/AGENTS.md", "02-legislation.md", "study/02-legislation.md")
CEILING_RX = re.compile(r"25\s*MiB|16[, ]384\s*B|16\s*KiB|1[, ]024\s*B|153[, ]600\s*B", re.I)
ROUTE_RX = re.compile(r"shell_entries=(\d+) shell_unique=(\d+) shell_duplicates=(\d+)")


def run_git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def parse_pair(value):
    label, sep, raw_path = value.partition("=")
    if not sep or not re.fullmatch(r"[a-z][a-z0-9_-]*", label) or not raw_path:
        raise ValueError("repo must be label=path")
    return label, Path(raw_path)


def repo_state(label, root):
    if not root.is_dir():
        return {"repo": label, "status": "NO_DATA", "cause": "checkout absent"}
    try:
        branch = "main"
        try:
            main = run_git(root, "rev-parse", "--verify", "refs/remotes/origin/main")
        except subprocess.CalledProcessError:
            branch = "master"
            main = run_git(root, "rev-parse", "--verify", "refs/remotes/origin/master")
        behind, ahead = map(int, run_git(root, "rev-list", "--left-right", "--count",
                                         "origin/" + branch + "...HEAD").split())
        dirty = bool(run_git(root, "status", "--porcelain"))
    except (subprocess.CalledProcessError, ValueError):
        return {"repo": label, "status": "NO_DATA", "cause": "git state unavailable"}
    return {"repo": label, "status": "MEASURED", "base_branch": branch, "base": main[:8],
            "behind": behind, "ahead": ahead, "dirty": dirty}


def route_state(root, document=None):
    counter = root / "bin" / "contar_rutas.py"
    if not counter.is_file():
        return {"status": "NO_DATA", "cause": "route counter absent"}
    try:
        output = subprocess.run([sys.executable, str(counter)], check=True, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    except subprocess.CalledProcessError:
        return {"status": "NO_DATA", "cause": "route counter failed"}
    match = ROUTE_RX.search(output)
    if not match:
        return {"status": "NO_DATA", "cause": "route counter output unrecognized"}
    names = ("shell_entries", "shell_unique", "shell_duplicates")
    result = {"status": "MEASURED", "source": "public/sw-listas.js",
              **dict(zip(names, map(int, match.groups())))}
    if document:
        try:
            subprocess.run([sys.executable, str(counter), "--check-doc", str(document)],
                           check=True, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
            result["document"] = "MATCH"
        except subprocess.CalledProcessError:
            result["status"] = "RED"
            result["document"] = "MISMATCH"
    return result


def ceiling_refs(label, root):
    found = []
    for rel in CEILING_FILES:
        path = root / rel
        if not path.is_file():
            continue
        values = sorted(set(CEILING_RX.findall(path.read_text(encoding="utf-8"))))
        if values:
            found.append({"repo": label, "file": rel, "values": values})
    return found


def scrub_file(label, root, rel):
    path = root / rel
    if not path.is_file():
        return {"repo": label, "file": rel, "status": "NO_DATA", "cause": "file absent"}
    try:
        path.resolve(strict=True).relative_to(root.resolve())
    except (OSError, ValueError):
        return {"repo": label, "file": rel, "status": "NO_DATA", "cause": "path outside checkout"}
    text = path.read_text(encoding="utf-8", errors="replace").casefold()
    hits = sum(len(re.findall(r"(?<![\w])" + re.escape(word) + r"(?![\w])", text))
               for word in BAN_WORDS)
    return {"repo": label, "file": rel, "status": "RED" if hits else "GREEN", "hits": hits}


def overall_status(repos, routes, scrub):
    statuses = [row.get("status") for row in repos + [routes] + scrub]
    if "RED" in statuses:
        return "RED"
    if "NO_DATA" in statuses or not scrub:
        return "NO_DATA"
    return "MEASURED"


def receipt(args):
    repos = [parse_pair(item) for item in args.repo]
    labels = [label for label, _ in repos]
    if len(labels) != len(set(labels)):
        raise ValueError("repo labels must be unique")
    repo_rows = [repo_state(label, root) for label, root in repos]
    route_row = (route_state(args.web_root, args.route_doc) if args.web_root else
                 {"status": "NO_DATA", "cause": "web checkout not supplied"})
    scrub_rows = [scrub_file(label, root, rel) for label, rel in args.scrub_file
                  for repo_label, root in repos if label == repo_label]
    if not scrub_rows:
        scrub_rows = [{"status": "NO_DATA", "cause": "no scrub paths supplied"}]
    report = {
        "date": args.date,
        "machine": args.machine,
        "status": overall_status(repo_rows, route_row, scrub_rows),
        "repos": repo_rows,
        "routes": route_row,
        "ceiling_refs": [[row["repo"], row["file"], row["values"]]
                         for label, root in repos for row in ceiling_refs(label, root)],
        "scrub": [[row.get("repo"), row.get("file"), row.get("status"), row.get("hits", 0)]
                  for row in scrub_rows],
    }
    encoded = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    report["sha256"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    encoded = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if len(encoded.encode("utf-8")) >= 1024:
        raise ValueError("receipt reaches the 1,024 B ceiling")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="measurement date in YYYY-MM-DD")
    parser.add_argument("--machine", choices=("local", "mobile", "rack"), default="local")
    parser.add_argument("--repo", action="append", default=[], help="label=checkout path")
    parser.add_argument("--web-root", type=Path)
    parser.add_argument("--route-doc", type=Path)
    parser.add_argument("--scrub-file", action="append", default=[], metavar="LABEL:RELATIVE_PATH")
    args = parser.parse_args()
    try:
        date.fromisoformat(args.date)
        args.scrub_file = [item.split(":", 1) for item in args.scrub_file]
        if any(len(item) != 2 for item in args.scrub_file):
            raise ValueError("scrub file must be LABEL:RELATIVE_PATH")
        repo_labels = {label for label, _ in map(parse_pair, args.repo)}
        if any(label not in repo_labels for label, _ in args.scrub_file):
            raise ValueError("scrub label has no supplied repo")
        print(json.dumps(receipt(args), sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    except (OSError, ValueError) as error:
        print("NO_DATA: " + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
