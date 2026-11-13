"""CEREBRO-CONTEXT-01: durable APP draft reconciliation, never promotion.

The host injects the existing memory module or proponer_borrador callable,
explicit consent, and the real Session witness. No authority is inferred from
serialized receipts. Only a fixed receipt-hash summary reaches the APP helper.

Select exactly one existing DB path or idle sqlite connection. A connection is
used only to select its main file; operations use a fresh owned connection so
caller transaction settings/handlers are untouched. DB and its direct parent
must be owner-private, with no symlink path components or linked DB sidecars.
All cooperating writers must use this adapter's permanent .meta-draft.lock.
Uncoordinated APP writers are outside this idempotency guarantee.

The timeout (0 < seconds <= 5) bounds lock acquisition and SQLite waits/work;
cancel is checked before insertion and by SQLite's progress handler. Trusted
Python proposer/cancel callbacks must themselves return promptly: synchronous
Python cannot safely be preempted. On timeout/cancel after a possible commit,
NO_DATA is returned; a later authorized retry reconciles without reinsertion.
No new tables, migrations, memory engine, promotion, or automatic retries here.
"""
from dataclasses import dataclass, field
import copy
import fcntl
import math
import os
from pathlib import Path
import sqlite3
import stat
import time

from .delegation import Session, sha, validate_task, verify

SCHEMA = "preceptoros.meta-memory-draft/1"
SUMMARY = "Execution receipt {receipt_ref}. Draft for review; no authority or correctness inferred."
STATES = {"pendiente": "PENDING", "descartado": "DISCARDED", "promovido": "PROMOTED"}
CAUSES = frozenset({"adapter_unavailable", "consent_required", "invalid_timeout",
    "invalid_cancel", "cancelled", "deadline_exceeded", "receipt_not_witnessed",
    "invalid_memory_api", "database_selection_required", "invalid_connection",
    "inherited_transaction", "unsafe_database", "unsafe_lock", "duplicate_origin",
    "draft_conflict", "proposer_contract_invalid", "draft_not_recorded"})


@dataclass(frozen=True)
class DraftResult:
    """Only export() is public evidence; draft_ref is an internal opaque handle."""
    state: str
    cause: str
    receipt_ref: str | None = None
    draft_ref: str | None = field(default=None, repr=False)

    def export(self):
        return dict(schema=SCHEMA, state=self.state, cause=self.cause,
                    receipt_ref=self.receipt_ref)


class _Stop(Exception):
    def __init__(self, cause):
        self.cause = cause if type(cause) is str and cause in CAUSES else "adapter_unavailable"


def _require(ok, cause):
    if not ok:
        raise _Stop(cause)


def _path(raw):
    p = Path(raw)
    _require(".." not in p.parts, "unsafe_database")
    p = p.absolute()
    for item in (p, *p.parents):
        _require(not stat.S_ISLNK(item.lstat().st_mode), "unsafe_database")
    info, parent = p.stat(), p.parent.stat()
    _require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
             and info.st_nlink == 1 and not info.st_mode & 0o077
             and parent.st_uid == os.geteuid() and not parent.st_mode & 0o077,
             "unsafe_database")
    for suffix in ("-wal", "-shm", "-journal"):
        side = Path(str(p) + suffix)
        if os.path.lexists(side):
            s = side.lstat()
            _require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1
                     and s.st_uid == os.geteuid() and not s.st_mode & 0o077,
                     "unsafe_database")
    return p, (info.st_dev, info.st_ino)


def _lookup(c, origin, text):
    rows = c.execute("SELECT id, texto, estado FROM borradores WHERE origen = ? LIMIT 2",
                     (origin,)).fetchall()
    _require(len(rows) <= 1, "duplicate_origin")
    if not rows:
        return None
    ident, actual, state = rows[0]
    _require(type(ident) is int and ident > 0 and type(actual) is str
             and actual == text and type(state) is str and state in STATES,
             "draft_conflict")
    return ident, state


def _present(row, ref):
    return DraftResult(STATES[row[1]], "exact_draft_present", ref,
                       sha({"schema": SCHEMA, "receipt_ref": ref, "row": row[0]}))


def _write(c, proposer, origin, text, ref, guard, progress):
    row = _lookup(c, origin, text)
    if row:
        return _present(row, ref)
    guard()
    ack, failed = None, False
    try:
        ack = proposer(c, text, origen=origin)
    except Exception:
        failed = True  # May have committed and then lost its acknowledgement.
    # Never commit work left pending by a broken/incomplete helper.
    c.set_progress_handler(None, 0)
    pending = c.in_transaction
    if pending:
        c.rollback()
    guard()
    c.set_progress_handler(progress, 100)
    row = _lookup(c, origin, text)
    if row:
        _require(row[1] == "pendiente", "draft_conflict")
        _require(failed or (not pending and type(ack) is int and ack == row[0]),
                 "proposer_contract_invalid")
        return _present(row, ref)
    raise _Stop("draft_not_recorded")


def propose_draft(receipt, task, *, session, memory_api, db_path=None,
                  connection=None, consent=False, timeout_s=1.0, cancelled=None):
    """Call only proponer_borrador, or reconcile its exact durable origin.

    Returns DraftResult: PENDING/DISCARDED/PROMOTED describe an existing row;
    PROMOTED never means this adapter performed promotion. NO_DATA carries a
    fixed cause. Consent defaults false and must be the literal runtime True.
    No draft ID or DB path appears in export(); draft_ref is a SHA256 handle.
    A pending caller transaction is refused without rollback or modification.
    The host owns consent, Session lifetime and the choice of trusted APP code.
    """
    ref, fd, c = None, None, None
    try:
        _require(consent is True, "consent_required")
        _require(type(timeout_s) in (int, float) and math.isfinite(timeout_s)
                 and 0 < timeout_s <= 5, "invalid_timeout")
        _require(cancelled is None or callable(cancelled), "invalid_cancel")
        deadline = time.monotonic() + timeout_s

        def guard():
            if cancelled is not None:
                flag = cancelled()
                _require(type(flag) is bool, "invalid_cancel")
                _require(not flag, "cancelled")
            _require(time.monotonic() < deadline, "deadline_exceeded")

        guard()
        task, receipt = copy.deepcopy(task), copy.deepcopy(receipt)
        validate_task(task)
        _require(type(session) is Session and verify(receipt)
                 and receipt["task_sha256"] == sha(task)
                 and receipt["run_id"] == task["run_id"]
                 and Session.attests(session, receipt, task) is True,
                 "receipt_not_witnessed")
        ref = receipt["receipt_ref"]
        proposer = memory_api if callable(memory_api) else getattr(memory_api, "proponer_borrador", None)
        _require(callable(proposer), "invalid_memory_api")
        _require((db_path is None) != (connection is None), "database_selection_required")
        if connection is not None:
            _require(type(connection) is sqlite3.Connection, "invalid_connection")
            _require(not connection.in_transaction, "inherited_transaction")
            dbs = connection.execute("PRAGMA database_list").fetchall()
            _require(len(dbs) == 1 and dbs[0][1] == "main" and dbs[0][2], "unsafe_database")
            db_path = dbs[0][2]
        path, identity = _path(db_path)
        lock = str(path) + ".meta-draft.lock"
        fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        info = os.fstat(fd)
        _require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                 and info.st_nlink == 1 and not info.st_mode & 0o077,
                 "unsafe_lock")
        while True:
            guard()
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(min(0.01, max(0, deadline - time.monotonic())))
        _require(_path(path)[1] == identity, "unsafe_database")
        now_lock = os.stat(lock, follow_symlinks=False)
        _require((now_lock.st_dev, now_lock.st_ino) == (info.st_dev, info.st_ino), "unsafe_lock")
        guard()
        c = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True,
                            timeout=max(0.001, deadline - time.monotonic()))
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA synchronous=FULL")

        def progress():
            try:
                guard()
                return 0
            except Exception:
                return 1

        c.set_progress_handler(progress, 100)
        text = SUMMARY.format(receipt_ref=ref)
        return _write(c, proposer, "meta-receipt:" + ref, text, ref, guard, progress)
    except _Stop as exc:
        return DraftResult("NO_DATA", exc.cause, ref)
    except Exception:
        return DraftResult("NO_DATA", "adapter_unavailable", ref)
    finally:
        if c is not None:
            try:
                c.set_progress_handler(None, 0)
                if c.in_transaction:
                    c.rollback()
            except Exception:
                pass
            try:
                c.close()
            except Exception:
                pass
        if fd is not None:
            try:
                os.close(fd)  # Release flock; keep the inode for other writers.
            except OSError:
                pass
