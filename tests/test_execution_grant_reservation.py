"""Synthetic-only tests for the host-verified execution-grant reservation contract."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from meta_harness.execution_journal import ExecutionJournal, GrantVerificationSource

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)
GRANT = 'a' * 64
RUN = 'run-one'
TASK = 'b' * 64
AGENT = 'codex'
HOST = 'c' * 64
EXPIRY = (NOW + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')


class FixtureAuthority(GrantVerificationSource):
    evidence_class = 'SYNTHETIC'

    def __init__(self, row=None):
        self.row = row or {'grant_id': GRANT, 'run_id': RUN, 'task_sha256': TASK,
                           'agent_id': AGENT, 'host_conditions_sha256': HOST,
                           'grant_sha256': 'd' * 64, 'issuer_ref': 'e' * 64,
                           'revocation_generation': 3, 'expires_at': EXPIRY,
                           'revoked': 0, 'signature_valid': 1}
        self.calls = 0

    def install(self, path):
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE fixture_authority (grant_id TEXT PRIMARY KEY, run_id TEXT, '
                       'task_sha256 TEXT, agent_id TEXT, host_conditions_sha256 TEXT, grant_sha256 TEXT, '
                       'issuer_ref TEXT, revocation_generation INTEGER, expires_at TEXT, '
                       'revoked INTEGER, signature_valid INTEGER)')
            db.execute('INSERT INTO fixture_authority VALUES(?,?,?,?,?,?,?,?,?,?,?)', tuple(self.row.values()))

    def verify_for_reservation(self, *, db, binding, now):
        self.calls += 1
        row = db.execute('SELECT grant_id,run_id,task_sha256,agent_id,host_conditions_sha256,'
                         'grant_sha256,issuer_ref,revocation_generation,expires_at,revoked,signature_valid '
                         'FROM fixture_authority WHERE grant_id=?', (binding['grant_id'],)).fetchone()
        if row is None:
            return {'state': 'NO_DATA', 'cause': 'fixture_authority_missing'}
        (grant_id, run_id, task_sha256, agent_id, host_sha, grant_sha, issuer_ref,
         rev_generation, expires_at, revoked, signature_valid) = row
        if not signature_valid:
            return {'state': 'REJECTED', 'cause': 'grant_signature_unverified'}
        if revoked:
            return {'state': 'REJECTED', 'cause': 'grant_revoked'}
        expected = {'grant_id': grant_id, 'run_id': run_id, 'task_sha256': task_sha256,
                    'agent_id': agent_id, 'host_conditions_sha256': host_sha}
        if binding != expected:
            return {'state': 'REJECTED', 'cause': 'authorization_binding_mismatch'}
        if datetime.strptime(expires_at, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc) <= now:
            return {'state': 'REJECTED', 'cause': 'grant_expired'}
        return {'state': 'VERIFIED', **expected, 'grant_sha256': grant_sha,
                'issuer_ref': issuer_ref, 'revocation_generation': rev_generation,
                'expires_at': expires_at, 'evidence_class': self.evidence_class}


class FailingAfterAuthorizationInsert(ExecutionJournal):
    def _claim_in_transaction(self, db, run_id, task_ref, budget_cap):
        raise RuntimeError('synthetic crash between authorization reservation and claim row')


class ExecutionGrantReservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='execution-grant-r1-')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'journal.sqlite3'
        self.source = FixtureAuthority()
        self.journal = ExecutionJournal.create(self.path, grant_source=self.source,
                                               wall_clock=lambda: NOW)
        self.source.install(self.path)

    def reserve(self, journal=None, **changes):
        binding = {'grant_id': GRANT, 'run_id': RUN, 'task_sha256': TASK,
                   'agent_id': AGENT, 'host_conditions_sha256': HOST}
        binding.update(changes)
        return (journal or self.journal).claim_authorized(**binding)

    def test_missing_authority_source_is_no_data_and_writes_nothing(self):
        no_source = ExecutionJournal(self.path, wall_clock=lambda: NOW)
        result = no_source.claim_authorized(grant_id=GRANT, run_id=RUN, task_sha256=TASK,
                                            agent_id=AGENT, host_conditions_sha256=HOST)
        self.assertEqual(result, {'state': 'NO_DATA', 'cause': 'authorization_source_unavailable'})
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT count(*) FROM authorization_reservations').fetchone()[0], 0)

    def test_valid_fixture_reserves_all_bindings_but_never_says_authorized(self):
        result = self.reserve()
        self.assertEqual(result['state'], 'SIMULATED_RESERVED')
        self.assertEqual(result['cause'], 'synthetic_verifier_only')
        self.assertEqual(result['task_sha256'], TASK)
        with sqlite3.connect(self.path) as db:
            row = db.execute('SELECT grant_id,run_id,task_sha256,agent_id,host_conditions_sha256,'
                             'grant_sha256,issuer_ref,revocation_generation,expires_at,evidence_class '
                             'FROM authorization_reservations').fetchone()
            self.assertEqual(row, (GRANT, RUN, TASK, AGENT, HOST, 'd' * 64, 'e' * 64,
                                   3, EXPIRY, 'SYNTHETIC'))
            self.assertEqual(db.execute('SELECT run_id,task_ref FROM claims').fetchone(), (RUN, TASK))

    def test_replay_task_agent_and_host_binding_rejected(self):
        for changes in ({'run_id': 'other-run'}, {'task_sha256': 'f' * 64},
                        {'agent_id': 'junie'}, {'host_conditions_sha256': '9' * 64}):
            with self.subTest(changes=changes):
                self.assertEqual(self.reserve(**changes)['state'], 'REJECTED')
        self.assertEqual(self.source.calls, 4)

    def test_one_grant_cannot_be_reserved_again_after_restart(self):
        self.assertEqual(self.reserve()['state'], 'SIMULATED_RESERVED')
        restarted = ExecutionJournal(self.path, grant_source=self.source, wall_clock=lambda: NOW)
        second = restarted.claim_authorized(grant_id=GRANT, run_id='run-two', task_sha256=TASK,
                                            agent_id=AGENT, host_conditions_sha256=HOST)
        self.assertEqual(second, {'state': 'REJECTED', 'cause': 'grant_reused'})
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT count(*) FROM authorization_reservations').fetchone()[0], 1)

    def test_real_label_without_integrated_trust_boundary_is_no_data(self):
        class UntrustedRealLabel(FixtureAuthority):
            evidence_class = 'REAL'
        result = self.reserve(journal=ExecutionJournal(
            self.path, grant_source=UntrustedRealLabel(), wall_clock=lambda: NOW))
        self.assertEqual(result, {'state': 'NO_DATA', 'cause': 'real_authority_verifier_not_integrated'})
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT count(*) FROM authorization_reservations').fetchone()[0], 0)

    def test_revoked_and_expired_grants_are_rejected(self):
        with sqlite3.connect(self.path) as db:
            db.execute('UPDATE fixture_authority SET revoked=1 WHERE grant_id=?', (GRANT,))
        self.assertEqual(self.reserve(), {'state': 'REJECTED', 'cause': 'grant_revoked'})
        with sqlite3.connect(self.path) as db:
            db.execute('UPDATE fixture_authority SET revoked=0,expires_at=? WHERE grant_id=?',
                       ((NOW - timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%SZ'), GRANT))
        self.assertEqual(self.reserve(), {'state': 'REJECTED', 'cause': 'grant_expired'})
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 0)

    def test_competing_reservations_for_one_grant_are_serialized(self):
        barrier = threading.Barrier(3)
        outcomes = []

        def contender(run_id):
            journal = ExecutionJournal(self.path, grant_source=self.source, wall_clock=lambda: NOW)
            barrier.wait()
            outcomes.append(journal.claim_authorized(grant_id=GRANT, run_id=run_id, task_sha256=TASK,
                                                     agent_id=AGENT, host_conditions_sha256=HOST))

        threads = [threading.Thread(target=contender, args=(name,)) for name in ('run-one', 'run-two')]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(5)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(sum(item['state'] == 'SIMULATED_RESERVED' for item in outcomes), 1)
        self.assertEqual(sum(item['state'] == 'REJECTED' for item in outcomes), 1)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT count(*) FROM authorization_reservations').fetchone()[0], 1)

    def test_failure_between_grant_reservation_and_run_claim_rolls_back_both(self):
        broken = FailingAfterAuthorizationInsert(self.path, grant_source=self.source, wall_clock=lambda: NOW)
        failed = broken.claim_authorized(grant_id=GRANT, run_id=RUN, task_sha256=TASK,
                                         agent_id=AGENT, host_conditions_sha256=HOST)
        self.assertEqual(failed, {'state': 'NO_DATA', 'cause': 'journal_reservation_write_failed'})
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT count(*) FROM authorization_reservations').fetchone()[0], 0)
        self.assertEqual(self.reserve()['state'], 'SIMULATED_RESERVED')

    def test_corrupt_or_unrecognized_verifier_result_fails_closed(self):
        class Broken(GrantVerificationSource):
            def verify_for_reservation(self, **_):
                return {'state': 'VERIFIED', 'grant_id': GRANT}
        journal = ExecutionJournal(self.path, grant_source=Broken(), wall_clock=lambda: NOW)
        result = self.reserve(journal=journal)
        self.assertEqual(result, {'state': 'NO_DATA', 'cause': 'authorization_verifier_result_invalid'})
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
