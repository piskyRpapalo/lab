import sqlite3
import subprocess
import sys
import tempfile
import threading
from contextlib import closing
from pathlib import Path
import unittest
from unittest.mock import patch

from meta_harness.delegation import Failure, Session, TokenBudget, sha
from meta_harness.execution_journal import DurableTokenBudget, ExecutionJournal
from tests.test_meta_delegation import STAMP, grant, result, task


class DurableBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'journal.sqlite3'
        self.journal = ExecutionJournal.create(self.path)
        self.journal.initialize_budget(128)
        self.calls = []

    def worker(self, t, cancelled):
        self.calls.append(1)
        return dict(result(t, cancelled), tokens=3)

    def session(self, authority=grant):
        j = ExecutionJournal(self.path)
        return Session(authority, DurableTokenBudget(j), journal=j)

    def test_known_result_settles_and_replay_after_restart_costs_nothing(self):
        first = self.session().execute(task(), self.worker, observed_at=STAMP)
        self.assertEqual(first['outcome'], 'KNOWN')
        self.assertEqual(self.session().budget.remaining, 125)
        self.assertEqual(self.session().execute(task(), self.worker, observed_at=STAMP), first)
        self.assertEqual(self.session().budget.remaining, 125)
        self.assertEqual(self.calls, [1])

    def test_denied_budget_and_interruption_before_claim_do_not_reserve(self):
        denied = self.session(lambda _:None)
        self.assertEqual(denied.execute(task(), self.worker, observed_at=STAMP)['failure_class'], 'PERMISSION')
        def interrupt(_): raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.session(interrupt).execute(task(), self.worker, observed_at=STAMP)
        self.assertEqual(self.session().budget.remaining, 128)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT count(*) FROM budget_reservations').fetchone()[0], 0)

    def test_unknown_completion_keeps_entire_reservation_across_restart(self):
        def uncertain(t, cancelled):
            self.calls.append(1); raise OSError('synthetic')
        first = self.session().execute(task(), uncertain, observed_at=STAMP)
        self.assertEqual(first['outcome'], 'UNKNOWN')
        self.assertEqual(self.session().budget.remaining, 64)
        self.assertEqual(self.session().execute(task(), uncertain, observed_at=STAMP), first)
        with self.assertRaises(Failure):
            self.session().execute(task(run_id='other'), self.worker, observed_at=STAMP)
        self.assertEqual(self.session().budget.remaining, 64)
        self.assertEqual(self.calls, [1])

    def test_crash_after_atomic_claim_preserves_full_reservation(self):
        self.journal.claim(task()['run_id'], sha(task()), budget_cap=64)
        self.assertEqual(self.session().budget.remaining, 64)
        with self.assertRaises(Failure): self.session().execute(task(), self.worker, observed_at=STAMP)
        self.assertEqual(self.calls, [])

    def test_real_child_exit_after_claim_cannot_restore_budget_or_repeat(self):
        code = ('import os,sys; from meta_harness.execution_journal import ExecutionJournal; '
                'from meta_harness.delegation import sha; from tests.test_meta_delegation import task; '
                'ExecutionJournal(sys.argv[1]).claim(task()["run_id"],sha(task()),budget_cap=64); os._exit(17)')
        child = subprocess.run([sys.executable, '-B', '-c', code, str(self.path)], timeout=10)
        self.assertEqual(child.returncode, 17)
        self.assertEqual(self.session().budget.remaining, 64)
        with self.assertRaises(Failure): self.session().execute(task(), self.worker, observed_at=STAMP)
        self.assertEqual(self.calls, [])

    def test_known_cancellation_after_claim_atomically_refunds(self):
        signals = iter([False, False, False, True])
        receipt = self.session().execute(task(), self.worker, observed_at=STAMP,
                                         cancelled=lambda: next(signals, True))
        self.assertEqual((receipt['phase'], receipt['outcome']), ('cancelled', 'NOT_STARTED'))
        self.assertEqual(self.session().budget.remaining, 128)
        self.assertEqual(self.calls, [])

    def test_two_sessions_cannot_double_reserve_same_run(self):
        started, release, output = threading.Event(), threading.Event(), []
        def slow(t, cancelled):
            self.calls.append(1); started.set(); release.wait(2)
            return dict(result(t, cancelled), tokens=3)
        thread = threading.Thread(target=lambda: output.append(self.session().execute(task(), slow, observed_at=STAMP)))
        thread.start()
        try:
            self.assertTrue(started.wait(2))
            self.assertEqual(self.session().budget.remaining, 64)
            with self.assertRaises(Failure): self.session().execute(task(), self.worker, observed_at=STAMP)
            with self.assertRaises(Failure): self.session().execute(task(run_id='other'), self.worker, observed_at=STAMP)
            self.assertEqual(self.session().budget.remaining, 64)
        finally:
            release.set(); thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(output), 1)
        self.assertEqual(self.session().budget.remaining, 125)
        self.assertEqual(self.calls, [1])

    def test_lost_ack_after_commit_replays_without_double_charge(self):
        session = self.session()
        finish = session.journal.finish
        def lost(*args):
            finish(*args)
            raise OSError('synthetic lost confirmation')
        with patch.object(session.journal, 'finish', side_effect=lost):
            with self.assertRaises(Failure): session.execute(task(), self.worker, observed_at=STAMP)
        self.assertEqual(self.session().budget.remaining, 125)
        replay = self.session().execute(task(), self.worker, observed_at=STAMP)
        self.assertEqual(replay['outcome'], 'KNOWN')
        self.assertEqual(self.session().budget.remaining, 125)
        self.assertEqual(self.calls, [1])

    def test_budget_cannot_be_reset_or_detached_from_journal(self):
        with self.assertRaises(Failure): self.journal.initialize_budget(4096)
        other = ExecutionJournal(self.path)
        with self.assertRaises(Failure): Session(grant, DurableTokenBudget(self.journal), journal=other)
        session = Session(grant, TokenBudget(128), journal=self.journal)
        receipt = session.execute(task(), self.worker, observed_at=STAMP)
        self.assertEqual((receipt['outcome'], receipt['failure_class']), ('NOT_STARTED', 'EVIDENCE'))
        self.assertEqual(self.session().budget.remaining, 128)
        self.assertEqual(self.calls, [])

    def test_insufficient_budget_does_not_create_a_claim(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('UPDATE durable_budget SET remaining=32'); db.commit()
        receipt = self.session().execute(task(), self.worker, observed_at=STAMP)
        self.assertEqual((receipt['outcome'], receipt['failure_class']), ('NOT_STARTED', 'BUDGET'))
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 0)
        self.assertEqual(self.session().budget.remaining, 32)

    def test_invalid_budget_and_nonempty_journal_refuse_initialization(self):
        other = ExecutionJournal.create(Path(self.temp.name)/'other.sqlite3')
        for value in (-1, 4097, True):
            with self.assertRaises(Failure): other.initialize_budget(value)
        other.claim('old-run', 'f'*64)
        with self.assertRaises(Failure): other.initialize_budget(128)
