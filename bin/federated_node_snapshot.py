#!/usr/bin/env python3
"""Read-only local metadata snapshot. No inference or model installation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import time
from datetime import datetime, timezone
import urllib.error
import urllib.request

MAX_BYTES = 4 * 1024 * 1024
MAX_AGE_SECONDS = 120


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True).encode()).hexdigest()


def no_data(cause):
    return {'state': 'NO_DATA', 'cause': cause}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('redirect_refused')


class Metadata:
    def __init__(self, port):
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError('invalid_port')
        self.base = 'http://127.0.0.1:' + str(port)
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def read(self, route, model=None):
        if route not in ('version', 'tags', 'ps', 'show') or (route == 'show') != (model is not None):
            raise ValueError('metadata_route_only')
        payload = None if model is None else json.dumps({'model': model, 'verbose': False}).encode()
        req = urllib.request.Request(self.base + '/api/' + route, data=payload,
                                     headers={'Content-Type': 'application/json'})
        started = time.monotonic()
        try:
            with self.opener.open(req, timeout=4) as response:
                raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                return no_data('metadata_byte_limit')
            data = json.loads(raw)
            if not isinstance(data, dict):
                return no_data('metadata_schema')
            return {'state': 'VERIFIED', 'rtt_ms': round((time.monotonic()-started)*1000, 3), 'data': data}
        except (OSError, ValueError, urllib.error.URLError):
            return no_data('metadata_unavailable_or_invalid')


def declared(value, cause='not_reported'):
    return {'state': 'DECLARED', 'value': value} if value is not None else no_data(cause)


def model_record(model, show):
    """Keep no arbitrary server text, template, system prompt or license body."""
    details = model.get('details', {})
    if not isinstance(details, dict):
        details = {}
    info = show.get('data', {}) if show.get('state') == 'VERIFIED' else {}
    params = info.get('parameters', '')
    context = re.search(r'^num_ctx\s+([0-9]{1,10})\s*$', params, re.M) if isinstance(params, str) else None
    license_text = info.get('license')
    caps = info.get('capabilities', [])
    if not isinstance(caps, list):
        caps = []
    caps = [c for c in caps if c in ('completion', 'embedding', 'vision', 'tools', 'thinking')]
    return {
        'model_ref': digest(model.get('name')), 'model_version': model.get('digest'),
        'catalog_bytes': model.get('size') if type(model.get('size')) is int and model['size'] >= 0 else no_data('invalid_size'),
        'state': 'VERIFIED',
        'format': declared(details.get('format') if details.get('format') in ('gguf', 'safetensors') else None),
        'quantization': declared(details.get('quantization_level') if re.fullmatch(r'(?:[A-Z0-9_]{1,24}|unknown)', str(details.get('quantization_level'))) else None),
        'architecture_context': declared(details.get('context_length') if type(details.get('context_length')) is int and details['context_length'] > 0 else None),
        'configured_context': declared(int(context.group(1)) if context else None),
        'capabilities': declared(caps if info else None),
        'license': declared({'sha256': hashlib.sha256(license_text.encode()).hexdigest(),
                             'review': 'NOT_REVIEWED'} if isinstance(license_text, str) and license_text.strip() else None),
        'task_quality': no_data('no_task_evaluation'),
        'inference_latency_peak_memory_energy': no_data('metadata_only_no_inference'),
    }


def host_snapshot():
    result = {}
    try:
        mem = dict(re.findall(r'^(MemTotal|MemAvailable):\s+(\d+) kB$', Path('/proc/meminfo').read_text(), re.M))
        result['memory_bytes'] = {k: int(v)*1024 for k, v in mem.items()}
        result['cpu_count'] = os.cpu_count()
        result['load_1_5_15'] = list(os.getloadavg())
        result['architecture'] = os.uname().machine
        cpu = Path('/proc/cpuinfo').read_text()
        match = re.search(r'^(?:model name|Model)\s*:\s*(.*)$', cpu, re.M)
        # Store only a digest of free-form hardware strings.
        result['cpu_model_ref'] = digest(match.group(1)) if match else None
        disk = os.statvfs('/')
        result['root_storage_bytes'] = {'total': disk.f_blocks*disk.f_frsize,
                                        'available': disk.f_bavail*disk.f_frsize}
    except OSError:
        result['host'] = no_data('host_telemetry_unavailable')
    result['pressure_avg10'] = {}
    for kind in ('cpu', 'memory', 'io'):
        try:
            raw = Path('/proc/pressure', kind).read_text()
            match = re.search(r'^some avg10=(\d+(?:\.\d+)?) ', raw, re.M)
            result['pressure_avg10'][kind] = float(match.group(1)) if match else no_data('pressure_schema')
        except OSError:
            result['pressure_avg10'][kind] = no_data('pressure_unavailable')
    return result


def collect(node, backend, backend_only=False):
    if not re.fullmatch(r'node-[abcde]', node):
        raise ValueError('anonymous_node_required')
    # Earliest observation bounds age; collection duration never refreshes it.
    observed_at = datetime.now(timezone.utc).isoformat()
    version, resident, catalog = (backend.read(route) for route in ('version', 'ps', 'tags'))
    records = []
    entries = catalog.get('data', {}).get('models')
    if catalog['state'] == 'VERIFIED' and isinstance(entries, list) and len(entries) <= 256:
        for item in entries:
            if not isinstance(item, dict) or not isinstance(item.get('name'), str) or not re.fullmatch(r'[0-9a-f]{64}', str(item.get('digest', ''))):
                catalog = no_data('catalog_schema'); records = []; break
            records.append(model_record(item, backend.read('show', item['name'])))
    else:
        catalog = no_data('catalog_missing_invalid_or_over_limit')
    loaded = resident.get('data', {}).get('models')
    snapshot = {
        'schema': 'preceptoros.lab.node-metadata/1', 'node': node,
        'observed_at': observed_at, 'completed_at': datetime.now(timezone.utc).isoformat(),
        'max_age_seconds': MAX_AGE_SECONDS,
        'scope': 'single_loopback_backend_metadata_not_complete_weight_inventory',
        'collector_sha256': hashlib.sha256(globals().get('_SOURCE_BYTES') or Path(__file__).read_bytes()).hexdigest(),
        'host': no_data('backend_transport_only') if backend_only else host_snapshot(),
        'backend_version': declared(version.get('data', {}).get('version') if re.fullmatch(r'\d+\.\d+\.\d+(?:[a-z0-9.-]{0,32})', str(version.get('data', {}).get('version'))) else None),
        'catalog_state': catalog['state'], 'catalog_cause': catalog.get('cause'),
        'metadata_rtt_ms': {k: r.get('rtt_ms', no_data('request_failed')) for k, r in
                            [('version', version), ('tags', catalog), ('ps', resident)]},
        'resident_count': len(loaded) if isinstance(loaded, list) else no_data('resident_catalog_unavailable'),
        'models': records,
        'other_backends_and_weight_stores': no_data('not_scanned_reuse_prior_receipts'),
        'admission': no_data('task_resource_envelope_not_calibrated'),
        'training': 'NOT_AUTHORIZED',
    }
    snapshot['snapshot_ref'] = digest(snapshot)
    return snapshot


def freshness(snapshot, now):
    """Integrity/age only, never authenticity, capacity or dispatch authority.

    Uses this consumer's ceiling, not an untrusted snapshot-provided lifetime.
    """
    try:
        payload = dict(snapshot)
        ref = payload.pop('snapshot_ref')
        if ref != digest(payload) or payload['schema'] != 'preceptoros.lab.node-metadata/1':
            return no_data('snapshot_integrity')
        captured = datetime.fromisoformat(payload['observed_at'])
        if captured.utcoffset() is None or now.utcoffset() is None:
            return no_data('timezone_required')
        age = (now - captured).total_seconds()
        if age < 0:
            return no_data('future_observation')
        return {'state': 'VERIFIED' if age <= MAX_AGE_SECONDS else 'STALE',
                'cause': 'age_within_ceiling' if age <= MAX_AGE_SECONDS else 'observation_expired'}
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
        return no_data('snapshot_schema')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', required=True, choices=['node-a', 'node-b', 'node-c', 'node-d', 'node-e'])
    parser.add_argument('--port', type=int, default=11434)
    parser.add_argument('--backend-only', action='store_true', help='Tunnel observation: do not attribute collector host telemetry to target')
    args = parser.parse_args()
    print(json.dumps(collect(args.node, Metadata(args.port), args.backend_only), sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
