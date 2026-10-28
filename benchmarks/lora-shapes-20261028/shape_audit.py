"""Compare local adapter tensor headers with local base headers without loading weights."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import struct

MAX_HEADER = 16 * 1024 * 1024


def read_header(path):
    with path.open('rb') as source:
        prefix = source.read(8)
        if len(prefix) != 8:
            raise ValueError('short_header')
        size = struct.unpack('<Q', prefix)[0]
        if size == 0 or size > MAX_HEADER or size > path.stat().st_size - 8:
            raise ValueError('invalid_header_size')
        raw = source.read(size)
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError('invalid_header')
    return data, hashlib.sha256(raw).hexdigest()


def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def scan(base, adapters):
    shards = sorted(base.glob('*.safetensors'))
    weights = sorted(adapters.rglob('adapter_model.safetensors'))
    if not shards or not weights:
        raise ValueError('base_shards_or_adapters_missing')
    base_shapes, shard_hashes = {}, []
    for path in shards:
        header, header_hash = read_header(path)
        shard_hashes.append(header_hash)
        for name, info in header.items():
            if name == '__metadata__':
                continue
            if name in base_shapes or not isinstance(info, dict) or not isinstance(info.get('shape'), list):
                raise ValueError('invalid_or_duplicate_base_tensor')
            base_shapes[name] = info['shape']
    rows = []
    for path in weights:
        header, header_hash = read_header(path)
        pairs, unexpected = {}, 0
        for name, info in header.items():
            if name == '__metadata__':
                continue
            prefix = 'base_model.model.'
            if not name.startswith(prefix) or not isinstance(info, dict):
                unexpected += 1
                continue
            tail = name[len(prefix):]
            if tail.endswith('.lora_A.weight'):
                key, side = tail[:-len('.lora_A.weight')] + '.weight', 'A'
            elif tail.endswith('.lora_B.weight'):
                key, side = tail[:-len('.lora_B.weight')] + '.weight', 'B'
            else:
                unexpected += 1
                continue
            pairs.setdefault(key, {})[side] = info.get('shape')
        matching = missing_base = malformed = mismatch = 0
        for key, pair in pairs.items():
            a, b, target = pair.get('A'), pair.get('B'), base_shapes.get(key)
            if not isinstance(a, list) or not isinstance(b, list) or len(a) != 2 or len(b) != 2:
                malformed += 1
            elif target is None:
                missing_base += 1
            elif len(target) != 2 or a[1] != target[1] or b[0] != target[0] or a[0] != b[1]:
                mismatch += 1
            else:
                matching += 1
        rows.append({'adapter_sha256': file_hash(path), 'header_sha256': header_hash,
                     'pairs': len(pairs), 'matching_shapes': matching, 'missing_base': missing_base,
                     'invalid_pairs': malformed, 'shape_mismatches': mismatch, 'other_tensors': unexpected})
    rows.sort(key=lambda row: row['adapter_sha256'])
    return {'base_shards': len(shards), 'base_header_sha256': sorted(shard_hashes),
            'base_tensor_count': len(base_shapes), 'adapters': rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-root', required=True, type=Path)
    parser.add_argument('--adapters-root', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = scan(args.base_root, args.adapters_root)
        result.update(state='MEASURED', date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
                      scope='header tensor shapes only; no weights loaded or inference performed')
    except (OSError, ValueError, TypeError, json.JSONDecodeError, struct.error):
        result = {'state': 'NO_DATA', 'cause': 'missing, unreadable or malformed local headers'}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
