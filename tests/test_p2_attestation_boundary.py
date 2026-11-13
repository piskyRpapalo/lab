"""Cross-boundary synthetic fixtures, not a signer, host fence or live journal."""
from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import unittest

from meta_harness.delegation import Failure, sha
from meta_harness.host_witness import HostWitness
from meta_harness.readonly_mirror import ReadOnlyMirror
from meta_harness.source_capture import FixtureSourceCapture
from tests.test_meta_delegation import STAMP, task
import tests.test_human_uncertainty as synthetic


class AttestationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = synthetic.HumanUncertainty()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path
        self.local = [True]
        self.mirror = ReadOnlyMirror({'owned': {'journal': str(self.path), 'task': task()}},
                                     local_source_witness=lambda _: self.local[0])  # synthetic
        self.now = datetime.fromisoformat(STAMP.replace('Z', '+00:00'))
        self.host = HostWitness(self.fixture.journal.identity(), sha(task()), now=lambda: self.now)

    def capture(self):
        info = self.path.stat()
        config = {'owned': {'path': str(self.path), 'device': info.st_dev, 'inode': info.st_ino,
                            'journal_id': self.fixture.journal.identity()}}
        return FixtureSourceCapture(config, local_witness=lambda _: True,
                                    fixture_witness=lambda _: True).capture('owned')

    def test_consistent_snapshot_and_valid_shaped_ack_are_not_source_authority(self):
        r = self.capture()
        ack = self.fixture.proposal()
        self.assertEqual(r['state'], 'SIMULATED')
        self.assertEqual(r['source_integrity'], 'NO_DATA(real_host_stability)')
        self.assertEqual(self.host.diagnose(ack)['cause'], 'human_authority_and_durable_fence_unavailable')
        self.assertFalse(self.host.human_authorize(ack))
        self.assertFalse(self.host.quiescence(ack))
        self.assertFalse(self.host.resolution_witness(ack))
        self.assertFalse(r['execution_authorized'])

    def test_source_substitution_even_clone_of_journal_identity_is_not_authority(self):
        info = self.path.stat()
        pinned = {'owned': {'path': str(self.path), 'device': info.st_dev, 'inode': info.st_ino,
                            'journal_id': self.fixture.journal.identity()}}
        clone = self.path.parent / 'clone.sqlite3'
        clone.write_bytes(self.path.read_bytes())
        clone.chmod(0o600)
        with closing(sqlite3.connect(clone)) as db:
            self.assertEqual(db.execute('SELECT id FROM journal_identity').fetchone()[0], pinned['owned']['journal_id'])
        os.replace(clone, self.path)  # disposable fixture only
        r = FixtureSourceCapture(pinned, local_witness=lambda _: True,
                                 fixture_witness=lambda _: True).capture('owned')
        self.assertEqual((r['state'], r['cause']), ('NO_DATA', 'source_identity_mismatch'))
        self.assertFalse(self.host.resolution_witness(self.fixture.proposal()))

    def test_unchanged_projection_does_not_attest_source_generation(self):
        packet = self.mirror.read('owned', observed_at=STAMP)
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('CREATE TABLE fixture_unrelated_generation (value INTEGER)')
            db.execute('INSERT INTO fixture_unrelated_generation VALUES (2)')
            db.commit()
        after = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.assertNotEqual(before, after)
        # verify() checks projection equality, not full DB generation or provenance.
        self.assertTrue(self.mirror.verify(packet, 'owned', observed_at=STAMP))
        self.assertEqual(self.capture()['source_integrity'], 'NO_DATA(real_host_stability)')
        self.assertFalse(self.host.resolution_witness(self.fixture.proposal()))
        self.assertEqual(packet['machine']['record']['state'], 'UNKNOWN')

    def test_local_witness_revoked_after_observation_invalidates_use(self):
        packet = self.mirror.read('owned', observed_at=STAMP)
        self.local[0] = False
        self.assertFalse(self.mirror.verify(packet, 'owned', observed_at=STAMP))
        current = self.mirror.read('owned', observed_at=STAMP)['machine']['record']
        self.assertEqual((current['state'], current['cause']), ('NO_DATA', 'local_source_not_attested'))
        self.assertEqual(self.fixture.session().budget.remaining, 64)
        self.assertEqual(self.fixture.calls, ['uncertain'])

    def test_forged_expired_and_restarted_host_never_attest(self):
        record = self.fixture.proposal()
        forged = dict(record, source_verified=True)
        self.assertEqual(self.host.diagnose(forged)['cause'], 'record_invalid')
        self.assertFalse(self.host.quiescence(forged))
        expired = HostWitness(self.fixture.journal.identity(), sha(task()),
                              now=lambda: self.now + timedelta(seconds=121))
        self.assertEqual(expired.diagnose(record)['cause'], 'evidence_expired')
        self.assertFalse(expired.resolution_witness(record))
        restarted = HostWitness(self.fixture.journal.identity(), sha(task()), now=lambda: self.now)
        self.assertEqual(restarted.diagnose(record), self.host.diagnose(record))
        self.assertFalse(restarted.resolution_witness(record))

    def test_revocation_between_synthetic_checks_rolls_back_ack_and_budget(self):
        record = self.fixture.proposal()
        self.fixture.accepted.add(record['resolution_ref'])
        checks = iter((True, False))
        with self.assertRaises(Failure):
            self.fixture.acknowledge(record, fence=lambda _: next(checks, False))
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM resolution_events').fetchone()[0], 0)
        self.assertEqual(self.fixture.session().budget.remaining, 64)
        self.assertEqual(self.fixture.calls, ['uncertain'])

    def test_child_process_restart_blocks_unknown_without_refund(self):
        code = """import sys
from meta_harness.delegation import Session, Failure
from meta_harness.execution_journal import ExecutionJournal, DurableTokenBudget
from tests.test_meta_delegation import grant, task, STAMP
journal = ExecutionJournal(sys.argv[1], resolution_witness=None)
session = Session(grant, DurableTokenBudget(journal), journal=journal)
try:
    session.execute(task(run_id='next'), lambda *_: sys.exit(77), observed_at=STAMP)
except Failure:
    print('BLOCKED', session.budget.remaining)
"""
        child = subprocess.run([sys.executable, '-B', '-c', code, str(self.path)],
                               capture_output=True, text=True, timeout=10)
        self.assertEqual((child.returncode, child.stdout.strip()), (0, 'BLOCKED 64'))
        self.assertEqual(self.fixture.calls, ['uncertain'])
