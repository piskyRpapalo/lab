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

    def claim(self, run_id, task_ref):
        """Atomically claim, or replay a known result; uncertain work blocks new work."""
        try:
            with closing(self._connect()) as db:
                db.execute('BEGIN IMMEDIATE')
                row = db.execute('SELECT task_ref,receipt FROM claims WHERE run_id=?', (run_id,)).fetchone()
                if row:
                    if row[0] != task_ref or row[1] is None:
                        raise Failure('REPLAY')
                    return self._receipt(row[1], run_id, task_ref)
                rows = db.execute('SELECT run_id,task_ref,receipt FROM claims LIMIT 4097').fetchall()
                if len(rows) > 4096:
                    raise Failure('EVIDENCE')
                for old_id, old_ref, raw in rows:
                    prior = self._receipt(raw, old_id, old_ref)
                    if prior is None or prior['outcome'] == 'UNKNOWN':
                        raise Failure('EVIDENCE')
                db.execute('INSERT INTO claims(run_id,task_ref,receipt) VALUES(?,?,NULL)', (run_id, task_ref))
                db.commit()
                return None
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
