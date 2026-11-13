"""Only disposable fixtures; this is not rack recovery or production authorization."""
import copy
import subprocess
import unittest
from unittest.mock import patch

from meta_harness.delegation import Failure
from meta_harness.improvement import _digest
from meta_harness.readonly_mirror import ReadOnlyMirror
from meta_harness.recovery_readiness import RecoveryReadiness
from meta_harness.sealed_patch_snapshot import capture
from tests.recovery_drill_fixture import BAD, Drill
from tests.test_meta_delegation import STAMP, task
import tests.test_human_uncertainty as synthetic


class RecoveryDrillTests(unittest.TestCase):
    def setUp(self):
        self.drill = Drill()
        self.addCleanup(self.drill.close)

    def test_sandbox_restores_exact_tree_and_prechange_behavior(self):
        r = self.drill.run()
        self.assertEqual(r['state'], 'DEMONSTRATED_IN_SANDBOX')
        self.assertEqual((r['baseline_pass'], r['candidate_pass'], r['restored_pass']), (True, False, True))
        self.assertTrue(r['restored_tree_matches'])
        self.assertEqual((r['source'], r['real_host_recovery'], r['execution']),
                         ('NO_DATA(real_host_stability)', 'NO_DATA', 'NOT_AUTHORIZED'))
        self.assertTrue(all(type(v) is int and v > 0 for v in r['timings_ns'].values()))

    def test_missing_or_incorrect_previous_commit_is_refused(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.drill.git(self.drill.copy, 'checkout', '-q', '--detach', '0'*40)
        self.drill.git(self.drill.copy, 'checkout', '-q', '--detach', self.drill.head)
        self.assertFalse(self.drill.same_tree())

    def test_tampered_patch_or_wrong_proposal_is_rejected(self):
        snap, r = capture(b'tampered', proposal_ref='a'*64, patch_ref=self.drill.patch_ref, lifetime_seconds=10)
        self.assertIsNone(snap)
        self.assertEqual(r['state'], 'NO_DATA')
        p = copy.deepcopy(self.drill.p)
        p['patch_ref'] = '0'*64
        r = self.drill.lineage.assess(p, _digest(p), self.drill.head, self.drill.operation_ref, self.drill.snap)
        self.assertNotEqual(r['integrity'], 'INTEGRITY_VERIFIED')

    def test_head_changed_and_restored_never_becomes_real_source_evidence(self):
        self.drill.git(self.drill.repo, 'checkout', '-q', '--detach', self.drill.base)
        self.assertEqual(self.drill.assess()['cause'], 'git_source_unverified')
        self.drill.git(self.drill.repo, 'checkout', '-q', '--detach', self.drill.head)
        self.assertEqual(self.drill.assess()['source'], 'NO_DATA')

    def test_expired_and_revoked_snapshot(self):
        now = [100.0]
        snap, _ = self.drill.new_snapshot(clock=lambda: now[0], lifetime=1)
        self.addCleanup(snap.revoke)
        now[0] = 101.0
        self.assertNotEqual(self.drill.assess(snapshot=snap)['integrity'], 'INTEGRITY_VERIFIED')
        self.drill.snap.revoke()
        self.assertNotEqual(self.drill.assess()['integrity'], 'INTEGRITY_VERIFIED')

    def test_missing_restored_file_invalidates_tree(self):
        self.drill.restore()
        (self.drill.copy / 'docs/feature.md').unlink()
        self.assertFalse(self.drill.same_tree())

    def test_regression_after_restore_is_detected(self):
        self.drill.restore()
        (self.drill.copy / 'docs/feature.md').write_bytes(BAD)
        self.assertFalse(self.drill.same_tree())
        self.assertFalse(self.drill.check(self.drill.copy)[1])

    def test_wrong_operation_and_synthetic_witness_never_authorize(self):
        self.assertEqual(self.drill.assess(operation='e'*64)['state'], 'NO_DATA')
        r = self.drill.assess()
        self.assertEqual(r['source'], 'NO_DATA')
        self.assertFalse(r['execution_authorized'])

    def test_unknown_execution_is_not_retried_or_refunded(self):
        fixture = synthetic.HumanUncertainty()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        mirror = ReadOnlyMirror({'owned': {'journal': str(fixture.path), 'task': task()}},
                                local_source_witness=lambda _: True)  # synthetic only
        readiness = RecoveryReadiness(mirror, 'owned', previous_sha=self.drill.base,
                                      candidate_sha=self.drill.head, plan_ref=self.drill.operation_ref,
                                      approval_ref='f'*64)
        projected = readiness.read(current_head=self.drill.head, observed_at=STAMP)['machine']['record']
        self.assertEqual((projected['journal_outcome'], projected['reservation']), ('UNKNOWN', 'RETAINED'))
        self.assertFalse(projected['execution_authorized'])
        before = fixture.session().budget.remaining
        with self.assertRaises(Failure):
            fixture.session(witness=False).execute(task(run_id='next'), fixture.worker, observed_at=STAMP)
        self.assertEqual(fixture.calls, ['uncertain'])
        self.assertEqual((before, fixture.session().budget.remaining), (64, 64))
        self.assertEqual(self.drill.run()['execution'], 'NOT_AUTHORIZED')

    def test_mutated_source_objects_do_not_create_source_authority(self):
        tree = self.drill.git(self.drill.repo, 'rev-parse', self.drill.head + '^{tree}').strip().decode()
        obj = self.drill.repo / '.git/objects' / tree[:2] / tree[2:]
        obj.unlink()
        obj.write_bytes(b'corrupt')
        self.assertEqual(self.drill.assess()['source'], 'NO_DATA')
        self.assertFalse(self.drill.assess()['execution_authorized'])

    def test_changed_head_prevents_sandbox_success_before_or_during_restore(self):
        self.drill.git(self.drill.repo, 'checkout', '-q', '--detach', self.drill.base)
        with self.assertRaisesRegex(AssertionError, 'fixture_prerequisites_failed'):
            self.drill.run()
        self.drill.git(self.drill.repo, 'checkout', '-q', '--detach', self.drill.head)
        restore = self.drill.restore
        def change_during_restore():
            elapsed = restore()
            self.drill.git(self.drill.repo, 'checkout', '-q', '--detach', self.drill.base)
            return elapsed
        with patch.object(self.drill, 'restore', side_effect=change_during_restore):
            with self.assertRaisesRegex(AssertionError, 'sandbox_restoration_failed'):
                self.drill.run()

    def test_missing_synthetic_fixture_guard_refuses_measurement(self):
        self.drill.witness.stable_source = None
        with self.assertRaisesRegex(AssertionError, 'fixture_prerequisites_failed'):
            self.drill.run()
