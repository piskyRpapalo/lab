"""Read-only LAB -> private-rack Notebook observation, not an authority bridge.

The host supplies an existing ReadOnlyMirror with an allowlisted journal/task
and source witness. No caller can select a filesystem path or permission.
No database, user memory, prompts, or private model/node names are exported.
A checked local receipt is not an independent witness of a worker's effect.
"""
from .delegation import HEX, encode, sha
from .readonly_mirror import ReadOnlyMirror

SCHEMA = 'preceptoros.lab.rack-memory-observation/1'
SUMMARY = {
    'UNKNOWN': 'Outcome unknown. Token reservation is retained or unverified. Do not retry; human and host review required.',
    'KNOWN': 'A completed local receipt exists. Only exact journal replay is allowed; no effect or remote authority is attested.',
    'NO_DATA': 'Local journal evidence is unavailable. No execution or retry is authorized.',
}
ALLOWED_CAUSES = frozenset({
    'execution_outcome_unknown', 'journal_receipt_known',
    'host_clock_invalid', 'source_not_allowlisted', 'local_source_not_attested',
    'source_busy_or_wal_not_supported', 'source_unavailable_or_unsafe',
    'journal_unavailable_or_invalid', 'exact_claim_missing',
    'known_receipt_not_verified', 'source_changed', 'projection_invalid',
    'claim_not_uncertain',
})


def _ref(value):
    return type(value) is str and HEX.fullmatch(value) is not None


def _build(state, cause, *, observed_at, task_ref=None, source_ref=None,
           evidence_ref=None, receipt_ref=None, budget_state='NO_DATA',
           acknowledgement='NO_DATA'):
    if state not in SUMMARY or cause not in ALLOWED_CAUSES:
        state, cause = 'NO_DATA', 'projection_invalid'
    record = {
        'schema': SCHEMA, 'execution_state': state,
        'budget_state': budget_state if budget_state in ('RETAINED', 'SETTLED') else 'NO_DATA',
        'retry_policy': 'REPLAY_ONLY' if state == 'KNOWN' else 'NO_RETRY',
        'acknowledgement': acknowledgement if acknowledgement in
            ('HITL_REQUIRED', 'HUMAN_ACKNOWLEDGED', 'AUTHORITY_NOT_VERIFIED', 'NOT_APPLICABLE')
            else 'NO_DATA',
        'cause': cause, 'observed_at': observed_at,
        'expires_at': observed_at, 'ttl_seconds': 0,
        'task_ref': task_ref if _ref(task_ref) else None,
        'source_ref': source_ref if _ref(source_ref) else None,
        'evidence_ref': evidence_ref if _ref(evidence_ref) else None,
        'receipt_ref': receipt_ref if _ref(receipt_ref) else None,
        'provenance': 'LOCAL_JOURNAL_SNAPSHOT' if state != 'NO_DATA' else 'NO_DATA',
        'authority': 'NOT_AUTHORIZED', 'independent_witness': 'NO_DATA',
        'summary': SUMMARY[state],
    }
    record['state_ref'] = sha(record)
    if len(encode(record)) >= 1024:
        raise ValueError('app_memory_projection_budget_exceeded')
    return record


def project(mirror, source_id, *, observed_at):
    """One ephemeral, immutable-by-contract observation for APP Notebook.

    The read is re-verified against its host source. A checksum alone is not
    testimony; a failure always maps to NO_DATA and NO_RETRY. TTL0 is
    a demand to re-read, never a caching freshness guarantee.
    """
    if type(mirror) is not ReadOnlyMirror:
        return _build('NO_DATA', 'projection_invalid', observed_at=None)
    try:
        packet = mirror.read(source_id, observed_at=observed_at)
        if not mirror.verify(packet, source_id, observed_at=observed_at):
            return _build('NO_DATA', 'source_changed', observed_at=observed_at)
        if (type(packet) is not dict or set(packet) != {'text', 'speech', 'machine'}
                or type(packet['machine']) is not dict
                or type(packet['text']) is not dict
                or type(packet['speech']) is not dict):
            return _build('NO_DATA', 'projection_invalid', observed_at=observed_at)
        record = packet['machine'].get('record')
        if (type(record) is not dict
                or record.get('schema') != 'preceptoros.lab.uncertainty-ack/1'
                or record.get('ttl_seconds') != 0
                or record.get('no_retry') is not True
                or record.get('promotion') != 'NOT_AUTHORIZED'
                or not _ref(record.get('projection_ref'))
                or packet['text'].get('state_ref') != record['projection_ref']
                or packet['speech'].get('state_ref') != record['projection_ref']
                or packet['text'].get('summary') != packet['speech'].get('summary')):
            return _build('NO_DATA', 'projection_invalid', observed_at=observed_at)

        state = record['state']
        if state == 'UNKNOWN':
            if not _ref(record.get('journal_id')) or not _ref(record.get('task_ref')):
                return _build('NO_DATA', 'projection_invalid', observed_at=observed_at)
            reservation = record.get('reservation')
            retained = (type(reservation) is dict
                        and reservation.get('state') == 'RETAINED'
                        and type(reservation.get('tokens')) is int
                        and 0 <= reservation['tokens'] <= 512)
            return _build(
                'UNKNOWN', 'execution_outcome_unknown', observed_at=observed_at,
                task_ref=record['task_ref'],
                source_ref=sha({'journal_id': record['journal_id'],
                                'task_ref': record['task_ref']}),
                evidence_ref=record['projection_ref'],
                budget_state='RETAINED' if retained else 'NO_DATA',
                acknowledgement=record.get('acknowledgement'))
        if state == 'NO_DATA' and record.get('cause') == 'claim_not_uncertain':
            # ReadOnlyMirror's uncertainty projection is *not* a KNOWN proof.
            # A separate, read-only exact-receipt verification is required.
            completed = mirror.read_known(source_id, observed_at=observed_at)
            if (type(completed) is not dict or not all(_ref(completed.get(k))
                    for k in ('journal_id', 'task_ref', 'receipt_ref'))):
                return _build('NO_DATA', 'known_receipt_not_verified',
                              observed_at=observed_at)
            return _build(
                'KNOWN', 'journal_receipt_known', observed_at=observed_at,
                task_ref=completed['task_ref'],
                source_ref=sha({'journal_id': completed['journal_id'],
                                'task_ref': completed['task_ref']}),
                evidence_ref=completed['receipt_ref'],
                receipt_ref=completed['receipt_ref'],
                budget_state=completed.get('budget_state'),
                acknowledgement='NOT_APPLICABLE')
        return _build('NO_DATA',
                      record.get('cause') if record.get('cause') in ALLOWED_CAUSES
                      else 'projection_invalid',
                      observed_at=record.get('observed_at'))
    except Exception:
        return _build('NO_DATA', 'projection_invalid', observed_at=None)


def verify(record, mirror, source_id, *, observed_at):
    """Re-measure current host journal; digest equality by itself is insufficient."""
    try:
        return (type(record) is dict and len(encode(record)) < 1024
                and record == project(mirror, source_id, observed_at=observed_at)
                and record.get('state_ref') == sha({k: v for k, v in record.items()
                                                 if k != 'state_ref'}))
    except Exception:
        return False
