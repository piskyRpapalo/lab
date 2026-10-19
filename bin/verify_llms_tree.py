#!/usr/bin/env python3
"""Check every path declared in the INDEX line against the physical tree."""
import argparse
import re
from pathlib import Path

INDEX_RE = re.compile(r"^INDEX:\s*(.+)$", re.MULTILINE)
ITEM_RE = re.compile(r"\s*([^;,#\s]+)(?:#L([1-9][0-9]*)\.?)?\s*")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    index_file = root / "llms.txt"
    if not index_file.is_file():
        raise SystemExit("NO_DATA: llms.txt is absent")
    text = index_file.read_text(encoding="utf-8")
    rows = INDEX_RE.findall(text)
    if len(rows) != 1:
        raise SystemExit(f"ERROR: expected one INDEX line, found {len(rows)}")
    entries = [part.strip() for part in rows[0].split(";") if part.strip()]
    if not entries:
        raise SystemExit("ERROR: INDEX is empty")
    failures = []
    for entry in entries:
        match = ITEM_RE.fullmatch(entry)
        if not match:
            failures.append(f"invalid index item: {entry}")
            continue
        rel, line = match.groups()
        candidate = root / rel
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError):
            failures.append(f"missing or outside tree: {rel}")
            continue
        if not resolved.is_file():
            failures.append(f"not a file: {rel}")
            continue
        if line:
            try:
                line_count = len(resolved.read_text(encoding="utf-8").splitlines())
            except (OSError, UnicodeError):
                failures.append(f"unreadable text anchor: {rel}")
                continue
            if int(line) > line_count:
                failures.append(f"line anchor beyond file: {rel}#L{line}")
    if failures:
        print("\n".join(failures))
        raise SystemExit(1)
    print(f"LIVE · {len(entries)} indexed paths resolve inside the physical tree")


if __name__ == "__main__":
    main()
