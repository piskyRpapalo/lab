#!/usr/bin/env python3
"""Offline, pinned receipt projections. Never probes, dispatches or grants."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import sys

SPEC = importlib.util.spec_from_file_location('_node_snapshot', Path(__file__).with_name('federated_node_snapshot.py'))
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)
SCHEMA = 'preceptoros.lab.node-metadata/1'
NODES = tuple('node-' + c for c in 'abcde')
HEX = re.compile(r'[a-f0-9]{64}\Z')
NAME = re.compile(r'[0-9]{8}-federated-(node-[abcde])(?:-(primary|secondary))?(?:-r[1-9][0-9]{0,3})?\.json\Z')
MAX_PIECE = 16384
CAPABILITIES = ('completion', 'embedding', 'vision', 'tools', 'thinking')


class EvidenceError(ValueError):
    pass


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()


def nd(cause):
    return {'state': 'NO_DATA', 'cause': cause}


def instant(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.utcoffset() is None:
        raise EvidenceError('timezone_required')
    return result.astimezone(timezone.utc)


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError('duplicate_json_key')
        result[key] = value
    return result


def read_json(root, name):
    # Names are validated by the caller. No symlink/FIFO reads or unbounded data.
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd = os.open(Path(root) / name, flags)
        with os.fdopen(fd, 'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise EvidenceError('source_not_regular_file')
            raw = stream.read(MAX_PIECE)
        if len(raw) >= MAX_PIECE:
            raise EvidenceError('source_byte_limit')
        def reject(_):
            raise EvidenceError('nonfinite_json')
        def finite(value):
            parsed = float(value)
            return parsed if math.isfinite(parsed) else reject(value)
        return raw, json.loads(raw, object_pairs_hook=unique, parse_constant=reject, parse_float=finite)
    except EvidenceError:
        raise
    except (OSError, ValueError, RecursionError):
        raise EvidenceError('source_unavailable_or_invalid') from None


def load_receipt(root, name, expected_ref):
    """The host supplies its trusted source seal. A self-sealed file is not authority."""
    match = NAME.fullmatch(name)
    if not match or not isinstance(expected_ref, str) or not HEX.fullmatch(expected_ref):
        raise EvidenceError('source_name_or_pin_invalid')
    _, doc = read_json(root, name)
    if (type(doc) is not dict or doc.get('schema') != 'preceptoros.lab.node-metadata-parts/1'
            or doc.get('snapshot_ref') != expected_ref or type(doc.get('header')) is not dict
            or type(doc.get('model_count')) is not int or not 0 <= doc['model_count'] <= 256
            or type(doc.get('parts')) is not list or len(doc['parts']) > 26):
        raise EvidenceError('manifest_or_pin_invalid')
    models, seen = [], set()
    part_name = re.compile(re.escape(name[:-5]) + r'-models-[1-9][0-9]*\.json\Z')
    for part in doc['parts']:
        if (type(part) is not dict or set(part) != {'file', 'sha256', 'count'}
                or type(part['file']) is not str or not part_name.fullmatch(part['file'])
                or part['file'] in seen or type(part['sha256']) is not str
                or not HEX.fullmatch(part['sha256'])):
            raise EvidenceError('part_manifest_invalid')
        seen.add(part['file'])
        raw, entries = read_json(root, part['file'])
        if hashlib.sha256(raw).hexdigest() != part['sha256']:
            raise EvidenceError('part_hash_mismatch')
        if (type(entries) is not list or type(part['count']) is not int
                or not 0 <= part['count'] <= 10 or len(entries) != part['count']):
            raise EvidenceError('part_count_invalid')
        models.extend(entries)
    source = dict(doc['header'], models=models)
    if (len(models) != doc['model_count'] or source.get('schema') != SCHEMA
            or source.get('node') != match[1] or snapshot.digest(source) != expected_ref):
        raise EvidenceError('snapshot_integrity_or_node_binding')
    source['snapshot_ref'] = expected_ref
    return source, match[2] or 'default'


def number(value):
    return value if type(value) is int and 0 <= value < 2**63 else None


def seal(record):
    record['projection_ref'] = snapshot.digest(record)
    return record


def missing(node, now, cause='no_observation_in_supplied_bundle', last_failure=None, backend='unknown'):
    if (node not in NODES or now.utcoffset() is None or backend not in ('unknown', 'default', 'primary', 'secondary')
            or cause not in ('no_observation_in_supplied_bundle', 'evidence_invalid_or_unavailable')):
        raise EvidenceError('node_invalid')
    now = now.astimezone(timezone.utc)
    record = {'schema': SCHEMA, 'kind': 'projection', 'node': node, 'backend': backend,
        'state': 'NO_DATA', 'cause': cause, 'observed_at': None,
        'checked_at': now.isoformat(), 'source_ref': None, 'topology_state': 'DECLARED',
        'verification': nd('source_missing'), 'models': None, 'memory': nd('source_missing'),
        'resources': nd('source_missing'),
        'missing_measurements': ['fresh_node_telemetry', 'independent_task_quality', 'task_peak_memory',
                                 'inference_latency', 'scoped_permission', 'concurrency_calibration'],
        'responds_now': nd('no_fresh_transport_observation'),
        'inference': nd('no_independent_task_witness'),
        'admission': dict(nd('evidence_insufficient'), allowed=False),
        'summary': node + ': No usable observation. Current models and resources are unknown.'}
    if last_failure is not None:
        if (type(last_failure) is not dict or set(last_failure) != {'cause', 'source_ref'}
                or last_failure['cause'] not in ('access_timeout', 'transport_unavailable', 'authorization_refused')
                or type(last_failure['source_ref']) is not str or not HEX.fullmatch(last_failure['source_ref'])):
            raise EvidenceError('failure_claim_invalid')
        record['last_failure'] = dict(last_failure, state='DECLARED', scope='host_cited_prior_failure')
        record['summary'] = node + ': Prior access failure reported; current models and resources are unknown.'
    return seal(record)


def project(source, now, expected_ref, backend='default'):
    """Additive projection of node-metadata/1, with an independent projection seal."""
    if now.utcoffset() is None:
        raise EvidenceError('timezone_required')
    now = now.astimezone(timezone.utc)
    if (type(source) is not dict or source.get('node') not in NODES
            or backend not in ('default', 'primary', 'secondary')
            or source.get('snapshot_ref') != expected_ref or not isinstance(expected_ref, str)
            or not HEX.fullmatch(expected_ref)):
        raise EvidenceError('source_identity_invalid')
    age = snapshot.freshness(source, now)
    if age['state'] == 'NO_DATA':
        raise EvidenceError(age['cause'])
    if type(source.get('models')) is not list or len(source['models']) > 256:
        raise EvidenceError('model_list_invalid')
    observation_state = 'STALE' if age['state'] == 'STALE' else 'OBSERVED'
    state = observation_state
    cause = 'observation_expired' if state == 'STALE' else 'metadata_query_only'
    if source.get('catalog_state') not in ('VERIFIED', 'OBSERVED'):
        state, cause = 'NO_DATA', 'metadata_unavailable'
    items = []
    for model in source['models']:
        if (type(model) is not dict or any(type(model.get(k)) is not str or not HEX.fullmatch(model[k])
                                          for k in ('model_ref', 'model_version'))):
            raise EvidenceError('model_identity_invalid')
        caps = model.get('capabilities', {})
        caps = caps.get('value') if type(caps) is dict and caps.get('state') == 'DECLARED' else None
        capabilities = (sorted({c for c in caps if type(c) is str and c in CAPABILITIES})
                        if type(caps) is list else None)
        items.append({'model_ref': model['model_ref'], 'model_version': model['model_version'],
                      'capabilities': capabilities})
    host = source.get('host', {})
    mem = host.get('memory_bytes', {}) if type(host) is dict else {}
    mem = mem if type(mem) is dict else {}
    total, available = number(mem.get('MemTotal')), number(mem.get('MemAvailable'))
    memory = {'state': observation_state, 'total_bytes': total, 'available_bytes': available}
    if total is None or available is None or available > total:
        memory = nd('host_memory_not_observed')
    host = host if type(host) is dict else {}
    disk = host.get('root_storage_bytes', {})
    disk = disk if type(disk) is dict else {}
    pressure = host.get('pressure_avg10', {})
    pressure = pressure if type(pressure) is dict else {}
    axes = {k: pressure.get(k) for k in ('cpu', 'memory', 'io')}
    pressure_ok = all(type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 100 for v in axes.values())
    resources = {'state': observation_state, 'cpu_count': number(host.get('cpu_count')),
                 'root_available_bytes': number(disk.get('available')),
                 'pressure': {'state': observation_state, 'avg10': axes} if pressure_ok else nd('pressure_not_observed')}
    missing_measurements = ['independent_task_quality', 'task_peak_memory', 'inference_latency',
                            'scoped_permission', 'concurrency_calibration']
    if not pressure_ok:
        missing_measurements.append('node_pressure')
    if state != 'OBSERVED':
        missing_measurements.append('fresh_node_telemetry')
    version = source.get('backend_version', {})
    version = version.get('value') if type(version) is dict and version.get('state') == 'DECLARED' else None
    if type(version) is not str or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+[a-z0-9.-]{0,32}', version):
        version = None
    if state == 'STALE':
        message = 'Observation expired; %d historical model tags. Refresh before deciding.' % len(items)
    elif state == 'OBSERVED':
        message = 'Metadata observed; %d model tag%s announced. No task evaluation supplied.' % (len(items), '' if len(items) == 1 else 's')
    else:
        message = 'Metadata request failed. Model availability is unknown.'
    record = {'schema': SCHEMA, 'kind': 'projection', 'node': source['node'], 'backend': backend,
        'state': state, 'cause': cause, 'observed_at': instant(source['observed_at']).isoformat(),
        'checked_at': now.isoformat(), 'source_ref': expected_ref, 'topology_state': 'DECLARED',
        'collector_sha256': source.get('collector_sha256') if type(source.get('collector_sha256')) is str
                            and HEX.fullmatch(source['collector_sha256']) else None,
        'verification': {'state': 'VERIFIED', 'scope': 'receipt_integrity'},
        'backend_version': {'state': 'DECLARED', 'value': version} if version else nd('version_not_declared'),
        'models': {'state': state, 'count': len(items), 'capability_basis': 'DECLARED', 'items': items}
                  if state != 'NO_DATA' else None,
        'freshness': {'state': observation_state, 'max_age_seconds': snapshot.MAX_AGE_SECONDS},
        'memory': memory, 'resources': resources, 'missing_measurements': missing_measurements,
        'responds_now': {'state': 'OBSERVED', 'scope': 'metadata_snapshot_only'} if state == 'OBSERVED'
                        else nd('no_fresh_transport_observation'),
        'inference': nd('no_independent_task_witness'),
        'admission': dict(nd('task_resource_envelope_not_calibrated'), allowed=False),
        'summary': source['node'] + ': ' + message}
    return seal(record)


def views(record):
    """Same record/ref/summary for visual text, screen reader, audio and machine."""
    if (type(record) is not dict or record.get('schema') != SCHEMA or record.get('kind') != 'projection'
            or record.get('node') not in NODES or record.get('state') not in ('OBSERVED', 'STALE', 'NO_DATA')
            or record.get('admission', {}).get('allowed') is not False
            or record.get('inference') != nd('no_independent_task_witness')
            or record.get('projection_ref') != snapshot.digest({k: v for k, v in record.items() if k != 'projection_ref'})):
        raise EvidenceError('projection_integrity')
    ref = record['projection_ref']
    packet = {'record': record,
              'views': {'text': {'state_ref': ref, 'summary': record['summary']},
                        'speech': {'state_ref': ref, 'summary': record['summary']},
                        'machine': {'state_ref': ref, 'record': record}}}
    if len(encode(packet)) >= MAX_PIECE:
        raise EvidenceError('projection_byte_limit')
    return packet


def verify_packet(packet, source, now, expected_ref, backend='default'):
    """Recompute from pinned source and HOST time; a resealed packet is not enough."""
    try:
        return packet == views(project(source, now, expected_ref, backend))
    except (EvidenceError, TypeError, ValueError, KeyError, AttributeError):
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipts-root', type=Path, required=True)
    parser.add_argument('--source', action='append', required=True, metavar='MANIFEST=SNAPSHOT_SHA256')
    parser.add_argument('--at', help='Explicit UTC/offset time for deterministic replay; default: current UTC')
    args = parser.parse_args()
    try:
        now = instant(args.at) if args.at else datetime.now(timezone.utc)
        if len(args.source) > 8:
            raise EvidenceError('source_count_limit')
        records, seen, failed = [], set(), False
        for value in args.source:
            name, _, ref = value.partition('=')
            match = NAME.fullmatch(name)
            if not match:
                raise EvidenceError('source_name_or_pin_invalid')
            identity = (match[1], match[2] or 'default')
            if identity in seen:
                raise EvidenceError('duplicate_backend_identity')
            seen.add(identity)
            try:
                source, backend = load_receipt(args.receipts_root, name, ref)
                record = project(source, now, ref, backend)
                views(record)  # Refuse oversized complete packets before writing any output.
            except EvidenceError:
                record, failed = missing(match[1], now, 'evidence_invalid_or_unavailable', backend=identity[1]), True
            records.append(record)
        for node in NODES:
            if node not in {r['node'] for r in records}:
                records.append(missing(node, now))
        for record in sorted(records, key=lambda r: (r['node'], r['source_ref'] or '')):
            print(encode(views(record)).decode())
        return 2 if failed else 0
    except (EvidenceError, ValueError, TypeError):
        print('NO_DATA(invalid_projection_request)', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
