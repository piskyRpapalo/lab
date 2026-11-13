"""Disposable SQLite only; every witness is synthetic and no APP source is used."""
import hashlib
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import unittest

from meta_harness.delegation import Failure
from meta_harness.source_capture import FixtureSourceCapture, MAX_BYTES
from tests.test_meta_delegation import STAMP, task
import tests.test_human_uncertainty as synthetic


class SourceCaptureTests(unittest.TestCase):
    def setUp(self):
        self.fixture = synthetic.HumanUncertainty()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path
        info = self.path.stat()
        self.spec = {'owned': {'path': str(self.path), 'device': info.st_dev, 'inode': info.st_ino,
                                'journal_id': self.fixture.journal.identity()}}

    def capture(self, *, local=lambda _: True, witness=lambda _: True, spec=None, source='owned'):
        return FixtureSourceCapture(self.spec if spec is None else spec,
                                    local_witness=local, fixture_witness=witness).capture(source)

    def test_clean_fixture_snapshot_is_simulated_not_authority(self):
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        r = self.capture()
        self.assertEqual((r['state'], r['cause']), ('SIMULATED', 'synthetic_fixture_only'))
        self.assertEqual(r['snapshot_sha256'], before)
        self.assertEqual(r['source_integrity'], 'NO_DATA(real_host_stability)')
        self.assertEqual(r['real_host_recovery'], 'NO_DATA(real_host_recovery)')
        self.assertFalse(r['execution_authorized'])
        self.assertTrue(r['no_retry'])
        self.assertEqual(before, hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertNotIn(str(self.path), str(r))

    def test_noncooperative_writer_during_double_read(self):
        calls = []
        def witness(_):
            calls.append(1)
            if len(calls) == 2:
                code = ('import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); '
                        'c.execute("UPDATE durable_budget SET remaining=remaining-1"); c.commit(); c.close()')
                subprocess.run([sys.executable, '-c', code, str(self.path)], check=True, timeout=5)
            return True
        self.assertEqual(self.capture(witness=witness)['cause'], 'source_changed')

    def test_real_wal_writer_during_observation_fails_closed(self):
        calls, connections = [], []
        def witness(_):
            calls.append(1)
            if len(calls) == 2:
                db = sqlite3.connect(self.path)
                connections.append(db)
                db.execute('PRAGMA journal_mode=WAL')
                db.execute('CREATE TABLE synthetic_wal(value INTEGER)')
                db.commit()
            return True
        try:
            r = self.capture(witness=witness)
            self.assertIn(r['cause'], ('source_changed', 'source_sidecar_present'))
            self.assertEqual(r['state'], 'NO_DATA')
        finally:
            for db in connections:
                db.close()

    def test_wal_shm_journal_and_broken_symlink_rejected(self):
        for suffix in ('-wal', '-shm', '-journal'):
            sidecar = Path(str(self.path) + suffix)
            with self.subTest(suffix=suffix):
                sidecar.symlink_to('missing-target')
                self.assertEqual(self.capture()['cause'], 'source_sidecar_present')
                sidecar.unlink()

    def test_wal_appears_after_initial_check(self):
        calls = []
        def local(_):
            calls.append(1)
            if len(calls) == 2:
                Path(str(self.path) + '-wal').write_bytes(b'synthetic')
            return True
        self.assertEqual(self.capture(local=local)['cause'], 'source_sidecar_present')

    def test_wrong_pin_or_replacement_is_rejected(self):
        bad = {'owned': dict(self.spec['owned'], inode=self.spec['owned']['inode'] + 1)}
        self.assertEqual(self.capture(spec=bad)['cause'], 'source_identity_mismatch')
        calls = []
        def witness(_):
            calls.append(1)
            if len(calls) == 2:
                clone = self.path.parent / 'new.sqlite3'
                clone.write_bytes(self.path.read_bytes())
                clone.chmod(0o600)
                os.replace(clone, self.path)
            return True
        self.assertEqual(self.capture(witness=witness)['cause'], 'source_identity_mismatch')

    def test_wrong_journal_identity_is_rejected(self):
        bad = {'owned': dict(self.spec['owned'], journal_id='0'*64)}
        self.assertEqual(self.capture(spec=bad)['cause'], 'journal_identity_mismatch')

    def test_witness_missing_invalid_and_revoked(self):
        self.assertEqual(self.capture(local=None)['cause'], 'local_source_not_attested')
        self.assertEqual(self.capture(local=lambda _: 1)['cause'], 'local_source_not_attested')
        self.assertEqual(self.capture(witness=None)['cause'], 'fixture_witness_unavailable')
        calls = iter((True, False))
        self.assertEqual(self.capture(witness=lambda _: next(calls, False))['cause'], 'fixture_witness_revoked')
        calls = iter((True, False))
        self.assertEqual(self.capture(local=lambda _: next(calls, False))['cause'], 'local_source_revoked')
        self.assertEqual(self.capture(source='not-allowed')['cause'], 'source_not_allowlisted')

    def test_truncated_corrupt_and_oversized_snapshot(self):
        data = self.path.read_bytes()
        self.path.write_bytes(data[:100])
        self.assertEqual(self.capture()['cause'], 'snapshot_corrupt')
        self.path.write_bytes(b'not a sqlite database')
        self.assertEqual(self.capture()['cause'], 'snapshot_corrupt')
        with self.path.open('wb') as file:
            file.truncate(MAX_BYTES + 1)
        self.assertEqual(self.capture()['cause'], 'source_size_invalid')

    def test_unknown_does_not_retry_or_release_reservation(self):
        self.assertEqual(self.fixture.session().budget.remaining, 64)
        self.assertEqual(self.capture()['state'], 'SIMULATED')
        with self.assertRaises(Failure):
            self.fixture.session(witness=False).execute(task(run_id='next'), self.fixture.worker, observed_at=STAMP)
        self.assertEqual(self.fixture.calls, ['uncertain'])
        self.assertEqual(self.fixture.session().budget.remaining, 64)

    def test_mutation_during_final_witness_is_rejected(self):
        calls = []
        def witness(_):
            calls.append(1)
            if len(calls) == 3:
                with sqlite3.connect(self.path) as db:
                    db.execute('UPDATE durable_budget SET remaining=remaining-1')
                    db.commit()
            return True
        self.assertEqual(self.capture(witness=witness)['cause'], 'source_changed')
