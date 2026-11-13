"""Disposable SQLite WAL experiments; no production witness, retry or service."""
from contextlib import closing
from datetime import datetime
import json
import os
import sqlite3
import subprocess
import sys
import unittest

from meta_harness.delegation import Failure, Session, sha
from meta_harness.execution_journal import DurableTokenBudget, ExecutionJournal
from meta_harness.host_witness import HostWitness
from meta_harness.source_capture import FixtureSourceCapture
from tests.test_meta_delegation import STAMP, task
import tests.test_human_uncertainty as synthetic


class WalConsistencyFixture(unittest.TestCase):
    def setUp(self):
        self.fixture = synthetic.HumanUncertainty()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path
        self.writer = sqlite3.connect(self.path, timeout=2)
        self.addCleanup(self.writer.close)
        self.assertEqual(self.writer.execute('PRAGMA journal_mode=WAL').fetchone()[0].lower(), 'wal')
        self.writer.execute('PRAGMA wal_autocheckpoint=0')
        self.writer.execute('CREATE TABLE fixture_generation (generation INTEGER, left_value INTEGER, right_value INTEGER)')
        self.writer.execute('INSERT INTO fixture_generation VALUES (1, 1, 1)')
        self.writer.commit()
        self.reader = sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True, timeout=2)
        self.addCleanup(self.reader.close)
        self.assertTrue(os.path.exists(str(self.path) + '-wal'))

    def snapshot(self, *, progress=None):
        # SQLite's backup API, on a disposable fixture only. Source is not immutable=1.
        dst = sqlite3.connect(':memory:')
        self.addCleanup(dst.close)
        self.reader.backup(dst, pages=1, progress=progress, sleep=0.001)
        return dst

    def test_committed_wal_included_uncommitted_excluded_and_unknown_retained(self):
        self.writer.execute('BEGIN IMMEDIATE')
        self.writer.execute('UPDATE fixture_generation SET generation=2,left_value=2,right_value=2')
        dst = self.snapshot()
        self.assertEqual(dst.execute('SELECT * FROM fixture_generation').fetchone(), (1, 1, 1))
        raw = dst.execute('SELECT receipt FROM claims WHERE run_id=?', (task()['run_id'],)).fetchone()[0]
        self.assertEqual(json.loads(raw)['outcome'], 'UNKNOWN')
        self.assertEqual(dst.execute('SELECT remaining FROM durable_budget').fetchone()[0], 64)
        self.assertEqual(dst.execute('SELECT status FROM budget_reservations').fetchone()[0], 'UNKNOWN')
        self.writer.rollback()
        self.assertEqual(self.fixture.calls, ['uncertain'])

    def test_concurrent_commit_backup_is_not_mixed_or_source_authority(self):
        # Force enough pages to exercise incremental backup. Writer acts in progress callback.
        self.writer.execute('CREATE TABLE fixture_padding (payload BLOB)')
        self.writer.executemany('INSERT INTO fixture_padding VALUES (?)', [(bytes(4000),)] * 80)
        self.writer.commit()
        fired = []
        def progress(status, remaining, total):
            if not fired and remaining > 0:
                fired.append(True)
                self.writer.execute('UPDATE fixture_generation SET generation=2,left_value=2,right_value=2')
                self.writer.commit()
        dst = self.snapshot(progress=progress)
        self.assertTrue(fired)
        self.assertIn(dst.execute('SELECT * FROM fixture_generation').fetchone(), ((1, 1, 1), (2, 2, 2)))
        self.assertEqual(dst.execute('PRAGMA quick_check').fetchone(), ('ok',))
        # Coherent SQLite data is not a signed host source or authority.
        witness = HostWitness(self.fixture.journal.identity(), sha(task()),
                              now=lambda: datetime.fromisoformat(STAMP.replace('Z', '+00:00')))
        self.assertFalse(witness.resolution_witness(self.fixture.proposal()))

    def test_snapshot_stale_after_wal_change_and_no_use_time_fence(self):
        dst = self.snapshot()
        observed = dst.execute('SELECT generation FROM fixture_generation').fetchone()[0]
        self.writer.execute('UPDATE fixture_generation SET generation=2,left_value=2,right_value=2')
        self.writer.commit()
        live = self.reader.execute('SELECT generation FROM fixture_generation').fetchone()[0]
        self.assertNotEqual(observed, live)  # stale fixture, never a durable generation witness
        witness = HostWitness(self.fixture.journal.identity(), sha(task()))
        self.assertFalse(witness.quiescence(self.fixture.proposal()))
        self.assertEqual(self.fixture.session().budget.remaining, 64)

    def test_wal_and_shm_remain_refused_by_existing_capture(self):
        info = self.path.stat()
        spec = {'owned': {'path': str(self.path), 'device': info.st_dev, 'inode': info.st_ino,
                          'journal_id': self.fixture.journal.identity()}}
        r = FixtureSourceCapture(spec, local_witness=lambda _: True,
                                 fixture_witness=lambda _: True).capture('owned')
        self.assertEqual((r['state'], r['cause']), ('NO_DATA', 'source_sidecar_present'))
        self.assertFalse(r['execution_authorized'])
        self.assertTrue(r['no_retry'])

    def test_forged_witness_and_revoked_permission_do_not_dispatch(self):
        record = self.fixture.proposal()
        witness = HostWitness(self.fixture.journal.identity(), sha(task()),
                              now=lambda: datetime.fromisoformat(STAMP.replace('Z', '+00:00')))
        forged = dict(record, authority_ref='0'*64)
        self.assertFalse(witness.human_authorize(forged))
        self.assertFalse(witness.quiescence(record))
        self.assertFalse(witness.resolution_witness(record))
        journal = ExecutionJournal(self.path, resolution_witness=witness.resolution_witness)
        session = Session(lambda _: None, DurableTokenBudget(journal), journal=journal)
        # UNKNOWN blocks even before the new grant is consulted.
        with self.assertRaises(Failure):
            session.execute(task(run_id='next'), self.fixture.worker, observed_at=STAMP)
        self.assertEqual(self.fixture.calls, ['uncertain'])
        self.assertEqual(session.budget.remaining, 64)

    def test_restart_with_unresolved_claim_never_retries_or_refunds(self):
        # New Session + reopened journal is a synthetic process-restart analogue;
        # existing test_human_uncertainty includes an actual subprocess restart.
        journal = ExecutionJournal(self.path, resolution_witness=None)
        session = Session(self.fixture.session().authority, DurableTokenBudget(journal), journal=journal)
        with self.assertRaises(Failure):
            session.execute(task(run_id='next'), self.fixture.worker, observed_at=STAMP)
        self.assertEqual(session.budget.remaining, 64)
        self.assertEqual(self.fixture.calls, ['uncertain'])

    def test_cloned_id_and_inode_replacement_are_not_host_provenance(self):
        dst = self.snapshot()
        clone = self.path.parent / 'clone.sqlite3'
        with closing(sqlite3.connect(clone)) as filedb:
            dst.backup(filedb)
        clone.chmod(0o600)
        with closing(sqlite3.connect(clone)) as db:
            clone_id = db.execute('SELECT id FROM journal_identity').fetchone()[0]
        self.assertEqual(clone_id, self.fixture.journal.identity())
        source_info = self.path.stat()
        clone_info = clone.stat()
        self.assertNotEqual(source_info.st_ino, clone_info.st_ino)
        spec = {'clone': {'path': str(clone), 'device': source_info.st_dev, 'inode': source_info.st_ino,
                          'journal_id': clone_id}}
        r = FixtureSourceCapture(spec, local_witness=lambda _: True,
                                 fixture_witness=lambda _: True).capture('clone')
        self.assertEqual((r['state'], r['cause']), ('NO_DATA', 'source_identity_mismatch'))
        self.assertFalse(r['execution_authorized'])
        # Even if a host pins the clone's own inode, a copied journal ID is not authority.
        spec['clone']['inode'] = clone_info.st_ino
        r = FixtureSourceCapture(spec, local_witness=lambda _: True,
                                 fixture_witness=lambda _: True).capture('clone')
        self.assertEqual(r['source_integrity'], 'NO_DATA(real_host_stability)')
        self.assertFalse(r['execution_authorized'])

    def test_revoked_permission_on_empty_journal_still_never_dispatches(self):
        path = self.path.parent / 'empty.sqlite3'
        journal = ExecutionJournal.create(path)
        journal.initialize_budget(128)
        session = Session(lambda _: None, DurableTokenBudget(journal), journal=journal)
        receipt = session.execute(task(run_id='next'), self.fixture.worker, observed_at=STAMP)
        self.assertEqual((receipt['failure_class'], receipt['outcome']), ('PERMISSION', 'NOT_STARTED'))
        self.assertEqual(session.budget.remaining, 128)
        self.assertEqual(self.fixture.calls, ['uncertain'])

    def test_real_subprocess_restart_blocks_unknown_without_refund(self):
        code = ("import sys; from meta_harness.delegation import Session,Failure; "
                "from meta_harness.execution_journal import ExecutionJournal,DurableTokenBudget; "
                "from tests.test_meta_delegation import grant,task,STAMP; "
                "j=ExecutionJournal(sys.argv[1],resolution_witness=None); "
                "s=Session(grant,DurableTokenBudget(j),journal=j); "
                "exec(\"try:\\n s.execute(task(run_id='next'),lambda *_:sys.exit(77),observed_at=STAMP)\\nexcept Failure:\\n print('BLOCKED',s.budget.remaining)\")")
        child = subprocess.run([sys.executable, '-B', '-c', code, str(self.path)],
                               capture_output=True, text=True, timeout=10)
        self.assertEqual(child.returncode, 0)
        self.assertEqual(child.stdout.strip(), 'BLOCKED 64')
        self.assertEqual(self.fixture.calls, ['uncertain'])
