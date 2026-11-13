"""Human acknowledgement logic mixed into the existing execution journal.

No authority is minted here; host witnesses are required at every use.
"""
import hashlib
import json
import sqlite3
from contextlib import closing

from .delegation import Failure, HEX, LABEL, encode, sha
from .reuse import instrument


class UncertaintyAcknowledgements:
    def _identity(self, db):
        rows = db.execute('SELECT id FROM journal_identity').fetchall()
        if len(rows) != 1 or type(rows[0][0]) is not str or not HEX.fullmatch(rows[0][0]):
            raise Failure('EVIDENCE')
        return rows[0][0]

    def identity(self):
        try:
            with closing(self._connect()) as db:
                return self._identity(db)
        except Failure:
            raise
        except (sqlite3.Error, OSError, ValueError, TypeError):
            raise Failure('EVIDENCE') from None

    def _resolution_witnessed(self, db, run_id, task_ref, raw):
        if not callable(self.resolution_witness):
            return False
        row = db.execute('SELECT task_ref,record FROM resolution_events WHERE run_id=?', (run_id,)).fetchone()
        if row is None or row[0] != task_ref or type(row[1]) is not str or len(row[1].encode()) >= 1024:
            return False
        value = json.loads(row[1])
        keys = {'schema', 'journal_id', 'run_id', 'task_ref', 'prior_ref', 'evidence_ref',
                'authority_ref', 'observed_at', 'decision', 'no_retry', 'reservation_release', 'resolution_ref'}
        if (type(value) is not dict or set(value) != keys
                or value['schema'] != 'preceptoros.lab.uncertainty-ack/1'
                or value['journal_id'] != self._identity(db) or value['run_id'] != run_id
                or value['task_ref'] != task_ref or value['prior_ref'] != hashlib.sha256((raw or '').encode()).hexdigest()
                or value['decision'] != 'ACK_UNKNOWN_RETAIN_RESERVATION'
                or value['no_retry'] is not True or value['reservation_release'] is not False
                or any(type(value[k]) is not str or not HEX.fullmatch(value[k])
                       for k in ('evidence_ref', 'authority_ref', 'resolution_ref'))
                or value['resolution_ref'] != sha({k: v for k, v in value.items() if k != 'resolution_ref'})):
            return False
        instrument('evidence').valid_time(value['observed_at'])
        try:
            return self.resolution_witness(value.copy()) is True
        except Exception:
            return False

    def _ack_record(self, db, run_id, task_ref, evidence_ref, authority_ref, observed_at):
        if (type(run_id) is not str or not LABEL.fullmatch(run_id)
                or any(type(x) is not str or not HEX.fullmatch(x)
                       for x in (task_ref, evidence_ref, authority_ref))):
            raise Failure('EVIDENCE')
        instrument('evidence').valid_time(observed_at)
        old = db.execute('SELECT task_ref,receipt FROM claims WHERE run_id=?', (run_id,)).fetchone()
        if old is None or old[0] != task_ref:
            raise Failure('EVIDENCE')
        prior = self._receipt(old[1], run_id, task_ref)
        if prior is not None and prior['outcome'] != 'UNKNOWN':
            raise Failure('EVIDENCE')
        record = {'schema': 'preceptoros.lab.uncertainty-ack/1', 'journal_id': self._identity(db),
                  'run_id': run_id, 'task_ref': task_ref,
                  'prior_ref': hashlib.sha256((old[1] or '').encode()).hexdigest(),
                  'evidence_ref': evidence_ref, 'authority_ref': authority_ref, 'observed_at': observed_at,
                  'decision': 'ACK_UNKNOWN_RETAIN_RESERVATION', 'no_retry': True,
                  'reservation_release': False}
        record['resolution_ref'] = sha(record)
        if len(encode(record)) >= 1024:
            raise Failure('EVIDENCE')
        return record

    def prepare_unknown_ack(self, run_id, task_ref, *, evidence_ref, authority_ref, observed_at):
        """Read-only proposal for exact human review; conveys no permission."""
        try:
            with closing(self._connect()) as db:
                return self._ack_record(db, run_id, task_ref, evidence_ref, authority_ref, observed_at)
        except Failure:
            raise
        except Exception:
            raise Failure('EVIDENCE') from None

    def acknowledge_unknown(self, run_id, task_ref, *, evidence_ref, authority_ref, observed_at,
                            expected_ref, human_authorize, quiescence):
        """Record human-authorized acknowledgement; never changes outcome or releases budget.

        Host callbacks must independently verify the exact signed decision and
        enforce a durable stop/fence for the old worker. They cannot come from
        task/model JSON. Every later consumer rechecks resolution_witness.
        """
        try:
            if (type(expected_ref) is not str or not HEX.fullmatch(expected_ref)
                    or not all(callable(x) for x in (human_authorize, quiescence, self.resolution_witness))):
                raise Failure('EVIDENCE')
            with closing(self._connect()) as db:
                db.execute('BEGIN IMMEDIATE')
                record = self._ack_record(db, run_id, task_ref, evidence_ref, authority_ref, observed_at)
                if (record['resolution_ref'] != expected_ref or human_authorize(record.copy()) is not True
                        or quiescence(record.copy()) is not True
                        or self.resolution_witness(record.copy()) is not True):
                    raise Failure('PERMISSION')
                existing = db.execute('SELECT task_ref,record FROM resolution_events WHERE run_id=?', (run_id,)).fetchone()
                if existing is not None:
                    if existing != (task_ref, encode(record).decode()):
                        raise Failure('EVIDENCE')
                    return record  # Idempotent retry of the exact acknowledged decision.
                db.execute('INSERT INTO resolution_events VALUES(?,?,?)', (run_id, task_ref, encode(record).decode()))
                if quiescence(record.copy()) is not True or human_authorize(record.copy()) is not True:
                    raise Failure('PERMISSION')
                db.commit()
                return record
        except Failure:
            raise
        except Exception:
            raise Failure('EVIDENCE') from None
