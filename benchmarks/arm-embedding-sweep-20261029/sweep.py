"""Measure local embedding calls without retaining input or vectors."""
import datetime
import hashlib
import json
import math
import struct
import sys
import time
import urllib.error
import urllib.request

URL = 'http://127.0.0.1:11434'
LIMIT = 2_200_000_000


def request(route, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(URL + route, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as result:
        return json.load(result)


def vector_receipt(vector):
    if not isinstance(vector, list) or not vector:
        raise ValueError('empty_vector')
    packed = bytearray()
    for value in vector:
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError('invalid_vector')
        packed.extend(struct.pack('<f', value))
    return {'dimensions': len(vector), 'float32_le_sha256': hashlib.sha256(packed).hexdigest()}


def sweep(text):
    if not isinstance(text, str) or not text or len(text.encode()) > 4096:
        raise ValueError('input_unavailable_or_too_large')
    entries = request('/api/tags')['models']
    rows, skipped = [], {'over_size_limit': 0, 'not_embedding': 0, 'unavailable': 0}
    for item in sorted(entries, key=lambda x: (str(x.get('digest')), str(x.get('name')))):
        size, sha, name = item.get('size'), item.get('digest'), item.get('name')
        if type(size) is not int or size <= 0 or not isinstance(name, str) or not isinstance(sha, str) or len(sha) != 64:
            skipped['unavailable'] += 1
            continue
        if size > LIMIT:
            skipped['over_size_limit'] += 1
            continue
        try:
            if 'embedding' not in request('/api/show', {'model': name}).get('capabilities', []):
                skipped['not_embedding'] += 1
                continue
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            skipped['unavailable'] += 1
            continue
        row = {'manifest_sha256': sha, 'declared_bytes': size, 'samples': []}
        for _ in range(2):
            try:
                start = time.monotonic_ns()
                result = request('/api/embed', {'model': name, 'input': text, 'keep_alive': 0})
                elapsed = time.monotonic_ns() - start
                vectors = result.get('embeddings')
                if not isinstance(vectors, list) or len(vectors) != 1:
                    raise ValueError('invalid_result')
                row['samples'].append({'state': 'MEASURED', 'wall_ns': elapsed,
                    'load_ns': result.get('load_duration'), 'prompt_eval_count': result.get('prompt_eval_count'),
                    **vector_receipt(vectors[0])})
            except (OSError, ValueError, TypeError, OverflowError, struct.error, json.JSONDecodeError):
                row['samples'].append({'state': 'NO_DATA', 'cause': 'embedding_unavailable_or_invalid'})
        rows.append(row)
    return {'date_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
            'input_sha256': hashlib.sha256(text.encode()).hexdigest(), 'size_limit_bytes': LIMIT,
            'listed_entries': len(entries), 'skipped': skipped, 'models': rows,
            'limits': 'service manifest digests; vectors hashed as IEEE-754 float32 little-endian; no quality or blob verification'}


def main():
    try:
        print(json.dumps(sweep(sys.stdin.read()), sort_keys=True, indent=2))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        print(json.dumps({'state': 'NO_DATA', 'cause': 'local_inventory_unavailable_or_invalid'}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
