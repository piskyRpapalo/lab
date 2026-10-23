#!/usr/bin/env python3
"""Compare a classified graphic inventory with its declared Git snapshot. Read-only."""
import argparse
from collections import Counter
from pathlib import Path
import re
import subprocess

CEILING = 16384
FOLDERS = ('public/game', 'public/assets')
ROW = re.compile(r'\| ([\w.-]+\.(?:js|css)) \| (\d+) \| ([CRD]) \| ([BLVH]) \|')


def verify(root, inventory):
    data = inventory.read_bytes()
    if len(data) >= CEILING:
        raise ValueError(f'inventory is {len(data)} B; expected < {CEILING} B')
    text = data.decode('utf-8')
    base = re.search(r'origin/main `([0-9a-f]{7,40})`', text)
    if not base:
        raise ValueError('missing declared Git snapshot')
    ref = base.group(1)
    folder = None
    rows, classes = {}, Counter()
    for line in text.splitlines():
        if line.startswith('### public/'):
            folder = line.split()[1].rstrip('/')
            if folder not in FOLDERS:
                raise ValueError('unknown inventory folder')
        match = ROW.fullmatch(line)
        if not match:
            continue
        name, size, category, role = match.groups()
        if folder not in FOLDERS:
            raise ValueError('file row outside a declared folder')
        path = f'{folder}/{name}'
        if path in rows:
            raise ValueError(f'duplicate file: {path}')
        if (category == 'R' and role != 'V') or (category == 'D' and role != 'H') or (category == 'C' and role == 'V'):
            raise ValueError(f'inconsistent class/role: {path}')
        rows[path] = int(size)
        classes[category] += 1
    listing = subprocess.run(['git', '-C', str(root), 'ls-tree', '-r', '-l', ref, *FOLDERS],
                             check=True, capture_output=True, text=True).stdout
    expected = {}
    for line in listing.splitlines():
        meta, path = line.split('\t')
        if Path(path).suffix in ('.js', '.css'):
            expected[path] = int(meta.split()[-1])
    if not expected:
        raise ValueError('declared Git snapshot has no JS/CSS modules')
    if rows != expected:
        changed = sorted(p for p in set(rows) | set(expected) if rows.get(p) != expected.get(p))
        raise ValueError('inventory differs from measured tree: ' + ', '.join(changed))
    return len(rows), sum(rows.values()), len(data), ref, classes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    args = parser.parse_args()
    try:
        count, total, size, ref, classes = verify(args.root, args.inventory)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'RED: {error}\n')
    print(f'GREEN · {count} unique files · {total} B · doc {size} B · base {ref} · '
          f'C={classes["C"]} R={classes["R"]} D={classes["D"]}')


if __name__ == '__main__':
    main()
