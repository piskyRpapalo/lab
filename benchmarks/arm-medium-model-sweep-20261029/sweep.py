"""Sequential local-only smoke: report hashes and counts, never input or output text."""
import datetime
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request

MINIMUM = 2_200_000_000
LIMIT = 4_800_000_000
URL = 'http://127.0.0.1:11434'
OPTIONS = {'temperature': 0, 'seed': 20261028, 'num_ctx': 2048, 'num_predict': 64}


def request(route, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(URL + route, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as result:
        return json.load(result)


def sweep(prompt):
    if not isinstance(prompt, str) or not prompt or len(prompt.encode()) > 4096:
        raise ValueError('input_unavailable_or_too_large')
    entries = request('/api/tags')['models']
    rows, skipped = [], {'over_size_limit': 0, 'below_size_limit': 0, 'not_completion': 0, 'capabilities_unavailable': 0}
    entries = sorted(entries, key=lambda item: (str(item.get('digest')), str(item.get('name'))))
    for item in entries:
        size = item.get('size')
        if type(size) is not int or size <= 0:
            skipped['capabilities_unavailable'] += 1
            continue
        if size <= MINIMUM:
            skipped['below_size_limit'] += 1
            continue
        if size > LIMIT:
            skipped['over_size_limit'] += 1
            continue
        sha, name = item.get('digest'), item.get('name')
        if not isinstance(sha, str) or len(sha) != 64 or not isinstance(name, str):
            skipped['capabilities_unavailable'] += 1
            continue
        try:
            info = request('/api/show', {'model': name})
            if 'completion' not in info.get('capabilities', []):
                skipped['not_completion'] += 1
                continue
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            skipped['capabilities_unavailable'] += 1
            continue
        row = {'manifest_sha256': sha, 'declared_bytes': size, 'samples': []}
        for _ in range(2):
            try:
                start = time.monotonic_ns()
                answer = request('/api/generate', {'model': name, 'prompt': prompt, 'stream': False,
                    'options': OPTIONS, 'keep_alive': 0, 'think': False})
                elapsed = time.monotonic_ns() - start
                text = answer.get('response')
                if not answer.get('done') or not isinstance(text, str):
                    raise ValueError('incomplete')
                row['samples'].append({'state': 'MEASURED' if text else 'NO_DATA',
                    'cause': None if text else 'empty_visible_response',
                    'response_bytes': len(text.encode()), 'response_sha256': hashlib.sha256(text.encode()).hexdigest(),
                    'wall_ns': elapsed, 'eval_count': answer.get('eval_count'),
                    'eval_ns': answer.get('eval_duration'), 'load_ns': answer.get('load_duration'),
                    'done_reason': answer.get('done_reason')})
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                row['samples'].append({'state': 'NO_DATA', 'cause': 'local_generation_failed'})
        rows.append(row)
    return {'date_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
            'input_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
            'settings': {**OPTIONS, 'think': False, 'keep_alive': 0}, 'minimum_exclusive_bytes': MINIMUM, 'size_limit_bytes': LIMIT,
            'listed_entries': len(entries), 'skipped': skipped, 'models': rows,
            'limits': 'service-reported manifest digests; no quality, blob verification, or fleet ranking'}


def main():
    try:
        print(json.dumps(sweep(sys.stdin.read()), indent=2, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        print(json.dumps({'state': 'NO_DATA', 'cause': 'local_inventory_unavailable_or_invalid'}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
