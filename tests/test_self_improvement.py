"""Synthetic host witnesses: no real source authority is asserted."""
import copy
import unittest

from meta_harness.delegation import Session, TokenBudget
from meta_harness.self_improvement import propose
from tests.test_meta_delegation import STAMP, grant, task


def receipt():
    return Session(lambda _: None, TokenBudget(0)).execute(task(), lambda *_: None, observed_at=STAMP)


class ImprovementProposalTests(unittest.TestCase):
    def test_review_only_deterministic_and_no_execution_authority(self):
        r = receipt()
        witness = lambda _: True  # synthetic fixture, not a real host witness
        p = propose([r], verify_source=witness)
        self.assertEqual(p, propose([copy.deepcopy(r)], verify_source=witness))
        self.assertEqual(p['state'], 'PROPOSAL_ONLY')
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
