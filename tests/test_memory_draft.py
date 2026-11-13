"""Temporary DBs only. META_APP_ROOT selects real APP code when available."""
from contextlib import contextmanager
import fcntl
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest

from meta_harness import memory_draft as m
from meta_harness.delegation import Session, TokenBudget, sha, seal


@contextmanager
def opened(path):
    c = sqlite3.connect(path)
    try:
        with c:
            yield c
    finally:
        c.close()


def witnessed():
    task = dict(schema="preceptoros.meta-task/1", task_id="private-canary",
                run_id="draft-run", specialist="fixture", source="private-canary",
                model_version="a" * 64, input_sha256="b" * 64, max_tokens=1,
                timeout_ms=1000, depth=0, privacy="LOCAL_ONLY", transport="local_function")
    def grant(t):
        return dict(approved=True, task_sha256=sha(t), approval_ref="c" * 64,
                    expires_ns=10**30, max_tokens=1, max_ms=1000, max_depth=0, local_only=True)
    session = Session(grant, TokenBudget(1))
    result = dict(model_version="a" * 64, tokens=1, output_sha256="d" * 64,
                  grade="PASS", basis="public_deterministic_reference")
    receipt = session.execute(task, lambda *_: result, observed_at="2026-11-12T00:00:00Z")
    return session, task, receipt


def fake(c, texto, origen):
    """Portable storage double, not a production memory implementation."""
    cur = c.execute("INSERT INTO borradores(texto, origen) VALUES (?, ?)", (texto, origen))
    c.commit()
    return cur.lastrowid


def crash_child(path, session, task, receipt, after_commit):
    def crash(c, texto, origen):
        c.execute("INSERT INTO borradores(texto, origen) VALUES (?, ?)", (texto, origen))
        if after_commit:
            c.commit()
        os._exit(41)
    m.propose_draft(receipt, task, session=session, memory_api=crash,
                    db_path=path, consent=True)


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "memory.db"
        with opened(self.db) as c:
            c.execute("CREATE TABLE borradores (id INTEGER PRIMARY KEY, texto TEXT, "
                      "origen TEXT, estado TEXT DEFAULT 'pendiente')")
        self.db.chmod(0o600)
        self.session, self.task, self.receipt = witnessed()
        self.origin = "meta-receipt:" + self.receipt["receipt_ref"]
        self.text = m.SUMMARY.format(receipt_ref=self.receipt["receipt_ref"])

    def call(self, **options):
        args = dict(session=self.session, memory_api=fake, db_path=self.db, consent=True)
        args.update(options)
        return m.propose_draft(self.receipt, self.task, **args)

    def assertCause(self, cause, **options):
        self.assertEqual(self.call(**options).cause, cause)

    def rows(self):
        with opened(self.db) as c:
            return c.execute("SELECT id, texto, origen, estado FROM borradores").fetchall()

    def insert(self, text=None, state="pendiente", ident=None):
        with opened(self.db) as c:
            c.execute("INSERT INTO borradores(id, texto, origen, estado) VALUES (?,?,?,?)",
                      (ident, self.text if text is None else text, self.origin, state))

    def test_durable_reopen(self):
        a = self.call()
        self.assertEqual(a.export(), dict(schema=m.SCHEMA, state="PENDING",
                         cause="exact_draft_present", receipt_ref=self.receipt["receipt_ref"]))
        def must_not_insert(*_args, **_kw):
            self.fail("reopen reconciliation must not call proposer")
        b = self.call(memory_api=must_not_insert)
        self.assertEqual((a.export(), a.draft_ref), (b.export(), b.draft_ref))
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(self.rows()[0][1:3], (self.text, self.origin))

    def test_consent(self):
        for consent in (False, None, 1, "true", {"approved": True}):
            self.assertCause("consent_required", consent=consent)
        r = m.propose_draft(self.receipt, self.task, session=self.session,
                            memory_api=fake, db_path=self.db)
        self.assertEqual(r.cause, "consent_required")
        self.assertFalse(Path(str(self.db) + ".meta-draft.lock").exists())
        self.assertFalse(self.rows())

    def test_witness(self):
        for witness in (None, True, SimpleNamespace(attests=lambda *_: True),
                        Session(lambda *_: None, TokenBudget(1))):
            self.assertCause("receipt_not_witnessed", session=witness)
        self.session.attests = lambda *_: False
        self.assertEqual(self.call().state, "PENDING")  # unbound real Session method

    def test_forged_binding(self):
        self.receipt["measurement"]["output_sha256"] = "e" * 64
        self.receipt.pop("receipt_ref")
        self.receipt = seal(self.receipt)
        self.assertCause("receipt_not_witnessed")
        self.session, self.task, self.receipt = witnessed()
        self.task["input_sha256"] = "f" * 64
        self.assertCause("receipt_not_witnessed")

    def test_integrity(self):
        self.receipt["receipt_ref"] = "0" * 64
        self.assertCause("receipt_not_witnessed")
        self.assertFalse(self.rows())


    def test_exact_bounded_query(self):
        queries = []
        def traced(c, text, origen):
            c.set_trace_callback(queries.append)
            return fake(c, text, origen)
        with opened(self.db) as c:
            c.execute("INSERT INTO borradores(texto, origen) VALUES ('private-canary', 'other')")
        self.assertEqual(self.call(memory_api=traced).state, "PENDING")
        reads = [q for q in queries if q.startswith("SELECT")]
        self.assertTrue(reads)
        self.assertTrue(all("WHERE origen = 'meta-receipt:" in q and q.endswith("LIMIT 2") for q in reads))
        self.assertEqual(len(self.rows()), 2)

    def test_terminal_rows(self):
        for state, expected in (("descartado", "DISCARDED"), ("promovido", "PROMOTED")):
            with opened(self.db) as c:
                c.execute("DELETE FROM borradores")
            self.insert(state=state)
            before = self.rows()
            def never(*_a, **_kw):
                self.fail("terminal row cannot be resurrected")
            self.assertEqual(self.call(memory_api=never).state, expected)
            self.assertEqual(self.rows(), before)

    def test_duplicate_and_conflict(self):
        self.insert()
        self.insert()
        self.assertCause("duplicate_origin")
        with opened(self.db) as c:
            c.execute("DELETE FROM borradores")
        self.insert(text="private-canary")
        self.assertCause("draft_conflict")
        self.assertEqual(len(self.rows()), 1)


    def test_rollback(self):
        def fail(c, text, origen):
            c.execute("INSERT INTO borradores(texto, origen) VALUES (?,?)", (text, origen))
            raise RuntimeError("private-canary")
        self.assertCause("draft_not_recorded", memory_api=fail)
        self.assertFalse(self.rows())
        self.assertEqual(self.call().state, "PENDING")

    def test_lost_ack(self):
        def fail(c, text, origen):
            fake(c, text, origen)
            raise RuntimeError("private-canary")
        first = self.call(memory_api=fail)
        self.assertEqual(first.state, "PENDING")
        self.assertEqual(self.call().draft_ref, first.draft_ref)
        self.assertEqual(len(self.rows()), 1)

    def test_uncommitted_return(self):
        def incomplete(c, text, origen):
            return c.execute("INSERT INTO borradores(texto, origen) VALUES (?,?)", (text, origen)).lastrowid
        self.assertCause("draft_not_recorded", memory_api=incomplete)
        self.assertFalse(self.rows())

    def test_wrong_ack(self):
        def wrong(c, text, origen):
            return fake(c, text, origen) + 1
        self.assertCause("proposer_contract_invalid", memory_api=wrong)
        self.assertEqual(self.call().state, "PENDING")
        self.assertEqual(len(self.rows()), 1)

    def test_inherited_transaction(self):
        c = sqlite3.connect(self.db)
        try:
            c.execute("INSERT INTO borradores(texto, origen) VALUES ('uncommitted', 'other')")
            self.assertCause("inherited_transaction", db_path=None, connection=c)
            self.assertTrue(c.in_transaction)
            self.assertFalse(self.rows())
        finally:
            c.rollback()
            c.close()

    def test_connection_selection(self):
        c = sqlite3.connect(self.db)
        try:
            c.execute("PRAGMA busy_timeout=1234")
            self.assertEqual(self.call(db_path=None, connection=c).state, "PENDING")
            self.assertFalse(c.in_transaction)
            self.assertEqual(c.execute("PRAGMA busy_timeout").fetchone()[0], 1234)
        finally:
            c.close()

    def test_database_selection(self):
        c = sqlite3.connect(":memory:")
        try:
            self.assertCause("unsafe_database", db_path=None, connection=c)
            self.assertCause("database_selection_required", connection=c)
            self.assertCause("database_selection_required", db_path=None)
        finally:
            c.close()

    def test_symlinks(self):
        for kind in ("database", "parent", "lock", "wal"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as d:
                target = Path(d) / "alias"
                if kind == "database":
                    target.symlink_to(self.db)
                    r = self.call(db_path=target)
                elif kind == "parent":
                    target.symlink_to(self.db.parent, target_is_directory=True)
                    r = self.call(db_path=target / self.db.name)
                else:
                    side = Path(str(self.db) + (".meta-draft.lock" if kind == "lock" else "-wal"))
                    side.symlink_to(self.db)
                    try:
                        r = self.call()
                    finally:
                        side.unlink()
                self.assertEqual(r.state, "NO_DATA")
        self.assertFalse(self.rows())

    def test_private_database(self):
        self.db.chmod(0o644)
        self.assertCause("unsafe_database")
        self.db.chmod(0o600)
        link = self.db.with_name("hardlink")
        os.link(self.db, link)
        self.assertCause("unsafe_database")

    def test_cancel(self):
        self.assertCause("cancelled", cancelled=lambda: True)
        fd = os.open(str(self.db) + ".meta-draft.lock", os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            n = [0]
            def cancel():
                n[0] += 1
                return n[0] >= 3
            self.assertCause("cancelled", cancelled=cancel)
        finally:
            os.close(fd)
        self.assertFalse(self.rows())

    def test_lock_timeout_is_bounded(self):
        fd = os.open(str(self.db) + ".meta-draft.lock", os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            start = time.monotonic()
            self.assertCause("deadline_exceeded", timeout_s=0.04)
            self.assertLess(time.monotonic() - start, 1)
        finally:
            os.close(fd)

    def test_cancel_after_commit(self):
        cancel = threading.Event()
        def committed(c, text, origen):
            ident = fake(c, text, origen)
            cancel.set()
            return ident
        self.assertCause("cancelled", memory_api=committed, cancelled=cancel.is_set)
        self.assertEqual(self.call().state, "PENDING")
        self.assertEqual(len(self.rows()), 1)

    def test_two_concurrent_calls_insert_once(self):
        barrier, calls, results = threading.Barrier(2), [], []
        def slow(c, text, origen):
            calls.append(True)
            time.sleep(0.03)
            return fake(c, text, origen)
        def worker():
            barrier.wait()
            results.append(self.call(memory_api=slow))
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(2)
            self.assertFalse(t.is_alive())
        self.assertEqual([r.state for r in results], ["PENDING", "PENDING"])
        self.assertEqual(results[0].draft_ref, results[1].draft_ref)
        self.assertEqual((len(calls), len(self.rows())), (1, 1))

    def test_process_crash_before_and_after_commit(self):
        for after in (False, True):
            with self.subTest(after=after):
                with opened(self.db) as c:
                    c.execute("DELETE FROM borradores")
                p = multiprocessing.get_context("fork").Process(target=crash_child,
                    args=(self.db, self.session, self.task, self.receipt, after))
                p.start()
                p.join(3)
                if p.is_alive():
                    p.kill()
                    p.join()
                self.assertEqual(p.exitcode, 41)
                self.assertEqual(len(self.rows()), int(after))
                self.assertEqual(self.call().state, "PENDING")
                self.assertEqual(len(self.rows()), 1)

    def test_private_canary(self):
        def explode(*_a, **_kw):
            raise RuntimeError("private-canary /private/database")
        for r in (self.call(memory_api=explode), self.call()):
            raw = json.dumps(r.export())
            self.assertNotIn("private", raw)
            self.assertNotIn(str(self.db), raw)
            self.assertNotIn("draft_ref", raw)
            self.assertNotIn("draft_id", raw)
            self.assertLess(len(raw.encode()), 512)
        self.assertNotIn("private-canary", self.rows()[0][1])

    def test_callback_contract(self):
        for value in (True, 0, -1, 6, float("inf"), float("nan"), "1"):
            self.assertCause("invalid_timeout", timeout_s=value)
        self.assertCause("invalid_cancel", cancelled=True)
        self.assertCause("invalid_cancel", cancelled=lambda: "yes")

APP_ROOT = Path(os.environ.get("META_APP_ROOT", Path.home() / "PreceptorOS"))


@unittest.skipUnless((APP_ROOT / "memory.py").is_file(), "NO_DATA: APP source unavailable")
class RealAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("draft_real_app", APP_ROOT / "memory.py")
        cls.app = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(APP_ROOT))
        try:
            spec.loader.exec_module(cls.app)
        finally:
            sys.path.pop(0)

    def test_real_app_durable_draft(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "memory.db"
            self.app.crear(str(db))
            db.chmod(0o600)
            session, task, receipt = witnessed()
            def lost(c, text, origen):
                self.app.proponer_borrador(c, text, origen=origen)
                raise RuntimeError("private-canary")
            a = m.propose_draft(receipt, task, session=session, memory_api=lost, db_path=db, consent=True)
            self.assertEqual(a.state, "PENDING")
            b = m.propose_draft(receipt, task, session=session, memory_api=self.app, db_path=db, consent=True)
            self.assertEqual(a.draft_ref, b.draft_ref)
            with opened(db) as c:
                self.assertEqual(c.execute("SELECT count(*) FROM borradores").fetchone()[0], 1)
                self.assertEqual(c.execute("SELECT count(*) FROM engrams").fetchone()[0], 0)
                c.execute("UPDATE borradores SET estado='descartado'")
            r = m.propose_draft(receipt, task, session=session, memory_api=self.app.proponer_borrador,
                                db_path=db, consent=True)
            self.assertEqual(r.state, "DISCARDED")


class PieceLimit(unittest.TestCase):
    def test_owned_files_under_house_ceiling(self):
        for p in (Path(m.__file__), Path(__file__)):
            self.assertLess(p.stat().st_size, 16384)


if __name__ == "__main__":
    unittest.main()
