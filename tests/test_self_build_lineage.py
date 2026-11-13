"""Git repositories are real temporary fixtures; snapshot/guard doubles are synthetic."""
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from meta_harness.improvement import _digest
from meta_harness.self_build_git_witness import GitWitness
from meta_harness.self_build_lineage import Lineage, binding_ref
from tests.test_self_build_preflight import proposal


class FixtureSnapshot:
    def __init__(self, ref, payload):
        self.ref, self.payload, self.valid = ref, payload, True

    def read(self, ref):
        if not self.valid or ref != self.ref:
            return None, {'snapshot_integrity': 'NO_DATA'}
        return self.payload, {'snapshot_integrity': 'VERIFIED'}


class LineageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        (self.root / 'docs').mkdir()
        (self.root / 'docs/a.md').write_text('old\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.base = self.git('rev-parse', 'HEAD').strip().decode()
        (self.root / 'docs/a.md').write_text('new\n')
        self.git('commit', '-qam', 'candidate')
        self.head = self.git('rev-parse', 'HEAD').strip().decode()
        self.patch = self.git('diff', '--binary', '--full-index', '--no-renames', '--no-ext-diff',
                              '--no-textconv', self.base, self.head, '--')
        self.p = proposal()
        self.p.update(repo_ref='a' * 64, base_sha=self.base, paths=['docs/a.md'],
                      patch_ref=hashlib.sha256(self.patch).hexdigest())
        self.ref = _digest(self.p)
        self.operation = 'd' * 64
        self.git_witness = GitWitness(self.root, 'a' * 64, self.head, stable_source=lambda: True)
        self.lineage = Lineage(self.git_witness, self.operation)
        self.snapshot = FixtureSnapshot(binding_ref(self.ref, self.head, self.operation), self.patch)
        mocker = patch('meta_harness.self_build_lineage._snapshot_type', return_value=FixtureSnapshot)
        mocker.start()
        self.addCleanup(mocker.stop)

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, stderr=subprocess.DEVNULL)

    def assess(self):
        return self.lineage.assess(self.p, self.ref, self.head, self.operation, self.snapshot)

    def test_integrity_is_not_synthetic_source_authority(self):
        r = self.assess()
        self.assertEqual((r['integrity'], r['source'], r['cause']),
                         ('INTEGRITY_VERIFIED', 'NO_DATA', 'real_host_stability'))
        self.assertFalse(r['execution_authorized'])
        self.assertEqual(r, self.assess())

    def test_wrong_repo_base_candidate_proposal_or_operation(self):
        for key in ('repo_ref', 'base_sha'):
            p = dict(self.p, **{key: '0' * (64 if key == 'repo_ref' else 40)})
            r = self.lineage.assess(p, _digest(p), self.head, self.operation, self.snapshot)
            self.assertNotEqual(r['source'], 'SOURCE_VERIFIED')
        for head, operation, ref in [('0' * 40, self.operation, self.ref),
                                     (self.head, 'e' * 64, self.ref),
                                     (self.head, self.operation, '0' * 64)]:
            self.assertEqual(self.lineage.assess(self.p, ref, head, operation, self.snapshot)['state'], 'NO_DATA')

    def test_patch_substitution_expiry_and_cross_operation(self):
        self.snapshot.payload = b'substituted'
        self.assertEqual(self.assess()['integrity'], 'NO_DATA')
        self.snapshot.payload = self.patch
        self.snapshot.valid = False  # simulates expiry or revocation; no real seal here
        self.assertEqual(self.assess()['integrity'], 'NO_DATA')
        self.snapshot.valid = True
        other = Lineage(self.git_witness, 'e' * 64)
        r = other.assess(self.p, self.ref, self.head, 'e' * 64, self.snapshot)
        self.assertEqual(r['integrity'], 'NO_DATA')

    def test_missing_snapshot_or_fabricated_object(self):
        with patch('meta_harness.self_build_lineage._snapshot_type', side_effect=ImportError):
            self.assertEqual(self.assess()['cause'], 'snapshot_component_unavailable')
        self.assertEqual(self.lineage.assess(self.p, self.ref, self.head, self.operation, object())['cause'],
                         'snapshot_type_unverified')

    def test_missing_real_host_stability_stays_no_data(self):
        self.git_witness.stable_source = None
        r = self.assess()
        self.assertEqual((r['state'], r['source'], r['cause']), ('NO_DATA', 'NO_DATA', 'real_host_stability'))

    def test_head_change_and_dirty_git_object_do_not_establish_source(self):
        self.git('checkout', '-q', '--detach', self.base)
        self.assertEqual(self.assess()['cause'], 'git_source_unverified')
        self.git('checkout', '-q', '--detach', self.head)
        (self.root / 'docs/a.md').write_text('dirty\n')
        self.assertEqual(self.assess()['cause'], 'git_source_unverified')

    def test_git_modes_and_paths_contradictions(self):
        p = dict(self.p, paths=['docs/other.md'])
        rref = _digest(p)
        snap = FixtureSnapshot(binding_ref(rref, self.head, self.operation), self.patch)
        r = self.lineage.assess(p, rref, self.head, self.operation, snap)
        self.assertEqual(r['cause'], 'git_source_unverified')

    def test_head_flip_and_restore_cannot_prove_stability(self):
        self.git('checkout', '-q', '--detach', self.base)
        self.git('checkout', '-q', '--detach', self.head)
        r = self.assess()
        self.assertEqual((r['source'], r['cause']), ('NO_DATA', 'real_host_stability'))

    def test_replaced_git_object_cannot_prove_source(self):
        oid = self.git('rev-parse', self.head + '^{tree}').strip().decode()
        obj = self.root / '.git' / 'objects' / oid[:2] / oid[2:]
        obj.unlink()
        obj.write_bytes(b'corrupt')
        r = self.assess()
        self.assertEqual(r['source'], 'NO_DATA')
        self.assertFalse(r['execution_authorized'])
