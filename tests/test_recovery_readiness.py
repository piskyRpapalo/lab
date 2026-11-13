"""P2 fixture witnesses are synthetic; no recovery or authority is asserted."""
import copy
import hashlib
import unittest
import sqlite3
from contextlib import closing

from meta_harness.delegation import Failure
from meta_harness.execution_journal import ExecutionJournal
from meta_harness.readonly_mirror import ReadOnlyMirror
from meta_harness.recovery_readiness import RecoveryReadiness
from tests.test_meta_delegation import STAMP, task
import tests.test_human_uncertainty as synthetic


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.fixture = synthetic.HumanUncertainty()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.mirror = ReadOnlyMirror({'owned': {'journal': str(self.fixture.path), 'task': task()}},
                                     local_source_witness=lambda _: True)  # synthetic
        self.readiness = RecoveryReadiness(self.mirror, 'owned', previous_sha='a'*40,
                                           candidate_sha='b'*40, plan_ref='c'*64, approval_ref='d'*64)

    def read(self, head='b'*40, now=STAMP):
        return self.readiness.read(current_head=head, observed_at=now)

    def test_unknown_reservation_and_same_views_are_read_only(self):
        before = hashlib.sha256(self.fixture.path.read_bytes()).hexdigest()
        packet = self.read()
        r = packet['machine']['record']
        self.assertEqual((r['state'], r['journal_outcome'], r['reservation']), ('NO_DATA', 'UNKNOWN', 'RETAINED'))
        self.assertEqual((r['plan'], r['previous_version']), ('DECLARED', 'DECLARED'))
        for name in ('previous_provenance', 'isolated_recovery_test', 'worker_fence', 'human_approval'):
            self.assertEqual(r[name], 'NO_DATA')
        self.assertFalse(r['execution_authorized'])
        self.assertTrue(r['no_retry'])
        self.assertEqual({x['state_ref'] for x in packet.values()}, {r['projection_ref']})
        self.assertEqual(packet['text']['summary'], packet['speech']['summary'])
        self.assertEqual(before, hashlib.sha256(self.fixture.path.read_bytes()).hexdigest())
        self.assertTrue(self.readiness.verify(packet, current_head='b'*40, observed_at=STAMP))

    def test_changed_head_and_invalid_clock_never_approve(self):
        r = self.read(head='f'*40)['machine']['record']
        self.assertEqual((r['state'], r['cause'], r['human_approval']), ('NO_DATA', 'candidate_head_mismatch', 'NO_DATA'))
        r = self.read(now='bad')['machine']['record']
        self.assertIsNone(r['observed_at'])
        self.assertEqual(r['journal_outcome'], 'NO_DATA')
        self.assertFalse(r['execution_authorized'])

    def test_resealed_forgery_and_expired_projection_fail_recheck(self):
        packet = self.read()
        forged = copy.deepcopy(packet)
        forged['machine']['record']['human_approval'] = 'VERIFIED'
        self.assertFalse(self.readiness.verify(forged, current_head='b'*40, observed_at=STAMP))
        self.assertFalse(self.readiness.verify(packet, current_head='b'*40, observed_at='2026-11-12T00:00:01Z'))

    def test_synthetic_ack_cannot_certify_fence_or_release_old_budget(self):
        old = self.fixture.proposal()
        self.fixture.accepted.add(old['resolution_ref'])
        self.fixture.acknowledge(old)
        r = self.read()['machine']['record']
        self.assertEqual((r['journal_outcome'], r['reservation'], r['worker_fence']), ('UNKNOWN', 'RETAINED', 'NO_DATA'))
        self.assertEqual(self.fixture.session().budget.remaining, 64)
        self.assertEqual(self.fixture.calls, ['uncertain'])
        self.assertFalse(r['execution_authorized'])

    def test_restart_uncertain_cannot_automatically_retry(self):
        self.assertEqual(self.read()['machine']['record']['journal_outcome'], 'UNKNOWN')
        with self.assertRaises(Failure):
            self.fixture.session(witness=False).execute(task(run_id='next'), self.fixture.worker, observed_at=STAMP)
        self.assertEqual(self.fixture.calls, ['uncertain'])
        self.assertEqual(self.fixture.session().budget.remaining, 64)

    def test_missing_host_source_fails_closed(self):
        mirror = ReadOnlyMirror({'owned': {'journal': str(self.fixture.path), 'task': task()}})
        ready = RecoveryReadiness(mirror, 'owned', previous_sha='a'*40, candidate_sha='b'*40,
                                  plan_ref='c'*64, approval_ref='d'*64)
        r = ready.read(current_head='b'*40, observed_at=STAMP)['machine']['record']
        self.assertEqual((r['journal_outcome'], r['reservation'], r['state']), ('NO_DATA', 'NO_DATA', 'NO_DATA'))

    def test_before_claim_does_not_create_claim_or_reservation(self):
        path = self.fixture.path.parent / 'before.sqlite3'
        journal = ExecutionJournal.create(path)
        journal.initialize_budget(128)
        mirror = ReadOnlyMirror({'before': {'journal': str(path), 'task': task()}},
                                local_source_witness=lambda _: True)
        ready = RecoveryReadiness(mirror, 'before', previous_sha='a'*40, candidate_sha='b'*40,
                                  plan_ref='c'*64, approval_ref='d'*64)
        r = ready.read(current_head='b'*40, observed_at=STAMP)['machine']['record']
        self.assertEqual((r['journal_outcome'], r['state']), ('NO_DATA', 'NO_DATA'))
        with closing(sqlite3.connect(path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT count(*) FROM budget_reservations').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT remaining FROM durable_budget').fetchone()[0], 128)
