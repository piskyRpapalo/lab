"""Read-only fail-closed host boundary for P2 acknowledgements.

The existing PR HITL line does not bind a P2 decision and a terminated process
is not a durable fence. No source currently attests either fact. This adapter
does not create authority and cannot return True for the three P2 callbacks.
"""
from datetime import datetime, timezone

from .delegation import HEX, LABEL, sha

KEYS = {'schema', 'journal_id', 'run_id', 'task_ref', 'prior_ref', 'evidence_ref',
        'authority_ref', 'observed_at', 'decision', 'no_retry', 'reservation_release', 'resolution_ref'}


class HostWitness:
    """Host-pinned identity and task; caller never supplies authority callbacks."""
    def __init__(self, journal_id, task_ref, *, now=lambda: datetime.now(timezone.utc)):
        if any(type(x) is not str or not HEX.fullmatch(x) for x in (journal_id, task_ref)) or not callable(now):
            raise ValueError('host_pin_invalid')
        self.journal_id, self.task_ref, self.now = journal_id, task_ref, now

    def diagnose(self, record):
        cause = 'human_authority_and_durable_fence_unavailable'
        try:
            if (type(record) is not dict or set(record) != KEYS
                    or record['schema'] != 'preceptoros.lab.uncertainty-ack/1'
                    or type(record['run_id']) is not str or not LABEL.fullmatch(record['run_id'])
                    or any(type(record[k]) is not str or not HEX.fullmatch(record[k])
                           for k in ('journal_id','task_ref','prior_ref','evidence_ref','authority_ref','resolution_ref'))
                    or record['decision'] != 'ACK_UNKNOWN_RETAIN_RESERVATION'
                    or record['no_retry'] is not True or record['reservation_release'] is not False
                    or record['resolution_ref'] != sha({k:v for k,v in record.items() if k != 'resolution_ref'})):
                cause = 'record_invalid'
            elif record['journal_id'] != self.journal_id:
                cause = 'journal_identity_mismatch'
            elif record['task_ref'] != self.task_ref:
                cause = 'task_identity_mismatch'
            else:
                seen = datetime.fromisoformat(record['observed_at'].replace('Z', '+00:00'))
                now = self.now()
                if seen.utcoffset() is None or now.utcoffset() is None:
                    cause = 'clock_invalid'
                elif (now-seen).total_seconds() < 0:
                    cause = 'evidence_from_future'
                elif (now-seen).total_seconds() > 120:
                    cause = 'evidence_expired'
        except Exception:
            cause = 'record_invalid'
        return {'state':'NO_DATA', 'cause':cause, 'human_authorize':False,
                'quiescence':False, 'resolution_witness':False}

    def human_authorize(self, record):
        self.diagnose(record)
        return False

    def quiescence(self, record):
        self.diagnose(record)
        return False

    def resolution_witness(self, record):
        self.diagnose(record)
        return False
