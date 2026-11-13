"""Local synthetic evidence: kernel sealing is not host/source authority."""
import fcntl
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from meta_harness.sealed_patch_snapshot import capture


class SealedPatchTests(unittest.TestCase):
    def make(self, payload=b'patch bytes', clock=lambda: 100.0, seconds=10):
        snap, state = capture(payload, proposal_ref='a' * 64,
                              patch_ref=hashlib.sha256(payload).hexdigest(),
                              lifetime_seconds=seconds, clock=clock)
        self.assertIsNotNone(snap)
        self.addCleanup(snap.revoke)
        self.assertEqual(state['snapshot_integrity'], 'VERIFIED')
        self.assertEqual(state['state'], 'NO_DATA')
        return snap

    def test_kernel_seal_denies_write_and_truncate(self):
        snap = self.make()
        duplicate = os.dup(snap._fd)
        try:
            with self.assertRaises(OSError):
                os.pwrite(duplicate, b'x', 0)
            with self.assertRaises(OSError):
                os.ftruncate(duplicate, 0)
        finally:
            os.close(duplicate)
        payload, status = snap.read('a' * 64)
        self.assertEqual(payload, b'patch bytes')
        self.assertEqual((status['state'], status['cause']), ('NO_DATA', 'real_host_stability'))
        self.assertFalse(status['execution_authorized'])

    def test_digest_and_proposal_binding(self):
        snap = self.make()
        self.assertEqual(snap.read('b' * 64)[1]['cause'], 'proposal_mismatch')
        bad, result = capture(b'other', proposal_ref='a' * 64, patch_ref='0' * 64, lifetime_seconds=10)
        self.assertIsNone(bad)
        self.assertEqual(result['state'], 'NO_DATA')

    def test_expiration_and_revocation(self):
        now = [100.0]
        snap = self.make(clock=lambda: now[0])
        now[0] = 110.0
        self.assertEqual(snap.read('a' * 64)[1]['cause'], 'snapshot_expired_or_clock_invalid')
        self.assertEqual(snap.read('a' * 64)[1]['cause'], 'snapshot_revoked')
        snap = self.make()
        snap.revoke()
        self.assertEqual(snap.read('a' * 64)[1]['cause'], 'snapshot_revoked')

    def test_clock_rollback_and_broken_clock(self):
        now = [100.0]
        snap = self.make(clock=lambda: now[0])
        now[0] = 99.0
        self.assertIsNone(snap.read('a' * 64)[0])
        def fail():
            raise RuntimeError('private')
        snap = self.make()
        snap._clock = fail
        self.assertEqual(snap.read('a' * 64)[1]['cause'], 'snapshot_unavailable')

    def test_replaced_source_file_cannot_change_sealed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'patch'
            path.write_bytes(b'patch bytes')
            snap = self.make(path.read_bytes())
            path.unlink()
            path.write_bytes(b'new patch')
            self.assertEqual(snap.read('a' * 64)[0], b'patch bytes')
            self.assertEqual(snap.read('a' * 64)[1]['source_stability'], 'NO_DATA')

    def test_cooperative_flock_does_not_stop_an_uncooperative_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lock = root / 'cooperative.lock'
            source = root / 'source'
            source.write_bytes(b'patch bytes')
            with lock.open('w') as file:
                fcntl.flock(file, fcntl.LOCK_EX)
                snap = self.make(source.read_bytes())
                subprocess.run(['python3', '-c', 'import pathlib,sys; pathlib.Path(sys.argv[1]).write_bytes(b"changed")',
                                str(source)], check=True)
                self.assertEqual(source.read_bytes(), b'changed')
                self.assertEqual(snap.read('a' * 64)[0], b'patch bytes')
                self.assertEqual(snap.read('a' * 64)[1]['cause'], 'real_host_stability')

    def test_head_flip_then_restore_is_not_host_stability(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL)
            git('init', '-q')
            git('config', 'user.name', 'Fixture')
            git('config', 'user.email', 'fixture@example.invalid')
            git('config', 'commit.gpgsign', 'false')
            (root / 'a').write_text('a')
            git('add', 'a')
            git('commit', '-qm', 'one')
            head = git('rev-parse', 'HEAD').strip()
            snap = self.make()
            git('checkout', '-qb', 'transient')
            (root / 'a').write_text('b')
            git('commit', '-qam', 'two')
            git('checkout', '-q', '--detach', head.decode())
            self.assertEqual(git('rev-parse', 'HEAD').strip(), head)
            self.assertEqual(snap.read('a' * 64)[1]['cause'], 'real_host_stability')

    def test_unsupported_kernel_and_oversized_input_abstain(self):
        with patch('os.memfd_create', side_effect=PermissionError):
            snapshot, status = capture(b'x', proposal_ref='a' * 64,
                                       patch_ref=hashlib.sha256(b'x').hexdigest(), lifetime_seconds=1)
        self.assertIsNone(snapshot)
        self.assertEqual(status['state'], 'NO_DATA')
        snapshot, status = capture(b'x' * (4 * 1024 * 1024 + 1), proposal_ref='a' * 64,
                                   patch_ref='0' * 64, lifetime_seconds=1)
        self.assertIsNone(snapshot)
        self.assertEqual(status['state'], 'NO_DATA')

    def test_git_index_untracked_and_object_mutation_do_not_prove_stability(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL)
            git('init', '-q')
            git('config', 'user.name', 'Fixture')
            git('config', 'user.email', 'fixture@example.invalid')
            git('config', 'commit.gpgsign', 'false')
            (root / 'a').write_text('a')
            git('add', 'a')
            git('commit', '-qm', 'one')
            snap = self.make()
            (root / 'a').write_text('changed')
            git('add', 'a')
            (root / 'untracked').write_text('new')
            objects = [p for p in (root / '.git/objects').glob('*/*') if p.is_file()]
            self.assertTrue(objects)
            objects[0].unlink()
            objects[0].write_bytes(b'corrupt')
            payload, status = snap.read('a' * 64)
            self.assertEqual(payload, b'patch bytes')
            self.assertEqual(status['cause'], 'real_host_stability')
            self.assertFalse(status['execution_authorized'])
