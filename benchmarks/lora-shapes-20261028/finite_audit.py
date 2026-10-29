"""Inspect F32 adapter payloads for non-finite values, without model loading."""
import argparse
import array
import datetime
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

MAX_HEADER = 16 * 1024 * 1024
CHUNK = 1024 * 1024


def inspect(path):
    sha = hashlib.sha256()
    with path.open('rb') as source:
        prefix = source.read(8)
        if len(prefix) != 8:
            raise ValueError('short_header')
        header_size = struct.unpack('<Q', prefix)[0]
        if header_size == 0 or header_size > MAX_HEADER or header_size > path.stat().st_size - 8:
            raise ValueError('invalid_header_size')
        raw = source.read(header_size)
        header = json.loads(raw)
        if not isinstance(header, dict):
            raise ValueError('invalid_header')
        body_size = path.stat().st_size - 8 - header_size
        segments = []
        for name, item in header.items():
            if name == '__metadata__':
                continue
            if not isinstance(item, dict) or item.get('dtype') != 'F32':
                raise ValueError('unsupported_dtype')
            shape, offsets = item.get('shape'), item.get('data_offsets')
            if (not isinstance(shape, list) or any(type(x) is not int or x < 0 for x in shape)
                    or not isinstance(offsets, list) or len(offsets) != 2
                    or any(type(x) is not int or x < 0 for x in offsets)):
                raise ValueError('invalid_shape_or_offsets')
            start, end = offsets
            if end < start or end > body_size or end - start != math.prod(shape) * 4:
                raise ValueError('offset_shape_mismatch')
            segments.append((start, end))
        if not segments:
            raise ValueError('no_tensors')
        segments.sort()
        cursor = 0
        for start, end in segments:
            if start != cursor:
                raise ValueError('overlap_or_gap')
            cursor = end
        if cursor != body_size:
            raise ValueError('trailing_or_missing_data')
        sha.update(prefix)
        sha.update(raw)
        finite = nan = infinity = 0
        remaining = body_size
        while remaining:
            block = source.read(min(CHUNK, remaining))
            if not block or len(block) % 4:
                raise ValueError('truncated_data')
            sha.update(block)
            bits = array.array('I')
            if bits.itemsize != 4:
                raise ValueError('unsupported_integer_width')
            bits.frombytes(block)
            if sys.byteorder != 'little':
                bits.byteswap()
            for word in bits:
                if word & 0x7f800000 != 0x7f800000:
                    finite += 1
                elif word & 0x007fffff:
                    nan += 1
                else:
                    infinity += 1
            remaining -= len(block)
    return {'sha256': sha.hexdigest(), 'bytes': path.stat().st_size, 'tensors': len(segments),
            'finite_values': finite, 'nan_values': nan, 'infinite_values': infinity}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adapters-root', type=Path, required=True)
    args = parser.parse_args()
    if not args.adapters_root.is_dir():
        print(json.dumps({'state': 'NO_DATA', 'cause': 'adapter directory unavailable'}))
        return
    paths = sorted(args.adapters_root.rglob('adapter_model.safetensors'))
    rows, failures = [], 0
    for path in paths:
        try:
            rows.append(inspect(path))
        except (OSError, ValueError, TypeError, json.JSONDecodeError, struct.error):
            failures += 1
    rows.sort(key=lambda row: row['sha256'])
    print(json.dumps({'date_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
                      'state': 'MEASURED' if paths and not failures else 'NO_DATA',
                      'cause': None if paths and not failures else 'no files or unsupported or invalid file',
                      'files_seen': len(paths), 'files_inspected': len(rows), 'files_unavailable': failures,
                      'rows': rows, 'scope': 'F32 payload finiteness; not authenticity or model quality'},
                     indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
