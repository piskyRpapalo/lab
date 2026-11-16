"""Explicit host-owned SQLite claims for the existing Session; no dispatch or retry.

Create only a new private file. Unknown claims are never automatically cleared.
The host owns the directory, authorization, budget and reconciliation policy.
"""
import json
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import secrets
import sqlite3
import stat

from .delegation import Failure, encode, verify
from .uncertainty_ack import UncertaintyAcknowledgements

_HEX64 = re.compile(r'[0-9a-f]{64}\Z')


class GrantVerificationSource:
    """Host-owned verifier boundary; it does not issue or sign grants.

    Implementations must verify the existing grant signature, issuer trust,
    exact bindings and current revocation state using the supplied journal
    transaction. No implementation is installed by LAB itself.
    """
    evidence_class = 'UNTRUSTED'

    def verify_for_reservation(self, *, db, binding, now):
        raise NotImplementedError


class ExecutionJournal(UncertaintyAcknowledgements):
    def __init__(self, path, *, resolution_witness=None, grant_source=None,
                 wall_clock=lambda: datetime.now(timezone.utc)):
        self.path = Path(path).absolute()
        self.resolution_witness = resolution_witness
        self.grant_source = grant_source
        self.wall_clock = wall_clock
        self._check()

    @classmethod
    def create(cls, path, *, resolution_witness=None, grant_source=None,
               wall_clock=lambda: datetime.now(timezone.utc)):
        path = Path(path).absolute()
        cls._parent(path)
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        journal = cls(path, resolution_witness=resolution_witness,
                      grant_source=grant_source, wall_clock=wall_clock)
        with closing(journal._connect()) as db:
            db.execute('CREATE TABLE claims (run_id TEXT PRIMARY KEY, task_ref TEXT NOT NULL, receipt TEXT)')
            db.execute('CREATE TABLE journal_identity (id TEXT NOT NULL)')
            db.execute('INSERT INTO journal_identity VALUES(?)', (secrets.token_hex(32),))
            db.execute('CREATE TABLE resolution_events (run_id TEXT PRIMARY KEY, task_ref TEXT NOT NULL, record TEXT NOT NULL)')
            db.execute('CREATE TABLE authorization_reservations ('
                       'grant_id TEXT PRIMARY KEY, run_id TEXT NOT NULL UNIQUE, task_sha256 TEXT NOT NULL, '
                       'agent_id TEXT NOT NULL, host_conditions_sha256 TEXT NOT NULL, grant_sha256 TEXT NOT NULL, '
                       'issuer_ref TEXT NOT NULL, revocation_generation INTEGER NOT NULL, expires_at TEXT NOT NULL, '
                       'evidence_class TEXT NOT NULL, reservation_ref TEXT NOT NULL UNIQUE)')
        return journal

    @staticmethod
    def _parent(path):
        parent = path.parent
        if any(p.is_symlink() for p in (parent, *parent.parents)):
            raise Failure('EVIDENCE')
        info = parent.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise Failure('EVIDENCE')

    def _check(self):
        try:
            self._parent(self.path)
            info = self.path.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                    or info.st_nlink != 1 or info.st_mode & 0o077):
                raise Failure('EVIDENCE')
        except OSError:
            raise Failure('EVIDENCE') from None

    def _connect(self):
        self._check()
        db = sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True, timeout=2, isolation_level=None)
        db.execute('PRAGMA synchronous=FULL')
        return db

    @staticmethod
    def _receipt(raw, run_id, task_ref):
        if raw is None:
            return None
        if type(raw) is not str or len(raw.encode('utf-8')) >= 1024:
            raise Failure('EVIDENCE')
        value = json.loads(raw)
        if (not verify(value) or value['run_id'] != run_id or value['task_sha256'] != task_ref
                or len(encode(value)) >= 1024):
            raise Failure('EVIDENCE')
        return value

    def _require_resolved(self, db):
        rows = db.execute('SELECT run_id,task_ref,receipt FROM claims LIMIT 4097').fetchall()
        if len(rows) > 4096:
            raise Failure('EVIDENCE')
        for old_id, old_ref, raw in rows:
            prior = self._receipt(raw, old_id, old_ref)
            if prior is None or prior['outcome'] == 'UNKNOWN':
                if not self._resolution_witnessed(db, old_id, old_ref, raw):
                    raise Failure('EVIDENCE')

    @staticmethod
    def _budget_enabled(db):
        return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='durable_budget'").fetchone() is not None

    def initialize_budget(self, limit):
        """Explicit one-time initialization on an empty, host-created journal."""
        if type(limit) is not int or not 0 <= limit <= 4096:
            raise Failure('BUDGET')
        try:
            with closing(self._connect()) as db:
                db.execute('BEGIN IMMEDIATE')
                if self._budget_enabled(db) or db.execute('SELECT 1 FROM claims LIMIT 1').fetchone():
                    raise Failure('EVIDENCE')
                db.execute('CREATE TABLE durable_budget (id INTEGER PRIMARY KEY CHECK(id=1), initial_limit INTEGER NOT NULL, remaining INTEGER NOT NULL)')
                db.execute('CREATE TABLE budget_reservations (run_id TEXT PRIMARY KEY, cap INTEGER NOT NULL, status TEXT NOT NULL)')
                db.execute('INSERT INTO durable_budget VALUES(1,?,?)', (limit, limit))
                db.commit()
        except Failure:
            raise
        except (sqlite3.Error, OSError, ValueError, TypeError):
            raise Failure('EVIDENCE') from None

    def remaining_budget(self):
        try:
            with closing(self._connect()) as db:
                row = db.execute('SELECT initial_limit,remaining FROM durable_budget WHERE id=1').fetchone()
                if (row is None or type(row[0]) is not int or type(row[1]) is not int
                        or not 0 <= row[1] <= row[0] <= 4096):
                    raise Failure('EVIDENCE')
                return row[1]
        except Failure:
            raise
        except (sqlite3.Error, OSError, ValueError, TypeError):
            raise Failure('EVIDENCE') from None

    def claim(self, run_id, task_ref, *, budget_cap=None):
        """Atomically deduplicate a journal run; this raw claim is not authorization."""
        try:
            with closing(self._connect()) as db:
                db.execute('BEGIN IMMEDIATE')
                previous = self._claim_in_transaction(db, run_id, task_ref, budget_cap)
                db.commit()
                return previous
        except Failure:
            raise
        except (sqlite3.Error, OSError, ValueError, TypeError):
            raise Failure('EVIDENCE') from None

    def _claim_in_transaction(self, db, run_id, task_ref, budget_cap):
        row = db.execute('SELECT task_ref,receipt FROM claims WHERE run_id=?', (run_id,)).fetchone()
        if row:
            if row[0] != task_ref or row[1] is None:
                raise Failure('REPLAY')
            return ExecutionJournal._receipt(row[1], run_id, task_ref)
        self._require_resolved(db)
        enabled = self._budget_enabled(db)
        if enabled != (budget_cap is not None):
            raise Failure('EVIDENCE')
        if enabled:
            if type(budget_cap) is not int or not 0 <= budget_cap <= 512:
                raise Failure('BUDGET')
            changed = db.execute('UPDATE durable_budget SET remaining=remaining-? WHERE id=1 AND initial_limit BETWEEN 0 AND 4096 AND remaining>=? AND remaining<=initial_limit',
                                 (budget_cap, budget_cap))
            if changed.rowcount != 1:
                raise Failure('BUDGET')
            db.execute('INSERT INTO budget_reservations VALUES(?,?,?)', (run_id, budget_cap, 'RESERVED'))
        db.execute('INSERT INTO claims(run_id,task_ref,receipt) VALUES(?,?,NULL)', (run_id, task_ref))
        return None

    @staticmethod
    def _grant_binding_valid(binding):
        return (type(binding) is dict
                and set(binding) == {'grant_id', 'run_id', 'task_sha256', 'agent_id', 'host_conditions_sha256'}
                and type(binding['grant_id']) is str and _HEX64.fullmatch(binding['grant_id'])
                and type(binding['run_id']) is str and re.fullmatch(r'[a-z][a-z0-9-]{0,31}', binding['run_id'])
                and type(binding['task_sha256']) is str and _HEX64.fullmatch(binding['task_sha256'])
                and type(binding['agent_id']) is str and re.fullmatch(r'[a-z][a-z0-9-]{0,31}', binding['agent_id'])
                and type(binding['host_conditions_sha256']) is str
                and _HEX64.fullmatch(binding['host_conditions_sha256']))

    @staticmethod
    def _grant_source_decision(source, db, binding, now):
        """Validate the verifier result shape; never trust a grant's own booleans."""
        if not isinstance(source, GrantVerificationSource):
            return {'state': 'NO_DATA', 'cause': 'authorization_source_unavailable'}
        try:
            result = source.verify_for_reservation(db=db, binding=dict(binding), now=now)
        except NotImplementedError:
            return {'state': 'NO_DATA', 'cause': 'authorization_source_unavailable'}
        except Exception:
            return {'state': 'NO_DATA', 'cause': 'authorization_verifier_failed'}
        if type(result) is not dict or result.get('state') not in ('VERIFIED', 'REJECTED', 'NO_DATA'):
            return {'state': 'NO_DATA', 'cause': 'authorization_verifier_result_invalid'}
        if result['state'] != 'VERIFIED':
            cause = result.get('cause')
            if type(cause) is not str or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', cause):
                cause = 'authorization_not_verified'
            return {'state': result['state'], 'cause': cause}
        expected = {'state', 'grant_id', 'run_id', 'task_sha256', 'agent_id',
                    'host_conditions_sha256', 'grant_sha256', 'issuer_ref',
                    'revocation_generation', 'expires_at', 'evidence_class'}
        if set(result) != expected:
            return {'state': 'NO_DATA', 'cause': 'authorization_verifier_result_invalid'}
        if any(result.get(key) != binding[key] for key in binding):
            return {'state': 'REJECTED', 'cause': 'authorization_binding_mismatch'}
        for key in ('grant_sha256', 'issuer_ref'):
            if type(result[key]) is not str or not _HEX64.fullmatch(result[key]):
                return {'state': 'NO_DATA', 'cause': 'authorization_evidence_invalid'}
        if type(result['revocation_generation']) is not int or result['revocation_generation'] < 0:
            return {'state': 'NO_DATA', 'cause': 'revocation_generation_unavailable'}
        if result['evidence_class'] not in ('REAL', 'SYNTHETIC'):
            return {'state': 'NO_DATA', 'cause': 'authorization_evidence_class_unavailable'}
        try:
            expires = datetime.strptime(result['expires_at'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            return {'state': 'NO_DATA', 'cause': 'grant_expiry_unverified'}
        if now.tzinfo is None or expires <= now.astimezone(timezone.utc):
            return {'state': 'REJECTED', 'cause': 'grant_expired'}
        # This increment defines the seam but ships no trusted human-signature
        # verifier. Never let an injected adapter self-promote a REAL label.
        if result['evidence_class'] == 'REAL':
            return {'state': 'NO_DATA', 'cause': 'real_authority_verifier_not_integrated'}
        return {'state': 'VERIFIED', 'proof': result}

    def claim_authorized(self, *, grant_id, run_id, task_sha256, agent_id,
                         host_conditions_sha256, budget_cap=None):
        """Reserve one task and consume one verified grant in a single transaction.

        The host verifier is invoked *inside* BEGIN IMMEDIATE and must verify
        signature, issuer trust, current revocation, exact task/agent/host
        bindings and expiry against authority evidence consistent with this
        journal transaction. LAB ships no such production verifier: absent
        source returns NO_DATA without writing or dispatching anything.
        """
        binding = {'grant_id': grant_id, 'run_id': run_id, 'task_sha256': task_sha256,
                   'agent_id': agent_id, 'host_conditions_sha256': host_conditions_sha256}
        if not self._grant_binding_valid(binding):
            return {'state': 'REJECTED', 'cause': 'authorization_binding_invalid'}
        if not isinstance(self.grant_source, GrantVerificationSource):
            return {'state': 'NO_DATA', 'cause': 'authorization_source_unavailable'}
        try:
            with closing(self._connect()) as db:
                db.execute('BEGIN IMMEDIATE')
                db.execute('CREATE TABLE IF NOT EXISTS authorization_reservations ('
                           'grant_id TEXT PRIMARY KEY, run_id TEXT NOT NULL UNIQUE, task_sha256 TEXT NOT NULL, '
                           'agent_id TEXT NOT NULL, host_conditions_sha256 TEXT NOT NULL, grant_sha256 TEXT NOT NULL, '
                           'issuer_ref TEXT NOT NULL, revocation_generation INTEGER NOT NULL, expires_at TEXT NOT NULL, '
                           'evidence_class TEXT NOT NULL, reservation_ref TEXT NOT NULL UNIQUE)')
                consumed = db.execute('SELECT run_id FROM authorization_reservations WHERE grant_id=?',
                                      (grant_id,)).fetchone()
                if consumed:
                    db.rollback()
                    cause = 'run_already_authorized' if consumed[0] == run_id else 'grant_reused'
                    return {'state': 'REJECTED', 'cause': cause}
                now = self.wall_clock()
                if not isinstance(now, datetime) or now.tzinfo is None:
                    db.rollback()
                    return {'state': 'NO_DATA', 'cause': 'host_clock_unavailable'}
                decision = self._grant_source_decision(self.grant_source, db, binding, now)
                if decision['state'] != 'VERIFIED':
                    db.rollback()
                    return decision
                proof = decision['proof']
                try:
                    reservation = {'schema': 'preceptoros.lab.authorization-reservation/1',
                                   **binding, 'grant_sha256': proof['grant_sha256'],
                                   'issuer_ref': proof['issuer_ref'],
                                   'revocation_generation': proof['revocation_generation'],
                                   'expires_at': proof['expires_at'],
                                   'evidence_class': proof['evidence_class']}
                    ref = hashlib.sha256(encode(reservation)).hexdigest()
                    db.execute('INSERT INTO authorization_reservations VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                               (grant_id, run_id, task_sha256, agent_id, host_conditions_sha256,
                                proof['grant_sha256'], proof['issuer_ref'], proof['revocation_generation'],
                                proof['expires_at'], proof['evidence_class'], ref))
                    previous = self._claim_in_transaction(db, run_id, task_sha256, budget_cap)
                    if previous is not None:
                        db.rollback()
                        return {'state': 'REJECTED', 'cause': 'run_already_completed'}
                    db.commit()
                except Failure as exc:
                    db.rollback()
                    cause = 'run_id_conflict' if exc.category == 'REPLAY' else 'journal_claim_rejected'
                    return {'state': 'REJECTED', 'cause': cause}
                except Exception:
                    db.rollback()
                    return {'state': 'NO_DATA', 'cause': 'journal_reservation_write_failed'}
            return {'state': 'SIMULATED_RESERVED', 'cause': 'synthetic_verifier_only',
                    'reservation_ref': ref, **binding}
        except (sqlite3.Error, OSError, ValueError, TypeError):
            return {'state': 'NO_DATA', 'cause': 'journal_reservation_unavailable'}

    def lookup(self, run_id, task_ref):
        """Read an existing result without reserving a new run before permission."""
        try:
            with closing(self._connect()) as db:
                row = db.execute('SELECT task_ref,receipt FROM claims WHERE run_id=?', (run_id,)).fetchone()
                if row is None:
                    self._require_resolved(db)
                    return None
                if row[0] != task_ref or row[1] is None:
                    raise Failure('REPLAY')
                return self._receipt(row[1], run_id, task_ref)
        except Failure:
            raise
        except (sqlite3.Error, OSError, ValueError, TypeError):
            raise Failure('EVIDENCE') from None

    def finish(self, run_id, task_ref, receipt):
        try:
            if self._receipt(encode(receipt).decode(), run_id, task_ref) != receipt:
                raise Failure('EVIDENCE')
            with closing(self._connect()) as db:
                db.execute('BEGIN IMMEDIATE')
                result = db.execute('UPDATE claims SET receipt=? WHERE run_id=? AND task_ref=? AND receipt IS NULL',
                                    (encode(receipt).decode(), run_id, task_ref))
                if result.rowcount != 1:
                    raise Failure('EVIDENCE')
                if self._budget_enabled(db):
                    reservation = db.execute('SELECT cap,status FROM budget_reservations WHERE run_id=?', (run_id,)).fetchone()
                    if reservation is None or reservation[1] != 'RESERVED':
                        raise Failure('EVIDENCE')
                    cap = reservation[0]
                    if receipt['outcome'] == 'UNKNOWN':
                        db.execute("UPDATE budget_reservations SET status='UNKNOWN' WHERE run_id=?", (run_id,))
                    else:
                        used = receipt['measurement']['tokens'] if receipt['outcome'] == 'KNOWN' else 0
                        if type(used) is not int or not 0 <= used <= cap:
                            raise Failure('EVIDENCE')
                        changed = db.execute('UPDATE durable_budget SET remaining=remaining+? WHERE id=1 AND remaining+?<=initial_limit',
                                             (cap-used, cap-used))
                        if changed.rowcount != 1:
                            raise Failure('EVIDENCE')
                        db.execute("UPDATE budget_reservations SET status='SETTLED' WHERE run_id=?", (run_id,))
                db.commit()
        except Failure:
            raise
        except (sqlite3.Error, OSError, ValueError, TypeError):
            raise Failure('EVIDENCE') from None

    def attests(self, receipt, task_ref, run_id):
        try:
            with closing(self._connect()) as db:
                row = db.execute('SELECT task_ref,receipt FROM claims WHERE run_id=?', (run_id,)).fetchone()
                return (row is not None and row[0] == task_ref
                        and self._receipt(row[1], run_id, task_ref) == receipt)
        except (sqlite3.Error, OSError, ValueError, TypeError, Failure):
            return False


class DurableTokenBudget:
    """Session adapter; actual reservation and settlement are journal transactions."""
    def __init__(self, journal):
        if not isinstance(journal, ExecutionJournal):
            raise Failure('EVIDENCE')
        self.journal = journal
        self.journal.remaining_budget()  # No implicit creation or reset.

    @property
    def remaining(self):
        return self.journal.remaining_budget()

    def reserve(self, cap):
        if type(cap) is not int or cap < 0 or cap > self.remaining:
            raise Failure('BUDGET')
        # Preflight only: claim() makes the actual atomic reservation.

    def settle(self, cap, used):
        # finish() settles atomically with the final witnessed receipt.
        pass
