"""Run a locally supplied synthetic input twice and retain only hashes and counters."""
import argparse
import datetime
import hashlib
import http.client
import json
import ipaddress
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import urllib.parse

URL = 'http://127.0.0.1:11434'
ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'benchmarks/fixtures/throughput-public-v1.json'
SETTINGS = {'stream': False, 'think': False, 'temperature': 0, 'seed': 42,
            'num_predict': 64, 'num_ctx': 2048, 'keep_alive': 0}


def no_data(cause):
    return {'state': 'NO_DATA', 'cause': cause}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('redirect_refused')


def local_url(base):
    try:
        parsed = urllib.parse.urlsplit(base)
        if (parsed.scheme != 'http' or parsed.username is not None or parsed.password is not None
                or parsed.path not in ('', '/') or parsed.query or parsed.fragment
                or not ipaddress.ip_address(parsed.hostname).is_loopback
                or parsed.port is None or not 1 <= parsed.port <= 65535):
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('nonlocal_endpoint') from None
    return base.rstrip('/')


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate_key')
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError('invalid_json_number')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_constant)


def request(path, body=None, base=URL):
    base = local_url(base)
    if path not in ('/api/tags', '/api/version', '/api/generate'):
        raise ValueError('endpoint_not_allowed')
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, headers={'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(req, timeout=180) as response:
        raw = response.read(1048577)
        if len(raw) > 1048576:
            raise ValueError('response_too_large')
        return strict_json(raw)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def model_digest(payload, model):
    entries = payload['models']
    candidates = [entry for entry in entries if entry.get('name') == model]
    if len(candidates) != 1:
        raise ValueError('model_not_installed_or_ambiguous')
    reject_remote(candidates[0])
    value = candidates[0]['digest']
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('invalid_model_digest')
    return value


def reject_remote(payload):
    if any(payload.get(key) not in (None, '') for key in ('remote_host', 'remote_model')):
        raise ValueError('remote_model_refused')


def public_input(raw):
    if len(raw) > 4096:
        raise ValueError('invalid_public_fixture')
    fixture = strict_json(raw)
    # A data-only public fixture: no arbitrary prompt, path or operator metadata.
    if (not isinstance(fixture, dict) or set(fixture) != {'schema', 'values'}
            or fixture['schema'] != 'throughput-public-v1'
            or not isinstance(fixture['values'], list) or len(fixture['values']) != 16
            or any(type(v) is not int or not 0 <= v <= 99 for v in fixture['values'])):
        raise ValueError('invalid_public_fixture')
    return 'Return these integers in ascending order, separated by commas: ' + ','.join(
        str(v) for v in fixture['values'])


def positive_int(value):
    return type(value) is int and 0 < value <= 10**18


def sample(result, model, elapsed):
    if isinstance(result, dict):
        reject_remote(result)
    if (not isinstance(result, dict) or result.get('done') is not True
            or result.get('model') != model or not isinstance(result.get('response'), str)
            or not result['response']):
        raise ValueError('invalid_generation')
    count, duration = result.get('eval_count'), result.get('eval_duration')
    if not positive_int(count) or not positive_int(duration) or not positive_int(elapsed):
        raise ValueError('invalid_timing')
    answer = result['response'].encode()
    load = result.get('load_duration')
    return {'state': 'MEASURED', 'eval_count': count, 'eval_duration_ns': duration,
            'generation_tokens_per_s': round(count * 1_000_000_000 / duration, 6),
            'wall_ns': elapsed, 'load_ns': load if type(load) is int and 0 <= load <= 10**18
            else no_data('load_duration_unavailable'),
            'response_bytes': len(answer), 'response_sha256': digest(answer)}


def run_public(model, raw, call=request, clock=time.monotonic_ns, measured_at=None,
               hardware_class='unknown', source=None):
    """Two independent attempts; failed runs stay in the denominator. No answer text escapes."""
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}', model):
        raise ValueError('invalid_model_label')
    if model.endswith(':cloud'):
        raise ValueError('remote_model_refused')
    if hardware_class not in ('unknown', 'cpu', 'integrated-gpu', 'discrete-gpu', 'mixed'):
        raise ValueError('invalid_hardware_class')
    prompt = public_input(raw)
    receipt = {'schema': 'bench-repro-01-v1', 'experiment_id': 'public-throughput-v1',
        'date_utc': measured_at or datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        'model_name': model, 'fixture_sha256': digest(raw), 'input_sha256': digest(prompt.encode()),
        'settings': dict(SETTINGS), 'source': source or no_data('source_not_supplied'),
        'hardware_class': no_data('hardware_not_declared') if hardware_class == 'unknown'
            else {'state': 'DECLARED', 'value': hardware_class},
        'inference_backend': no_data('backend_not_measured'),
        'server_egress': no_data('server_network_isolation_not_attested'),
        'cpu_gpu_split': no_data('placement_not_measured'), 'power': no_data('power_not_measured'),
        'ram': no_data('memory_not_measured'),
        'samples': [], 'limitations': ['New public experiment; not a reconstruction of LAB #164.',
            'Model digest and timing counters are service-reported, not independently authenticated.',
            'Throughput does not measure semantic quality, fairness, energy or regulatory compliance.',
            'keep_alive=0 requests unloading; cold-cache equivalence is not established.']}
    try:
        version = call('/api/version').get('version')
        receipt['ollama_version'] = version if isinstance(version, str) and re.fullmatch(
            r'\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]{1,32})?', version) else no_data('version_unavailable')
    except (OSError, http.client.HTTPException, ValueError, KeyError, TypeError, AttributeError):
        receipt['ollama_version'] = no_data('version_unavailable')
    try:
        manifest = model_digest(call('/api/tags'), model)
    except (OSError, http.client.HTTPException, ValueError, KeyError, TypeError, AttributeError) as exc:
        receipt.update(no_data('local_endpoint_unavailable' if isinstance(exc, OSError)
                               else 'local_protocol_error' if isinstance(exc, http.client.HTTPException)
                               else 'remote_model_refused' if str(exc) == 'remote_model_refused'
                               else 'model_not_installed_or_invalid'))
        receipt.update({'model_digest': no_data('preflight_failed'), 'attempted': 0,
                        'succeeded': 0, 'failed': 0, 'model_stable': no_data('preflight_failed')})
        return receipt
    receipt['model_digest'] = manifest
    options = {k: SETTINGS[k] for k in ('temperature', 'seed', 'num_predict', 'num_ctx')}
    for attempt in (1, 2):
        started = clock()
        try:
            result = call('/api/generate', {'model': model, 'prompt': prompt,
                'stream': False, 'think': False, 'keep_alive': 0, 'options': dict(options)})
            row = sample(result, model, clock() - started)
        except (OSError, http.client.HTTPException, ValueError, KeyError, TypeError, AttributeError, UnicodeError) as exc:
            row = no_data('local_endpoint_unavailable' if isinstance(exc, OSError) else
                          'local_protocol_error' if isinstance(exc, http.client.HTTPException) else
                          str(exc) if str(exc) in ('invalid_timing', 'remote_model_refused') else 'invalid_generation')
        receipt['samples'].append(dict(row, attempt=attempt))
    try:
        stable = model_digest(call('/api/tags'), model) == manifest
        receipt['model_stable'] = stable
    except (OSError, http.client.HTTPException, ValueError, KeyError, TypeError, AttributeError):
        stable = False
        receipt['model_stable'] = no_data('postflight_unavailable')
    success = sum(row['state'] == 'MEASURED' for row in receipt['samples'])
    receipt.update({'attempted': 2, 'succeeded': success, 'failed': 2 - success,
                    'state': 'MEASURED' if stable and success == 2 else 'NO_DATA',
                    'cause': None if stable and success == 2 else
                             'model_not_stable' if not stable else 'incomplete_samples'})
    receipt['byte_identical'] = (receipt['samples'][0]['response_sha256'] ==
        receipt['samples'][1]['response_sha256']) if success == 2 else no_data('incomplete_samples')
    return receipt


def comparison_key(receipt):
    """Experimental controls only; this is not a certification of comparable hardware."""
    return digest(json.dumps({k: receipt[k] for k in ('schema', 'fixture_sha256', 'input_sha256',
        'settings', 'model_digest', 'ollama_version')}, sort_keys=True).encode())


def source_record():
    paths = [str(Path(__file__).relative_to(ROOT)), str(FIXTURE.relative_to(ROOT))]
    try:
        sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        clean = subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', *paths], cwd=ROOT).returncode == 0
        committed = all(subprocess.run(['git', 'ls-files', '--error-unmatch', '--', p],
            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0 for p in paths)
        commit = sha if clean and committed else no_data('uncommitted_runner_or_fixture')
    except (OSError, subprocess.CalledProcessError):
        commit = no_data('git_source_unavailable')
    return {'commit': commit, 'runner_sha256': digest(Path(__file__).read_bytes())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--disable-thinking', action='store_true')
    parser.add_argument('--public-fixture', action='store_true')
    parser.add_argument('--base-url', default=URL)
    parser.add_argument('--hardware-class', default='unknown')
    args = parser.parse_args()
    try:
        base = local_url(args.base_url)
        if args.public_fixture:
            if args.disable_thinking:
                raise ValueError('public_profile_is_fixed')
            receipt = run_public(args.model, FIXTURE.read_bytes(),
                call=lambda path, body=None: request(path, body, base),
                hardware_class=args.hardware_class, source=source_record())
            receipt['comparison_key'] = comparison_key(receipt)
            print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))
            return 0 if receipt['state'] == 'MEASURED' else 1
        if base != URL or args.hardware_class != 'unknown':
            raise ValueError('options_require_public_profile')
    except (OSError, http.client.HTTPException, ValueError, KeyError, TypeError):
        print(json.dumps(no_data('invalid_public_configuration')))
        return 1
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
        outputs = []
        for _ in range(2):
            started = time.monotonic_ns()
            result = request('/api/generate', {'model': args.model, 'prompt': prompt, 'stream': False,
                'options': {k: v for k, v in receipt['settings'].items() if k not in ('keep_alive', 'think')}, 'keep_alive': 0, 'think': receipt['settings']['think']})
            elapsed = time.monotonic_ns() - started
            if not result.get('done') or not isinstance(result.get('response'), str):
                raise ValueError('generation_incomplete')
            outputs.append(result['response'].encode())
            receipt['samples'].append({'wall_ns': elapsed, 'response_bytes': len(result['response'].encode()), 'response_sha256': hashlib.sha256(result['response'].encode()).hexdigest(),
                'load_ns': result.get('load_duration'), 'prompt_eval_count': result.get('prompt_eval_count'),
                'prompt_eval_ns': result.get('prompt_eval_duration'), 'eval_count': result.get('eval_count'),
                'eval_ns': result.get('eval_duration'), 'done_reason': result.get('done_reason')})
        receipt['byte_identical'] = outputs[0] == outputs[1]
        after = [x.get('digest') for x in request('/api/tags')['models'] if x.get('name') == args.model]
        if after != [manifest]:
            raise ValueError('model_manifest_changed')
        print(json.dumps(receipt, indent=2, sort_keys=True))
    except (OSError, http.client.HTTPException, ValueError, KeyError, TypeError, json.JSONDecodeError):
        print(json.dumps({'state': 'NO_DATA', 'cause': 'local service or generation unavailable; no result asserted'}))
        raise SystemExit(1)


if __name__ == '__main__':
    sys.exit(main())
