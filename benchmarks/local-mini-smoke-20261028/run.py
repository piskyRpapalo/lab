"""Run a locally supplied synthetic input twice and retain only hashes and counters."""
import argparse
import datetime
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request

URL = 'http://127.0.0.1:11434'


def request(path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(URL + path, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--disable-thinking', action='store_true')
    args = parser.parse_args()
    prompt = sys.stdin.read()
    if not prompt or len(prompt.encode()) > 4096:
        raise SystemExit('input missing or exceeds 4096 bytes')
    try:
        entries = request('/api/tags')['models']
        candidates = [x for x in entries if x.get('name') == args.model]
        if len(candidates) != 1:
            raise ValueError('model_missing_or_ambiguous')
        manifest = candidates[0]['digest']
        if not isinstance(manifest, str) or len(manifest) != 64:
            raise ValueError('model_digest_invalid')
        receipt = {'date_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
                   'model_label': args.model, 'manifest_sha256': manifest,
                   'input_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                   'settings': {'temperature': 0, 'seed': 20261028, 'num_ctx': 2048, 'num_predict': 64, 'keep_alive': 0, 'think': not args.disable_thinking},
                   'samples': [], 'limits': ['manifest digest is service-reported, not rehashed weights',
                                             'no energy, quality, or physical device ranking measured']}
        for _ in range(2):
            started = time.monotonic_ns()
            result = request('/api/generate', {'model': args.model, 'prompt': prompt, 'stream': False,
                'options': {k: v for k, v in receipt['settings'].items() if k not in ('keep_alive', 'think')}, 'keep_alive': 0, 'think': receipt['settings']['think']})
            elapsed = time.monotonic_ns() - started
            if not result.get('done') or not isinstance(result.get('response'), str):
                raise ValueError('generation_incomplete')
            receipt['samples'].append({'wall_ns': elapsed, 'response_bytes': len(result['response'].encode()), 'response_sha256': hashlib.sha256(result['response'].encode()).hexdigest(),
                'load_ns': result.get('load_duration'), 'prompt_eval_count': result.get('prompt_eval_count'),
                'prompt_eval_ns': result.get('prompt_eval_duration'), 'eval_count': result.get('eval_count'),
                'eval_ns': result.get('eval_duration'), 'done_reason': result.get('done_reason')})
        after = [x.get('digest') for x in request('/api/tags')['models'] if x.get('name') == args.model]
        if after != [manifest]:
            raise ValueError('model_manifest_changed')
        print(json.dumps(receipt, indent=2, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        print(json.dumps({'state': 'NO_DATA', 'cause': 'local service or generation unavailable; no result asserted'}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
