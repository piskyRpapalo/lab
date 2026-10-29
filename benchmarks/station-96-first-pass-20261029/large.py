"""Measure one local 70B call; retain counters and digests, never text."""
import datetime
import hashlib
import json
import sys
import time
import urllib.request

BASE = 'http://127.0.0.1:11434'
MODEL = 'llama3.3:70b'


def request(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=1800) as response:
        return json.load(response)


def main():
    prompt = sys.stdin.read()
    if not prompt or len(prompt.encode()) > 4096:
        raise SystemExit('input absent or exceeds 4096 bytes')
    models = [m for m in request('/api/tags')['models'] if m.get('name') == MODEL]
    if len(models) != 1:
        raise SystemExit('NO_DATA: model missing or ambiguous')
    options = {'temperature': 0, 'seed': 20261028, 'num_ctx': 2048, 'num_predict': 64}
    begin = time.monotonic_ns()
    result = request('/api/generate', {'model': MODEL, 'prompt': prompt, 'stream': False,
                                      'options': options, 'keep_alive': '5m'})
    wall = time.monotonic_ns() - begin
    if not result.get('done') or not isinstance(result.get('response'), str):
        raise SystemExit('NO_DATA: generation incomplete')
    active = [m for m in request('/api/ps').get('models', []) if m.get('name') == MODEL]
    output = result['response'].encode()
    receipt = {'date_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
               'model': MODEL, 'manifest_sha256': models[0].get('digest'),
               'model_bytes': models[0].get('size'), 'model_details': models[0].get('details'),
               'input_sha256': hashlib.sha256(prompt.encode()).hexdigest(), 'settings': options,
               'response_sha256': hashlib.sha256(output).hexdigest(), 'response_bytes': len(output),
               'wall_ns': wall, 'load_ns': result.get('load_duration'),
               'prompt_eval_count': result.get('prompt_eval_count'),
               'prompt_eval_ns': result.get('prompt_eval_duration'),
               'eval_count': result.get('eval_count'), 'eval_ns': result.get('eval_duration'),
               'done_reason': result.get('done_reason'),
               'loaded': [{k: m.get(k) for k in ('size', 'size_vram', 'context_length')} for m in active],
               'limits': ['service-reported digest and placement; weights not independently rehashed',
                          'quality, energy and other devices capacity not measured']}
    print(json.dumps(receipt, indent=2, sort_keys=True))
    request('/api/generate', {'model': MODEL, 'keep_alive': 0})


if __name__ == '__main__':
    main()
