"""Bounded decision-only prototype; existing host contracts must attest inputs.

Never dispatches, grants, reserves resources, trains or writes memory. Positive
synthetic controls remain SIMULATED_ELIGIBLE, not measured node capabilities.
Measured inputs also abstain until the final production contract is connected.
"""
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import re

HEX = re.compile(r'[a-f0-9]{64}\Z')
NODES = tuple('node-' + c for c in 'abcde')
BACKENDS = ('default', 'primary', 'secondary')
PROFILE_KEYS = {'origin', 'task_profile_ref', 'node', 'backend', 'model_version', 'source_ref',
                'observed_at', 'peak_ram_bytes', 'headroom_bytes', 'latency_ms',
                'quality_pass', 'independent_cases', 'concurrency_ceiling', 'pressure_limit_pct', 'profile_ref'}


class EvidenceTimeError(ValueError):
    pass


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(encode(value)).hexdigest()


def profile_key(task):
    return sha({k: v for k, v in task.items() if k != 'run_id'})


def age_seconds(value, now):
    try:
        captured = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (TypeError, AttributeError, ValueError):
        raise EvidenceTimeError('CLOCK_INVALID') from None
    if captured.utcoffset() is None or now.utcoffset() is None:
        raise EvidenceTimeError('CLOCK_INVALID')
    age = (now - captured).total_seconds()
    if age < 0 or not math.isfinite(age):
        raise EvidenceTimeError('EVIDENCE_FUTURE')
    return age


@dataclass(frozen=True)
class Host:
    # Trusted read-only bounded callbacks, never populated from model JSON.
    validate_task: object
    authorize: object  # Validated exact-task grant -> approval_ref, else None.
    verify_projection: object  # Original source + pinned ref + HOST clock.
    witness: object  # Independent evaluation/resource ledger, not a self-hash.
    human_signature: object = None


def decide(task, packets, profiles, policy, *, host, now, cancelled=lambda: False):
    """Return a proposal or abstention. Even an eligible proposal is not a grant."""
    task_ref = None
    def result(cause, choice=None, mode=None):
        record = {'kind': 'resource-decision-proposal', 'state':
                  'SIMULATED_ELIGIBLE' if choice and mode == 'SYNTHETIC' else 'ABSTAIN',
                  'cause': cause, 'task_ref': task_ref, 'choice': choice,
                  'mode': 'OFFLINE_PROTOTYPE', 'production_contract': 'NOT_CONNECTED',
                  'dispatch_authorized': False, 'memory_promotion_authorized': False}
        record['decision_ref'] = sha(record)
        if len(encode(record)) >= 1024:
            raise ValueError('decision_budget')
        return record
    try:
        if cancelled():
            return result('CANCELLED')
        if (not isinstance(host, Host) or not all(callable(getattr(host, k)) for k in
                ('validate_task', 'authorize', 'verify_projection', 'witness'))):
            return result('HOST_CONTRACT_MISSING')
        if type(task) is not dict or len(encode(task)) >= 1024 or host.validate_task(copy.deepcopy(task)) is not True:
            return result('TASK_CONTRACT_INVALID')
        task = copy.deepcopy(task)
        task_ref = sha(task)
        if (task.get('schema') != 'preceptoros.meta-task/1' or type(task.get('model_version')) is not str
                or not HEX.fullmatch(task['model_version']) or type(task.get('timeout_ms')) is not int
                or not 1 <= task['timeout_ms'] <= 30000):
            return result('TASK_CONTRACT_INVALID')
        if (type(policy) is not dict or set(policy) != {'tokens_remaining', 'max_depth', 'requires_human',
                'human_ref', 'active_jobs', 'min_cases'} or any(type(policy[k]) is not int or policy[k] < 0
                for k in ('tokens_remaining', 'max_depth', 'active_jobs', 'min_cases'))
                or type(policy['requires_human']) is not bool or policy['min_cases'] < 1):
            return result('POLICY_EVIDENCE_MISSING')
        policy = copy.deepcopy(policy)
        if policy['requires_human'] and (type(policy['human_ref']) is not str or not HEX.fullmatch(policy['human_ref'])
                or not callable(host.human_signature)
                or host.human_signature(copy.deepcopy(task), policy['human_ref']) is not True):
            return result('HUMAN_SIGNATURE_REQUIRED')
        approval = host.authorize(copy.deepcopy(task))
        if type(approval) is not str or not HEX.fullmatch(approval):
            return result('PERMISSION_DENIED')
        if (type(task.get('max_tokens')) is not int or type(task.get('depth')) is not int
                or task['max_tokens'] < 0 or task['depth'] < 0
                or task['max_tokens'] > policy['tokens_remaining'] or task['depth'] > policy['max_depth']):
            return result('BUDGET_INSUFFICIENT')
        if (type(packets) is not list or not 1 <= len(packets) <= 8 or type(profiles) is not list
                or len(profiles) > 16 or len(encode([packets, profiles])) > 262144):
            return result('INPUT_BOUND_EXCEEDED')
        if now.utcoffset() is None:
            return result('CLOCK_INVALID')
        packets, profiles = copy.deepcopy(packets), copy.deepcopy(profiles)
        eligible, rejected, seen = [], [], set()
        for packet in packets:
            if cancelled():
                return result('CANCELLED')
            if host.verify_projection(copy.deepcopy(packet)) is not True:
                rejected.append('PROJECTION_NOT_WITNESSED'); continue
            record = packet.get('record', {})
            if (type(record) is not dict or record.get('schema') != 'preceptoros.lab.node-metadata/1'
                    or record.get('kind') != 'projection' or record.get('node') not in NODES
                    or record.get('backend') not in BACKENDS or type(record.get('source_ref')) is not str
                    or not HEX.fullmatch(record['source_ref'])):
                rejected.append('NODE_EVIDENCE_INVALID'); continue
            identity = (record['node'], record['backend'])
            if identity in seen:
                return result('DUPLICATE_BACKEND')
            seen.add(identity)
            if record.get('state') == 'STALE':
                rejected.append('EVIDENCE_STALE'); continue
            if record.get('state') != 'OBSERVED' or record.get('responds_now', {}).get('state') != 'OBSERVED':
                rejected.append('NODE_UNAVAILABLE'); continue
            if age_seconds(record['observed_at'], now) > 120:
                rejected.append('EVIDENCE_STALE'); continue
            models = record.get('models', {})
            items = models.get('items') if type(models) is dict else None
            if (type(items) is not list or len(items) > 256 or not any(type(m) is dict
                    and m.get('model_version') == task.get('model_version') for m in items)):
                rejected.append('MODEL_IDENTITY_MISMATCH'); continue
            matches = [p for p in profiles if type(p) is dict and p.get('node') == record['node']
                       and p.get('backend') == record['backend'] and p.get('model_version') == task['model_version']
                       and p.get('task_profile_ref') == profile_key(task) and p.get('source_ref') == record['source_ref']]
            if len(matches) != 1:
                rejected.append('TASK_RESOURCE_EVIDENCE_MISSING'); continue
            profile = copy.deepcopy(matches[0])
            if (set(profile) != PROFILE_KEYS or profile['origin'] not in ('SYNTHETIC', 'MEASURED')
                    or type(profile['profile_ref']) is not str or not HEX.fullmatch(profile['profile_ref'])
                    or profile['profile_ref'] != sha({k: v for k, v in profile.items() if k != 'profile_ref'})
                    or host.witness(copy.deepcopy(profile), copy.deepcopy(task), copy.deepcopy(record)) is not True):
                rejected.append('PROFILE_NOT_WITNESSED'); continue
            if age_seconds(profile['observed_at'], now) > 120:
                rejected.append('PROFILE_STALE'); continue
            fields = ('peak_ram_bytes', 'headroom_bytes', 'latency_ms', 'independent_cases', 'concurrency_ceiling')
            if profile['quality_pass'] is False:
                rejected.append('MODEL_TASK_FAILURE'); continue
            if (any(type(profile[k]) is not int or profile[k] < 0 for k in fields)
                    or profile['quality_pass'] is not True or profile['peak_ram_bytes'] < 1
                    or profile['latency_ms'] < 1 or profile['independent_cases'] < policy['min_cases']
                    or profile['concurrency_ceiling'] < 1):
                rejected.append('QUALITY_OR_CALIBRATION_INSUFFICIENT'); continue
            memory, resources = record.get('memory', {}), record.get('resources', {})
            pressure = resources.get('pressure', {}) if type(resources) is dict else {}
            axes = pressure.get('avg10', {}) if type(pressure) is dict else {}
            limit = profile['pressure_limit_pct']
            if (type(memory) is not dict or memory.get('state') != 'OBSERVED'
                    or type(memory.get('available_bytes')) is not int or memory['available_bytes'] < 0
                    or type(pressure) is not dict or pressure.get('state') != 'OBSERVED'
                    or type(axes) is not dict or set(axes) != {'cpu', 'memory', 'io'}
                    or any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 100 for v in axes.values())
                    or type(limit) not in (int, float) or not math.isfinite(limit) or not 0 <= limit <= 100):
                rejected.append('RESOURCE_TELEMETRY_MISSING'); continue
            if policy['active_jobs'] >= profile['concurrency_ceiling'] or max(axes.values()) > limit:
                rejected.append('NODE_SATURATION'); continue
            if profile['peak_ram_bytes'] + profile['headroom_bytes'] > memory['available_bytes']:
                rejected.append('RESOURCE_SHORTFALL'); continue
            if profile['latency_ms'] > task['timeout_ms']:
                rejected.append('LATENCY_ENVELOPE_EXCEEDS_BUDGET'); continue
            eligible.append((record, profile, approval, packet))
        if cancelled():
            return result('CANCELLED')
        if len(eligible) > 1:
            return result('MULTIPLE_ELIGIBLE_REQUIRES_HOST_CHOICE')
        if not eligible:
            return result(rejected[0] if rejected and len(set(rejected)) == 1 else 'EVIDENCE_INSUFFICIENT')
        record, profile, approval, packet = eligible[0]
        if (host.authorize(copy.deepcopy(task)) != approval
                or host.verify_projection(copy.deepcopy(packet)) is not True
                or host.witness(copy.deepcopy(profile), copy.deepcopy(task), copy.deepcopy(record)) is not True):
            return result('FINAL_HOST_RECHECK_FAILED')
        if profile['origin'] != 'SYNTHETIC':
            return result('PRODUCTION_ADMISSION_NOT_CONNECTED')
        return result('TASK_AND_RESOURCES_WITNESSED', {'node': record['node'], 'backend': record['backend'],
            'model_version': task['model_version'], 'source_ref': record['source_ref'],
            'profile_ref': profile['profile_ref'], 'approval_ref': approval}, profile['origin'])
    except EvidenceTimeError as error:
        return result(str(error) if str(error) in ('CLOCK_INVALID', 'EVIDENCE_FUTURE') else 'HOST_OR_EVIDENCE_ERROR')
    except Exception:
        # Callback and malformed-input errors never become fallback, grants or raw logs.
        return result('HOST_OR_EVIDENCE_ERROR')
