"""Offline host projection of an uncertain journal claim, never an authority.

Text, speech and machine views bind the same immutable record. A consumer must
recompute against the host journal and current witness, not trust a self-hash.
"""
from contextlib import closing
import copy
import json

from .delegation import encode, sha, validate_task
from .reuse import instrument


def project(journal, task, *, observed_at):
    instrument('evidence').valid_time(observed_at)
    task = copy.deepcopy(task)
    validate_task(task)
    task_ref = sha(task)
    state, acknowledgement, cause = 'NO_DATA', 'NO_DATA', 'journal_unavailable_or_invalid'
    journal_id, resolution_ref, reservation = None, None, {'state':'NO_DATA', 'cause':'reservation_unavailable'}
    try:
        with closing(journal._connect()) as db:
            db.execute('BEGIN')
            journal_id = journal._identity(db)
            row = db.execute('SELECT task_ref,receipt FROM claims WHERE run_id=?', (task['run_id'],)).fetchone()
            if row is None or row[0] != task_ref:
                cause = 'exact_claim_missing'
            else:
                prior = journal._receipt(row[1], task['run_id'], task_ref)
                if prior is not None and prior['outcome'] != 'UNKNOWN':
                    cause = 'claim_not_uncertain'
                else:
                    state, cause = 'UNKNOWN', 'execution_outcome_unknown'
                    event = db.execute('SELECT record FROM resolution_events WHERE run_id=?', (task['run_id'],)).fetchone()
                    if event is None:
                        acknowledgement = 'HITL_REQUIRED'
                    elif journal._resolution_witnessed(db, task['run_id'], task_ref, row[1]):
                        acknowledgement = 'HUMAN_ACKNOWLEDGED'
                        resolution_ref = json.loads(event[0])['resolution_ref']
                    else:
                        acknowledgement = 'AUTHORITY_NOT_VERIFIED'
                    if journal._budget_enabled(db):
                        budget = db.execute('SELECT cap,status FROM budget_reservations WHERE run_id=?', (task['run_id'],)).fetchone()
                        if (budget is not None and type(budget[0]) is int and 0 <= budget[0] <= 512
                                and budget[1] in ('RESERVED', 'UNKNOWN')):
                            reservation = {'state':'RETAINED', 'tokens':budget[0]}
                        else:
                            reservation = {'state':'NO_DATA', 'cause':'reservation_inconsistent'}
                    else:
                        reservation = {'state':'NO_DATA', 'cause':'durable_budget_not_configured'}
    except Exception:
        state, acknowledgement, cause = 'NO_DATA', 'NO_DATA', 'journal_unavailable_or_invalid'
        journal_id, resolution_ref = None, None
        reservation = {'state':'NO_DATA', 'cause':'reservation_unavailable'}
    if state == 'UNKNOWN':
        text = {'HITL_REQUIRED':'Outcome unknown; human review and a worker fence are required.',
                'HUMAN_ACKNOWLEDGED':'Outcome unknown; human acknowledgement and worker fence are witnessed.',
                'AUTHORITY_NOT_VERIFIED':'Outcome unknown; acknowledgement or worker fence cannot be verified.'}[acknowledgement]
        text += ' Token reservation is retained.' if reservation['state']=='RETAINED' else ' Token reservation is unknown.'
    else:
        text = 'Uncertain execution state is unavailable; check the host journal.'
    record = {'schema':'preceptoros.lab.uncertainty-ack/1', 'kind':'projection',
              'state':state, 'cause':cause, 'acknowledgement':acknowledgement,
              'observed_at':observed_at, 'journal_id':journal_id, 'task_ref':task_ref,
              'resolution_ref':resolution_ref, 'reservation':reservation,
              'ttl_seconds':0, 'no_retry':True, 'promotion':'NOT_AUTHORIZED', 'summary':text}
    record['projection_ref'] = sha(record)
    if len(encode(record)) >= 1024:
        raise ValueError('projection_budget')
    return record


def views(record):
    if (type(record) is not dict or record.get('kind') != 'projection'
            or record.get('projection_ref') != sha({k:v for k,v in record.items() if k != 'projection_ref'})
            or len(encode(record)) >= 1024):
        raise ValueError('projection_invalid')
    ref = record['projection_ref']
    return {'text':{'state_ref':ref,'summary':record['summary']},
            'speech':{'state_ref':ref,'summary':record['summary']},
            'machine':{'state_ref':ref,'record':copy.deepcopy(record)}}


def verify(packet, journal, task, *, observed_at):
    """A valid self-hash alone is not host or human attestation."""
    try:
        return packet == views(project(journal, task, observed_at=observed_at))
    except Exception:
        return False
