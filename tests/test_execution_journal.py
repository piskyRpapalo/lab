import os
from pathlib import Path
import sqlite3
import tempfile
import threading
from contextlib import closing
import unittest

from meta_harness.delegation import Failure, Session, TokenBudget, sha
from meta_harness.execution_journal import ExecutionJournal
from tests.test_meta_delegation import STAMP, grant, result, task


class DurableSession(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'owned.sqlite3'
        self.journal = ExecutionJournal.create(self.path)
        self.calls = []

    def worker(self, t, cancelled):
        self.calls.append(1)
        return result(t, cancelled)

    def session(self):
        return Session(grant, TokenBudget(128), journal=ExecutionJournal(self.path))

    def test_completed_receipt_replays_after_restart_without_dispatch(self):
        first = self.session().execute(task(), self.worker, observed_at=STAMP)
        restarted = self.session()
        self.assertEqual(restarted.execute(task(), self.worker, observed_at=STAMP), first)
        self.assertEqual(self.calls, [1])
        self.assertTrue(restarted.attests(first, task()))
        with self.assertRaises(Failure) as error:
            restarted.execute(task(input_sha256='f'*64), self.worker, observed_at=STAMP)
        self.assertEqual(error.exception.category, 'REPLAY')

    def test_crash_after_claim_blocks_same_and_other_tasks(self):
        self.journal.claim(task()['run_id'], sha(task()))
        for request in (task(), task(run_id='other-run')):
            with self.assertRaises(Failure):
                self.session().execute(request, self.worker, observed_at=STAMP)
        self.assertEqual(self.calls, [])

    def test_uncertain_outcome_replays_but_blocks_new_work(self):
        def uncertain(t, cancelled):
            self.calls.append(1)
            raise OSError('private-canary')
        first = self.session().execute(task(), uncertain, observed_at=STAMP)
        self.assertEqual(first['outcome'], 'UNKNOWN')
        self.assertEqual(self.session().execute(task(), uncertain, observed_at=STAMP), first)
        with self.assertRaises(Failure):
            self.session().execute(task(run_id='other-run'), self.worker, observed_at=STAMP)
        self.assertEqual(self.calls, [1])

    def test_lost_ack_after_dispatch_does_not_trigger_another_call(self):
        class LostAck:
            def lookup(self, *args): return self.journal.lookup(*args)
            def claim(self, *args): return self.journal.claim(*args)
            def finish(self, *args): raise OSError('lost acknowledgement')
        wrapper = LostAck(); wrapper.journal = self.journal
        session = Session(grant, TokenBudget(128), journal=wrapper)
        with self.assertRaises(Failure) as error:
            session.execute(task(), self.worker, observed_at=STAMP)
        self.assertEqual(error.exception.category, 'EVIDENCE')
        with self.assertRaises(Failure):
            self.session().execute(task(), self.worker, observed_at=STAMP)
        self.assertEqual(self.calls, [1])

    def test_atomic_claim_and_corruption_fail_closed(self):
        self.journal.claim(task()['run_id'], sha(task()))
        with self.assertRaises(Failure):
            ExecutionJournal(self.path).claim(task()['run_id'], sha(task()))
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('UPDATE claims SET receipt=?', ('{}',))
            db.commit()
        with self.assertRaises(Failure):
            self.session().execute(task(run_id='other-run'), self.worker, observed_at=STAMP)
        self.assertEqual(self.calls, [])

    def test_competing_sessions_never_execute_same_claim_twice(self):
        started, release, results = threading.Event(), threading.Event(), []
        def slow(t, cancelled):
            self.calls.append(1); started.set(); release.wait(2)
            return result(t, cancelled)
        thread = threading.Thread(target=lambda: results.append(self.session().execute(task(), slow, observed_at=STAMP)))
        thread.start()
        try:
            self.assertTrue(started.wait(2))
            with self.assertRaises(Failure): self.session().execute(task(), self.worker, observed_at=STAMP)
        finally:
            release.set(); thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(results), 1)
        self.assertEqual(self.calls, [1])

    def test_existing_file_and_unsafe_permissions_refused(self):
        with self.assertRaises(FileExistsError): ExecutionJournal.create(self.path)
        os.chmod(self.path, 0o644)
        with self.assertRaises(Failure): ExecutionJournal(self.path)

    def test_malformed_replay_from_host_journal_cannot_be_accepted(self):
        class Forged:
            def lookup(self, *args): return {'outcome': 'KNOWN'}
            def attests(self, *args): return True
        session = Session(grant, TokenBudget(128), journal=Forged())
        with self.assertRaises(Failure) as error:
            session.execute(task(), self.worker, observed_at=STAMP)
        self.assertEqual(error.exception.category, 'EVIDENCE')
        self.assertEqual(self.calls, [])

    def test_witness_refuses_a_corrupted_durable_record_even_in_same_session(self):
        session = self.session()
        receipt = session.execute(task(), self.worker, observed_at=STAMP)
        self.assertTrue(session.attests(receipt, task()))
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('UPDATE claims SET receipt=?', ('{}',)); db.commit()
        self.assertFalse(session.attests(receipt, task()))

    def test_denied_and_insufficient_budget_do_not_persist_claims(self):
        for authority, budget in ((lambda _: None, 128), (grant, 0)):
            session = Session(authority, TokenBudget(budget), journal=self.journal)
            receipt = session.execute(task(), self.worker, observed_at=STAMP)
            self.assertEqual(receipt['outcome'], 'NOT_STARTED')
            with closing(sqlite3.connect(self.path)) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 0)
        receipt = self.session().execute(task(run_id='next-run'), self.worker, observed_at=STAMP)
        self.assertEqual(receipt['outcome'], 'KNOWN')
        self.assertEqual(self.calls, [1])

    def test_interruption_before_grant_or_admission_leaves_no_persistent_claim(self):
        def interrupt(*_): raise KeyboardInterrupt()
        for session in (Session(interrupt, TokenBudget(128), journal=self.journal),
                        Session(grant, TokenBudget(128), journal=self.journal, admission=interrupt)):
            with self.assertRaises(KeyboardInterrupt):
                session.execute(task(), self.worker, observed_at=STAMP)
            with closing(sqlite3.connect(self.path)) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 0)
        receipt = self.session().execute(task(run_id='after-restart'), self.worker, observed_at=STAMP)
        self.assertEqual(receipt['outcome'], 'KNOWN')
        self.assertEqual(self.calls, [1])

    def test_repeated_rejections_do_not_grow_journal(self):
        for index in range(100):
            denied = Session(lambda _: None, TokenBudget(128), journal=self.journal)
            receipt = denied.execute(task(run_id='denied-%d' % index), self.worker, observed_at=STAMP)
            self.assertEqual(receipt['failure_class'], 'PERMISSION')
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 0)
        self.assertEqual(self.session().execute(task(), self.worker, observed_at=STAMP)['outcome'], 'KNOWN')

    def test_cancellation_before_dispatch_does_not_strand_other_tasks(self):
        session = Session(grant, TokenBudget(128), journal=self.journal)
        receipt = session.execute(task(), self.worker, observed_at=STAMP, cancelled=lambda: True)
        self.assertEqual((receipt['phase'], receipt['outcome']), ('cancelled', 'NOT_STARTED'))
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 0)
        self.assertEqual(self.session().execute(task(run_id='after-cancel'), self.worker, observed_at=STAMP)['outcome'], 'KNOWN')
