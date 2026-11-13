"""Synthetic authority/fence witnesses: no human signature is forged or inferred."""
import json
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path
import unittest

from meta_harness.delegation import Failure, Session, sha
from meta_harness.execution_journal import DurableTokenBudget, ExecutionJournal
from tests.test_meta_delegation import STAMP, grant, result, task


class HumanUncertainty(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'owned.sqlite3'
        initial = ExecutionJournal.create(self.path); initial.initialize_budget(128)
        self.accepted = set()
        self.journal = ExecutionJournal(self.path, resolution_witness=lambda r: r['resolution_ref'] in self.accepted)
        self.calls = []
        def uncertain(t, cancelled):
            self.calls.append('uncertain'); raise OSError('synthetic')
        self.unknown = self.session().execute(task(), uncertain, observed_at=STAMP)
        self.assertEqual(self.unknown['outcome'], 'UNKNOWN')

    def session(self, *, witness=True):
        callback = (lambda r: r['resolution_ref'] in self.accepted) if witness else None
        journal = ExecutionJournal(self.path, resolution_witness=callback)
        return Session(grant, DurableTokenBudget(journal), journal=journal)

    def proposal(self):
        return self.journal.prepare_unknown_ack(task()['run_id'], sha(task()),
            evidence_ref='e'*64, authority_ref='f'*64, observed_at=STAMP)

    def acknowledge(self, proposal, *, human=lambda _:True, fence=lambda _:True, expected=None):
        return self.journal.acknowledge_unknown(task()['run_id'], sha(task()),
            evidence_ref='e'*64, authority_ref='f'*64, observed_at=STAMP,
            expected_ref=expected or proposal['resolution_ref'], human_authorize=human, quiescence=fence)

    def worker(self, request, cancelled):
        self.calls.append('next'); return result(request, cancelled)

    def test_read_only_proposal_cannot_unblock_or_release(self):
        proposal = self.proposal()
        self.assertFalse(proposal['reservation_release'])
        self.assertTrue(proposal['no_retry'])
        self.assertEqual(self.session().budget.remaining, 64)
        with self.assertRaises(Failure): self.session().execute(task(run_id='next'), self.worker, observed_at=STAMP)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM resolution_events').fetchone()[0], 0)

    def test_human_and_host_fence_must_both_attest_exact_proposal(self):
        p = self.proposal(); self.accepted.add(p['resolution_ref'])
        for kwargs in ({'human':lambda _:False}, {'fence':lambda _:False}, {'expected':'0'*64}):
            with self.assertRaises(Failure): self.acknowledge(p, **kwargs)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM resolution_events').fetchone()[0], 0)
        self.assertEqual(self.session().budget.remaining, 64)

    def test_approved_acknowledgement_is_idempotent_and_never_retries_or_refunds(self):
        p = self.proposal(); self.accepted.add(p['resolution_ref'])
        self.assertEqual(self.acknowledge(p), p)
        self.assertEqual(self.acknowledge(p), p)
        self.assertEqual(self.session().execute(task(), self.worker, observed_at=STAMP), self.unknown)
        self.assertEqual(self.session().budget.remaining, 64)
        next_receipt = self.session().execute(task(run_id='next'), self.worker, observed_at=STAMP)
        self.assertEqual(next_receipt['outcome'], 'KNOWN')
        self.assertEqual(self.session().budget.remaining, 0)  # old unknown's 64 remain reserved
        self.assertEqual(self.calls, ['uncertain', 'next'])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM resolution_events').fetchone()[0], 1)

    def test_synthetic_new_process_rechecks_human_witness_and_keeps_old_reservation(self):
        p = self.proposal(); self.accepted.add(p['resolution_ref']); self.acknowledge(p)
        code = ('import json,sys; from meta_harness.execution_journal import ExecutionJournal,DurableTokenBudget; '
                'from meta_harness.delegation import Session; from tests.test_meta_delegation import grant,result,task,STAMP; '
                'j=ExecutionJournal(sys.argv[1],resolution_witness=lambda r:r["resolution_ref"]==sys.argv[2]); '
                's=Session(grant,DurableTokenBudget(j),journal=j); '
                'print(json.dumps(s.execute(task(run_id="next"),result,observed_at=STAMP)))')
        child = subprocess.run([sys.executable, '-B', '-c', code, str(self.path), p['resolution_ref']],
                               capture_output=True, text=True, timeout=10)
        self.assertEqual(child.returncode, 0)
        self.assertEqual(json.loads(child.stdout)['outcome'], 'KNOWN')
        self.assertEqual(self.session().budget.remaining, 0)
        self.assertEqual(self.session().execute(task(), self.worker, observed_at=STAMP), self.unknown)
        self.assertEqual(self.calls, ['uncertain'])

    def test_missing_or_revoked_host_witness_closes_future_work(self):
        p = self.proposal(); self.accepted.add(p['resolution_ref']); self.acknowledge(p)
        with self.assertRaises(Failure): self.session(witness=False).execute(task(run_id='next'), self.worker, observed_at=STAMP)
        self.accepted.clear()
        with self.assertRaises(Failure): self.session().execute(task(run_id='next'), self.worker, observed_at=STAMP)
        self.assertEqual(self.calls, ['uncertain'])

    def test_revocation_during_commit_rolls_back_entire_event(self):
        p = self.proposal(); self.accepted.add(p['resolution_ref'])
        checks = iter([True, False])
        with self.assertRaises(Failure): self.acknowledge(p, fence=lambda _:next(checks, False))
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM resolution_events').fetchone()[0], 0)
        with self.assertRaises(Failure): self.session().execute(task(run_id='next'), self.worker, observed_at=STAMP)
        self.assertEqual(self.session().budget.remaining, 64)

    def test_legacy_journal_without_identity_is_not_migrated_or_unblocked(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('DROP TABLE journal_identity'); db.commit()
        with self.assertRaises(Failure): self.proposal()
        with self.assertRaises(Failure): self.session().execute(task(run_id='next'), self.worker, observed_at=STAMP)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='journal_identity'").fetchone())

    def test_tampered_or_cross_journal_resolution_is_rejected(self):
        p = self.proposal(); self.accepted.add(p['resolution_ref']); self.acknowledge(p)
        with closing(sqlite3.connect(self.path)) as db:
            raw = json.loads(db.execute('SELECT record FROM resolution_events').fetchone()[0])
            raw['reservation_release'] = True
            db.execute('UPDATE resolution_events SET record=?', (json.dumps(raw),)); db.commit()
        with self.assertRaises(Failure): self.session().execute(task(run_id='next'), self.worker, observed_at=STAMP)
        other = ExecutionJournal.create(Path(self.temp.name)/'other.sqlite3')
        other.claim(task()['run_id'], sha(task()))
        other = ExecutionJournal(other.path, resolution_witness=lambda _:True)
        with self.assertRaises(Failure):
            other.acknowledge_unknown(task()['run_id'], sha(task()), evidence_ref='e'*64,
                authority_ref='f'*64, observed_at=STAMP, expected_ref=p['resolution_ref'],
                human_authorize=lambda _:True, quiescence=lambda _:True)
