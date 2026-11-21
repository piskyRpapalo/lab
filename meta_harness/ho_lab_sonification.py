"""HO-NATIVE / proposed LAB sonification adapter (EXPERIMENT, not HO canon).

Pure: no I/O, audio device, network, clock reads, permission changes or DB.
The official LAB verifier and a *host-owned* session attestor are injected.
The experiment never authorizes playback; projections carry a common digest.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from decimal import Decimal, ROUND_HALF_UP

MAX_ARTIFACT_BYTES = 4096
MAX_AGE_S = 120
SAMPLE_COUNT = 4
LOW_MS, HIGH_MS = 0, 200
LOW_HZ, HIGH_HZ = 220, 660
NOTE_MS = 160
AMP = 0.12


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      allow_nan=False, separators=(',', ':')).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def reject(cause, *, state='NO_DATA'):
    return {'state': state, 'cause': cause, 'execution_authorized': False,
            'playback_authorized': False, 'audio_events': []}


def _strict_json(raw):
    if type(raw) is not bytes or not (0 < len(raw) <= MAX_ARTIFACT_BYTES):
        raise ValueError('artifact_bounds')

    def no_duplicates(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError('duplicate_json_key')
            obj[key] = value
        return obj

    return json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=no_duplicates,
                      parse_constant=lambda val: (_ for _ in ()).throw(ValueError('nonfinite')),)


def _as_utc(timestamp):
    if type(timestamp) is not str or not timestamp.endswith('Z'):
        raise ValueError('timestamp_not_utc')
    result = dt.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timestamp_not_aware')
    return result.astimezone(dt.timezone.utc)


def _frequency_ms(value):
    # Host policy, not the min and max of the current samples.
    value_dec = Decimal(value)
    ratio = (value_dec - LOW_MS) * (HIGH_HZ - LOW_HZ) / (HIGH_MS - LOW_MS)
    return int((Decimal(LOW_HZ) + ratio).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def project(receipt, artifact_bytes, *, verify_receipt, attest_receipt,
            host_read_time, max_age_s=MAX_AGE_S):
    """Return a non-authoritative, 4-channel proposal from witnessed LAB data.

    `verify_receipt` must be LAB's exact `delegation.verify`.
    `attest_receipt` must be a HOST-owned witness, e.g. Session.attests
    bound to the actual task (never a model-provided boolean or hash).
    The full sample artifact's bytes must match receipt.measurement.output_sha256.
    No playback permission can be granted by this function.
    """
    if not callable(verify_receipt) or not callable(attest_receipt):
        return reject('independent_lab_verifiers_missing')
    if type(receipt) is not dict:
        return reject('lab_receipt_missing')
    try:
        if verify_receipt(receipt) is not True:
            return reject('lab_receipt_not_verified')
        if attest_receipt(receipt) is not True:
            return reject('lab_host_witness_missing')
    except Exception:
        return reject('lab_verifier_error')

    m = receipt.get('measurement')
    if (receipt.get('schema') != 'preceptoros.meta-receipt/1'
        or receipt.get('phase') != 'complete' or receipt.get('failure_class') != 'NONE'
        or receipt.get('outcome') != 'KNOWN'
        or type(m) is not dict or m.get('grade') not in ('PASS', 'NOT_EVALUATED')
        or type(m.get('output_sha256')) is not str):
        return reject('lab_result_not_numeric_candidate')
    if (type(artifact_bytes) is not bytes or len(artifact_bytes) > MAX_ARTIFACT_BYTES
        or hashlib.sha256(artifact_bytes).hexdigest() != m['output_sha256']):
        return reject('lab_sample_artifact_sha_mismatch')
    if (type(host_read_time) is not dt.datetime or host_read_time.tzinfo is None
        or type(max_age_s) is not int or not 1 <= max_age_s <= MAX_AGE_S):
        return reject('host_clock_or_freshness_policy_invalid')
    try:
        at = _as_utc(receipt['observed_at'])
        exact_age = (host_read_time.astimezone(dt.timezone.utc)-at).total_seconds()
        age = math.ceil(exact_age)
        if exact_age < 0:
            return reject('lab_observation_from_future')
        data = _strict_json(artifact_bytes)
    except (ValueError, TypeError, KeyError, UnicodeDecodeError, OverflowError):
        return reject('lab_artifact_or_time_invalid')
    if type(data) is not dict or set(data) != {'model_ref', 'measure_kind', 'unit', 'samples'}:
        return reject('lab_measurement_fields_invalid')
    if data['model_ref'] != receipt.get('specialist'):
        return reject('lab_model_identity_mismatch')
    if data['measure_kind'] != 'latency' or data['unit'] != 'ms':
        return reject('lab_measure_kind_or_unit_invalid')
    samples = data['samples']
    if type(samples) is not list or len(samples) != SAMPLE_COUNT:
        return reject('lab_samples_missing_or_wrong_count')
    if any(type(v) is not int or v < LOW_MS or v > HIGH_MS for v in samples):
        return reject('lab_sample_invalid_or_out_of_scale')

    fresh = exact_age <= max_age_s
    # A self-hash and Session.attests prove LAB execution, not a physical
    # measurement. Non-synthetic data needs a metric-specific host witness.
    if receipt.get('confidence_basis') != 'synthetic':
        return reject('lab_physical_measurement_witness_missing')
    state, cause = 'SIMULATED', 'synthetic_fixture_not_physical_measurement'
    if not fresh:
        state, cause = 'STALE', 'observation_expired'
    series = []
    for i, v in enumerate(samples):
        trend = 'start' if i == 0 else 'up' if v > samples[i - 1] else 'down' if v < samples[i - 1] else 'flat'
        series.append({'index': i, 'value_ms': v, 'hz': _frequency_ms(v),
                       'duration_ms': NOTE_MS, 'trend': trend})
    core = {'source_ref': 'preceptoros.meta-receipt/1',
            'receipt_ref': receipt['receipt_ref'], 'observed_at': receipt['observed_at'],
            'age_s': age, 'state': state, 'cause': cause,
            'basis': receipt.get('confidence_basis'), 'model_ref': data['model_ref'],
            'model_version_ref': receipt['model_version'],
            'measure_kind': 'latency', 'unit': 'ms',
            'scale': {'min': LOW_MS, 'max': HIGH_MS}, 'series': series,
            'playback_permission': 'DENIED', 'playback_cause': 'independent_user_gesture_and_grant_not_verified'}
    core_ref = digest(core)
    numbers = ', '.join(str(s['value_ms']) for s in series)
    status_text = f"{state}: {cause}; " if cause else f"{state}: "
    spoken = (f"{status_text}{data['model_ref']}; cuatro latencias en milisegundos: {numbers}. "
              f"Tendencia: {series[-1]['value_ms']-series[0]['value_ms']:+d} milisegundos. "
              "Sonido no autorizado; datos exactos disponibles.")
    # A sound PLAN is allowed, a playable/sounding payload is not. Freshness
    # also suppresses notes if source has expired.
    events = ([{'index': s['index'], 'frequency_hz': s['hz'],
                'duration_ms': NOTE_MS, 'max_amplitude': AMP} for s in series]
              if fresh else [])
    return {'state': state, 'cause': cause, 'semantic_ref': core_ref,
            'record': core, 'views': {
                'text': {'state_ref': core_ref, 'text': spoken},
                'speech': {'state_ref': core_ref, 'text': spoken, 'audio_generated': False},
                'plot': {'state_ref': core_ref, 'points': [(s['index'], s['value_ms']) for s in series],
                         'unit': 'ms', 'scale': [LOW_MS, HIGH_MS]},
                'machine': {'state_ref': core_ref, 'record': core},
                'sound_proposal': {'state_ref': core_ref, 'notes': events,
                                   'playback_authorized': False,
                                   'actual_audio': False}},
            'execution_authorized': False, 'playback_authorized': False}
