#!/usr/bin/env python3
"""Generate preceptoros.ai-index/1 from a repo tree. Stdlib only.

Measures every indexed file against the working tree: words, bytes, sha256,
class, one_liner (first markdown heading or first non-empty line, capped).
Emits decoys (fake paths with fake sha256) and canaries (real paths at
depth=99) for red-team reading signals.

Usage: python3 bin/gen_ai_index.py --root <repo> --output <path>
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "preceptoros.ai-index/1"
VERSION = "1.0.0"
PIECE_CEILING = 16384
ONE_LINER_MAX = 120
RAG_PROMPT_MAX = 256

BUDGET_WORDS = {"L0": 700, "L1": 3000, "L2": 6000, "L3": 20000, "L4": 1024}

CLASS_RULES = [
    (re.compile(r"\.py$"), "code"),
    (re.compile(r"\.mjs$"), "code"),
    (re.compile(r"\.js$"), "code"),
    (re.compile(r"\.json$"), "data"),
    (re.compile(r"\.md$"), "doc"),
    (re.compile(r"\.txt$"), "doc"),
    (re.compile(r"\.css$"), "style"),
    (re.compile(r"\.html$"), "markup"),
    (re.compile(r"\.sh$"), "script"),
    (re.compile(r"\.yml$"), "config"),
    (re.compile(r"\.yaml$"), "config"),
]

DEPTH_BY_DIR = [
    ("README", 0),
    ("llms.txt", 0),
    ("AGENTS.md", 1),
    ("STATE.md", 1),
    ("01-governance", 1),
    ("02-legislation", 1),
    ("03-github-flow", 1),
    ("04-measurement", 1),
    ("05-contracts", 2),
    ("06-software", 2),
    ("07-hardware", 2),
    ("08-ai-fluency", 2),
    ("09-lore", 2),
    ("10-collisions", 2),
    ("11-repos", 2),
    ("12-schema", 2),
    ("benchmarks", 2),
    ("bin/", 2),
    ("atlas/", 2),
    ("tests/", 3),
    ("test_", 3),
    ("public/", 3),
    ("docs/", 2),
    ("proposals/", 3),
]

EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".pytest_cache", ".mypy_cache", "historial",
    ".github", "coverage", ".tox", "Cuarentena",
}

EXCLUDE_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml"}

INDEXED_FILES = [
    "README.md", "llms.txt", "AGENTS.md", "STATE.md",
    "01-governance.md", "02-legislation.md", "03-github-flow.md",
    "04-measurement.md", "05-contracts.md", "06-software.md",
    "07-hardware.md", "08-ai-fluency.md", "09-lore.md",
    "10-collisions.md", "11-repos.md", "12-schema.md",
    "DISAGREEMENTS.md", "ai-index.json",
]


def classify(path: str) -> str:
    for rx, cls in CLASS_RULES:
        if rx.search(path):
            return cls
    return "other"


def depth_of(path: str) -> int:
    name = Path(path).name
    for prefix, depth in DEPTH_BY_DIR:
        if prefix.endswith("/"):
            if path.startswith(prefix):
                return depth
        elif name == prefix or path.startswith(prefix):
            return depth
    return 3


def one_liner(text: str, path: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^#{1,6}\s+(.+)$", line)
        if m:
            line = m.group(1).strip()
        line = re.sub(r"[*_`>\-]", "", line).strip()
        line = re.sub(r"\s+", " ", line)
        if line:
            return line[:ONE_LINER_MAX]
    return f"({Path(path).suffix or 'file'})"


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_files(root: Path, skipped_over_ceiling: list) -> list:
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if Path(rel).name in EXCLUDE_FILES:
            continue
        if rel not in INDEXED_FILES:
            continue
        if p.stat().st_size > PIECE_CEILING:
            skipped_over_ceiling.append(rel)
            continue
        files.append(rel)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--output", type=Path, default=None)
    ap.add_argument("--decoys", type=int, default=2)
    ap.add_argument("--canaries", type=int, default=1)
    ap.add_argument("--indexed", type=str, default=None,
                    help="comma-separated file list overriding INDEXED_FILES")
    args = ap.parse_args()
    root = args.root.resolve()

    global INDEXED_FILES
    if args.indexed:
        INDEXED_FILES = [f.strip() for f in args.indexed.split(",") if f.strip()]

    skipped_over_ceiling = []
    entries = []
    for rel in collect_files(root, skipped_over_ceiling):
        p = root / rel
        data = p.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = ""
        words = len(text.split()) if text else 0
        entries.append({
            "path": rel,
            "depth": depth_of(rel),
            "words": words,
            "bytes": len(data),
            "sha256": sha256_of(data),
            "class": classify(rel),
            "one_liner": one_liner(text, rel),
        })

    decoys = []
    for i in range(args.decoys):
        fake_path = f"docs/internal-roadmap-{i}.md" if i == 0 else f"admin_debug_{i}.md"
        decoys.append({
            "path": fake_path,
            "sha256": f"{i}" * 64,
            "reason": "decoy: path does not exist; citing it is a cheater signal",
        })

    canaries = []
    md_files = [e for e in entries if e["path"].endswith(".md")]
    for i in range(min(args.canaries, len(md_files))):
        canaries.append({
            "path": md_files[i]["path"],
            "depth": 99,
            "reason": "canary: reading this file at an agent's declared depth is a depth-violation alert",
        })

    index = {
        "esquema": SCHEMA,
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "lab/bin/gen_ai_index.py (stdlib)",
        "budget_words": BUDGET_WORDS,
        "entries": entries,
        "decoys": decoys,
        "canaries": canaries,
    }

    out = args.output or (root / "ai-index.json")
    out.write_text(json.dumps(index, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    total_words = sum(e["words"] for e in entries)
    print(f"ai-index: {len(entries)} entries, {total_words} words total, "
          f"{len(decoys)} decoys, {len(canaries)} canaries -> {out} ({out.stat().st_size} B)")
    if skipped_over_ceiling:
        print(f"SKIPPED (over {PIECE_CEILING} B piece ceiling): {', '.join(skipped_over_ceiling)}")
    if out.stat().st_size > PIECE_CEILING:
        raise SystemExit(f"ERROR: ai-index.json {out.stat().st_size} B exceeds {PIECE_CEILING} B ceiling")


if __name__ == "__main__":
    main()
