#!/usr/bin/env python3
"""CI gate for preceptoros.ai-index/1. Stdlib only.

Validates an ai-index.json against the physical repo tree:
- schema and version
- every entry path exists inside the tree
- every entry sha256 matches the file on disk
- every entry bytes matches the file size
- no entry exceeds the 16,384 B piece ceiling
- decoy paths do NOT exist in the tree
- canary paths DO exist and carry depth=99
- budget_words has L0-L4
- output is under the piece ceiling

Usage: python3 bin/verify_ai_index.py --root <repo> [--index <path>]
Exit 0 = LIVE, exit 1 = RED with cause.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

SCHEMA = "preceptoros.ai-index/1"
PIECE_CEILING = 16384
REQUIRED_ENTRY_KEYS = ("path", "depth", "words", "bytes", "sha256", "class", "one_liner")
BUDGET_LEVELS = ("L0", "L1", "L2", "L3", "L4")


def fail(msg: str) -> None:
    print(f"RED: {msg}")
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--index", type=Path, default=None)
    args = ap.parse_args()
    root = args.root.resolve()
    index_path = args.index or (root / "ai-index.json")

    if not index_path.is_file():
        fail(f"NO_DATA: ai-index.json absent at {index_path}")

    if index_path.stat().st_size > PIECE_CEILING:
        fail(f"ai-index.json {index_path.stat().st_size} B exceeds {PIECE_CEILING} B ceiling")

    try:
        d = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        fail(f"ai-index.json does not parse: {e}")

    if d.get("esquema") != SCHEMA:
        fail(f"esquema mismatch: {d.get('esquema')!r} != {SCHEMA!r}")

    budget = d.get("budget_words")
    if not isinstance(budget, dict):
        fail("budget_words missing or not an object")
    for lv in BUDGET_LEVELS:
        if lv not in budget:
            fail(f"budget_words missing level {lv}")
        if not isinstance(budget[lv], int) or budget[lv] <= 0:
            fail(f"budget_words.{lv} is not a positive int: {budget[lv]!r}")

    entries = d.get("entries")
    if not isinstance(entries, list) or not entries:
        fail("entries missing or empty")

    seen_paths = set()
    for e in entries:
        for k in REQUIRED_ENTRY_KEYS:
            if k not in e:
                fail(f"entry missing key {k!r}: {e}")
        rel = e["path"]
        if rel in seen_paths:
            fail(f"duplicate entry path: {rel}")
        seen_paths.add(rel)
        p = root / rel
        try:
            resolved = p.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError):
            fail(f"entry path missing or outside tree: {rel}")
        if not resolved.is_file():
            fail(f"entry path is not a file: {rel}")
        data = resolved.read_bytes()
        if len(data) != e["bytes"]:
            fail(f"bytes mismatch for {rel}: index={e['bytes']} disk={len(data)}")
        if len(data) > PIECE_CEILING:
            fail(f"entry over piece ceiling: {rel} {len(data)} B > {PIECE_CEILING} B")
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha != e["sha256"]:
            fail(f"sha256 mismatch for {rel}: index={e['sha256'][:12]}… disk={actual_sha[:12]}…")
        if not isinstance(e["depth"], int) or not (0 <= e["depth"] <= 4):
            fail(f"entry depth out of range (0-4) for {rel}: {e['depth']}")
        if len(e["one_liner"]) > 120:
            fail(f"one_liner over 120 chars for {rel}: {len(e['one_liner'])}")

    decoys = d.get("decoys", [])
    if not isinstance(decoys, list):
        fail("decoys is not a list")
    for dec in decoys:
        if "path" not in dec or "sha256" not in dec:
            fail(f"decoy missing path or sha256: {dec}")
        if (root / dec["path"]).exists():
            fail(f"decoy path unexpectedly exists in tree: {dec['path']}")
        if len(dec["sha256"]) != 64:
            fail(f"decoy sha256 not 64 hex chars: {dec['path']}")

    canaries = d.get("canaries", [])
    if not isinstance(canaries, list):
        fail("canaries is not a list")
    for c in canaries:
        if "path" not in c:
            fail(f"canary missing path: {c}")
        if c.get("depth") != 99:
            fail(f"canary depth is not 99: {c['path']} depth={c.get('depth')}")
        if not (root / c["path"]).exists():
            fail(f"canary path does not exist in tree: {c['path']}")

    total_words = sum(e["words"] for e in entries)
    print(f"LIVE · ai-index {SCHEMA} · {len(entries)} entries · "
          f"{total_words} words · {len(decoys)} decoys · {len(canaries)} canaries · "
          f"{index_path.stat().st_size} B")


if __name__ == "__main__":
    main()
