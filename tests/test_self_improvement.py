"""Synthetic host witnesses: no real source authority is asserted."""
import copy
import unittest

from meta_harness.delegation import Session, TokenBudget
from meta_harness.self_improvement import propose
from tests.test_meta_delegation import STAMP, grant, result, task


def receipt():
    return Session(lambda _: None, TokenBudget(0)).execute(task(), lambda *_: None, observed_at=STAMP)


class ImprovementProposalTests(unittest.TestCase):
    def test_review_only_deterministic_and_no_execution_authority(self):
        r = receipt()
        witness = lambda _: True  # synthetic fixture, not a real host witness
        p = propose([r], verify_source=witness)
        self.assertEqual(p, propose([copy.deepcopy(r)], verify_source=witness))
        self.assertEqual(p['state'], 'REVIEW_REQUIRED')
        self.assertEqual(p['suggestions'][0]['next_action'], 'request_permission')
        self.assertFalse(p['execution_authorized'])

    def test_denies_missing_false_exception_or_tampered_witness(self):
        r = receipt()
        bad = copy.deepcopy(r)
        bad['failure_class'] = 'NONE'
        def raises(_):
            raise RuntimeError('private detail')
        for rows, witness in [([r], None), ([r], lambda _: False), ([r], raises),
                              ([bad], lambda _: True), ([r, r], lambda _: True),
                              ([], lambda _: True), ([r] * 65, lambda _: True)]:
            with self.subTest(rows=len(rows), witness=witness):
                self.assertEqual(propose(rows, verify_source=witness)['state'], 'NO_DATA')

    def test_witness_mutation_does_not_alter_proposal(self):
        r = receipt()
        def mutating(copy_of_receipt):
            copy_of_receipt['failure_class'] = 'NONE'
            return True
        self.assertEqual(propose([r], verify_source=mutating)['suggestions'][0]['failure_class'], 'PERMISSION')
        self.assertEqual(r['failure_class'], 'PERMISSION')


class NoChangeTests(unittest.TestCase):
    def test_successful_receipt_has_no_change_limited_to_input(self):
        r = Session(grant, TokenBudget(64)).execute(task(), result, observed_at=STAMP)
        p = propose([r], verify_source=lambda _: True)  # synthetic witness
        self.assertEqual((p['state'], p['cause']), ('NO_CHANGE', 'no_failure_in_supplied_receipts'))
        self.assertEqual(p['schema'], 'preceptoros.self-improvement/2')
        self.assertEqual(p['suggestions'], [])
        self.assertFalse(p['execution_authorized'])
        self.assertEqual(p, propose([r], verify_source=lambda _: True))
        self.assertEqual(propose([r])['state'], 'NO_DATA')

    def test_any_failure_requires_review(self):
        success = Session(grant, TokenBudget(64)).execute(task(), result, observed_at=STAMP)
        failure = receipt()
        p = propose([success, failure], verify_source=lambda _: True)
        self.assertEqual(p['state'], 'REVIEW_REQUIRED')
        self.assertEqual(len(p['suggestions']), 1)
        self.assertFalse(p['execution_authorized'])
