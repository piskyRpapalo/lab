"""Explicit host-owned SQLite claims for the existing Session; no dispatch or retry.

Create only a new private file. Unknown claims are never automatically cleared.
The host owns the directory, authorization, budget and reconciliation policy.
"""
import json
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import stat

from .delegation import Failure, encode, verify


class ExecutionJournal:
    def __init__(self, path):
        self.path = Path(path).absolute()
        self._check()

    @classmethod
    def create(cls, path):
        path = Path(path).absolute()
        cls._parent(path)
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        journal = cls(path)
        with closing(journal._connect()) as db:
            db.execute('CREATE TABLE claims (run_id TEXT PRIMARY KEY, task_ref TEXT NOT NULL, receipt TEXT)')
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
        """Atomically claim, or replay a known result; uncertain work blocks new work."""
        try:
            with closing(self._connect()) as db:
                db.execute('BEGIN IMMEDIATE')
                row = db.execute('SELECT task_ref,receipt FROM claims WHERE run_id=?', (run_id,)).fetchone()
                if row:
                    if row[0] != task_ref or row[1] is None:
                        raise Failure('REPLAY')
                    return self._receipt(row[1], run_id, task_ref)
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
                db.commit()
                return None
        except Failure:
            raise
        except (sqlite3.Error, OSError, ValueError, TypeError):
            raise Failure('EVIDENCE') from None

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
