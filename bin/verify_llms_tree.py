#!/usr/bin/env python3
"""Check INDEX paths, DEPTH budgets, and per-file ceilings against the tree."""
import argparse
import re
from pathlib import Path

INDEX_RE = re.compile(r"^INDEX:\s*(.+)$", re.MULTILINE)
DEPTH_RE = re.compile(r"^DEPTH:\s*(.+)$", re.MULTILINE)
BUDGET_RE = re.compile(r"^BUDGET:\s*(.+)$", re.MULTILINE)
ITEM_RE = re.compile(r"\s*([^;,\s#]+)(?:#L([1-9][0-9]*))?\s*")
PIECE_CEILING = 16384


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
    entries = [part.strip().rstrip(".") for part in rows[0].split(";") if part.strip()]
    if not entries:
        raise SystemExit("ERROR: INDEX is empty")
    failures = []
    total_bytes = 0
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
        size = resolved.stat().st_size
        total_bytes += size
        if size > PIECE_CEILING:
            failures.append(f"over piece ceiling: {rel} {size} B > {PIECE_CEILING} B")
        if line:
            try:
                line_count = len(resolved.read_text(encoding="utf-8").splitlines())
            except (OSError, UnicodeError):
                failures.append(f"unreadable text anchor: {rel}")
                continue
            if int(line) > line_count:
                failures.append(f"line anchor beyond file: {rel}#L{line}")
    depth_rows = DEPTH_RE.findall(text)
    if len(depth_rows) > 1:
        failures.append(f"ERROR: expected at most one DEPTH line, found {len(depth_rows)}")
    budget_rows = BUDGET_RE.findall(text)
    if budget_rows:
        budget_token = budget_rows[0].split(";")[0].strip().rstrip(".")
        budget_digits = re.match(r"(\d+)", budget_token)
        if not budget_digits:
            failures.append(f"invalid BUDGET value: {budget_token}")
            budget = 0
        else:
            budget = int(budget_digits.group(1))
        if total_bytes > budget:
            failures.append(f"over depth budget: INDEX totals {total_bytes} B > {budget} B")
        budget_note = f" · depth budget {total_bytes} B <= {budget} B"
    else:
        budget_note = f" · INDEX total {total_bytes} B (no BUDGET line declared)"
    if failures:
        print("\n".join(failures))
        raise SystemExit(1)
    print(f"LIVE · {len(entries)} indexed paths resolve inside the physical tree{budget_note}")


if __name__ == "__main__":
    main()
