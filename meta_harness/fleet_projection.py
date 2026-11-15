"""Pure display projection of host-supplied fleet observations, never admission.

No discovery, identity registry, network, resource packet or permission is created.
The source verifier is host-owned; matching hashes alone do not authenticate it.
"""
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional, Tuple

from .resource_admission import resources

FIELDS = frozenset({'os', 'architecture', 'memory_total_bytes', 'memory_available_bytes',
                    'storage_available_bytes', 'catalog_models', 'loaded_models', 'reachable'})
MAX_BYTES = 262144


@dataclass(frozen=True)
class Observation:
    node_ref: str
    field: str
    value: object
    source_ref: str
    observed_at: str
    basis: str  # OBSERVED or DECLARED; neither is authority.


def _ref(value):
    return type(value) is str and resources.HEX.fullmatch(value) is not None


def _value(field, value):
    if field == 'os':
        return type(value) is str and value in ('Linux', 'Darwin', 'Windows')
    if field == 'architecture':
        return type(value) is str and value in ('x86_64', 'aarch64', 'arm64', 'armv7l')
    if field == 'reachable':
        return type(value) is bool
    if field in ('catalog_models', 'loaded_models'):
        return (type(value) in (list, tuple) and len(value) <= 128
                and all(_ref(v) for v in value) and len(set(value)) == len(value))
    return type(value) is int and 0 <= value < 2**63


def _missing(cause):
    return {'state': 'NO_DATA', 'cause': cause}


def project(nodes: Tuple[str, ...], observations: Tuple[Observation, ...], *,
            now: datetime, verify_source: Optional[Callable] = None):
    """Return bounded details and compact receipt; source fields are explicitly selected.

    nodes comes from the existing private inventory, up to six opaque references.
    OBSERVED means accepted source evidence, NOT current process liveness or physical
    node authentication. No field here can make a resource eligible for dispatch.
    Unknown fields/invalid envelopes fail closed and are never echoed.
    """
    if (type(nodes) is not tuple or not 1 <= len(nodes) <= 6
            or not all(_ref(n) for n in nodes) or len(set(nodes)) != len(nodes)
            or type(observations) is not tuple or len(observations) > 256
            or type(now) is not datetime or now.utcoffset() != timezone.utc.utcoffset(now)):
        raise ValueError('projection_input_invalid')
    rows = []
    for o in observations:
        if (type(o) is not Observation or o.node_ref not in nodes or o.field not in FIELDS
                or not _ref(o.source_ref) or o.basis not in ('OBSERVED', 'DECLARED')
                or type(o.observed_at) is not str or len(o.observed_at) > 64
                or not _value(o.field, o.value)):
            raise ValueError('observation_invalid')
        rows.append(copy.deepcopy(o.__dict__))
    if len(resources.encode(rows)) > MAX_BYTES:
        raise ValueError('projection_input_bound')
    details = []
    for node in sorted(nodes):
        fields = {}
        for field in sorted(FIELDS):
            matches = [o for o in rows if o['node_ref'] == node and o['field'] == field]
            if len(matches) != 1:
                fields[field] = _missing('source_absent' if not matches else 'conflicting_observations')
                continue
            row = matches[0]
            try:
                age = resources.age_seconds(row['observed_at'], now)
            except resources.EvidenceTimeError:
                fields[field] = _missing('clock_invalid_or_future')
                continue
            if not callable(verify_source):
                fields[field] = _missing('source_verifier_missing')
                continue
            try:
                verified = verify_source(copy.deepcopy(row)) is True
            except Exception:
                verified = False
            if not verified:
                fields[field] = _missing('source_not_witnessed')
                continue
            value = copy.deepcopy(row['value'])
            if field in ('catalog_models', 'loaded_models'):
                value = sorted(value)
            fields[field] = dict(state='STALE' if age > 120 else row['basis'],
                cause='evidence_expired' if age > 120 else 'source_evidence_only',
                value=value, basis=row['basis'], source_ref=row['source_ref'], observed_at=row['observed_at'])
        # Contradictory measurements cannot be presented as usable available memory.
        total, available = fields['memory_total_bytes'], fields['memory_available_bytes']
        if (total.get('state') == available.get('state') == 'OBSERVED'
                and total.get('observed_at') == available.get('observed_at')
                and total.get('source_ref') == available.get('source_ref')
                and available['value'] > total['value']):
            fields['memory_available_bytes'] = _missing('memory_observations_inconsistent')
        details.append({'node_ref': node, 'fields': fields, 'authority': 'none',
                        'admission': _missing('task_host_route_and_lease_not_bound')})
    summary = dict(schema='preceptoros.fleet-projection/1', state='PROJECTED',
        cause='display_only_not_resource_admission', node_count=len(details),
        observed_at=now.isoformat(), details_ref=resources.sha(details), authority='none',
        dispatch_authorized=False, physical_presence_verified=False)
    summary['receipt_ref'] = resources.sha(summary)
    if len(resources.encode(summary)) >= 1024 or len(resources.encode(details)) > MAX_BYTES:
        raise ValueError('projection_output_bound')
    return {'summary': summary, 'details': details}
