"""Consumer contract controls, using only synthetic human and host witnesses."""
import copy
from pathlib import Path
import sqlite3
from contextlib import closing
import unittest

from meta_harness import uncertainty_views as V
import tests.test_human_uncertainty as human
from tests.test_meta_delegation import STAMP, task


class UncertaintyViews(unittest.TestCase):
    def setUp(self):
        self.fixture = human.HumanUncertainty()
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)

    def packet(self):
        record = V.project(self.fixture.journal, task(), observed_at=STAMP)
        return V.views(record)

    def test_unacknowledged_claim_projects_one_unknown_state_for_every_reader(self):
        packet = self.packet(); record = packet['machine']['record']
        self.assertEqual((record['state'],record['acknowledgement']), ('UNKNOWN','HITL_REQUIRED'))
        self.assertEqual(record['reservation'], {'state':'RETAINED','tokens':64})
        self.assertEqual(record['ttl_seconds'], 0)
        self.assertEqual(packet['text']['summary'], packet['speech']['summary'])
        self.assertEqual({v['state_ref'] for v in packet.values()}, {record['projection_ref']})
        self.assertTrue(V.verify(packet, self.fixture.journal, task(), observed_at=STAMP))

    def test_host_witness_acknowledges_without_changing_outcome_or_budget(self):
        proposal = self.fixture.proposal(); self.fixture.accepted.add(proposal['resolution_ref'])
        self.fixture.acknowledge(proposal)
        packet = self.packet(); record = packet['machine']['record']
        self.assertEqual((record['state'],record['acknowledgement']), ('UNKNOWN','HUMAN_ACKNOWLEDGED'))
        self.assertEqual(record['resolution_ref'], proposal['resolution_ref'])
        self.assertEqual(record['reservation'], {'state':'RETAINED','tokens':64})
        self.assertTrue(record['no_retry'])
        self.assertEqual(record['promotion'], 'NOT_AUTHORIZED')
        self.fixture.accepted.clear()
        current = self.packet()['machine']['record']
        self.assertEqual(current['acknowledgement'], 'AUTHORITY_NOT_VERIFIED')
        self.assertIsNone(current['resolution_ref'])
        self.assertFalse(V.verify(packet, self.fixture.journal, task(), observed_at=STAMP))

    def test_resealed_forgery_cannot_replace_host_and_witness(self):
        packet = self.packet(); forged = copy.deepcopy(packet['machine']['record'])
        forged['acknowledgement'] = 'HUMAN_ACKNOWLEDGED'
        forged['projection_ref'] = V.sha({k:v for k,v in forged.items() if k != 'projection_ref'})
        self.assertFalse(V.verify(V.views(forged), self.fixture.journal, task(), observed_at=STAMP))

    def test_wrong_task_missing_budget_and_corrupt_journal_are_not_fabricated(self):
        record = V.project(self.fixture.journal, task(input_sha256='0'*64), observed_at=STAMP)
        self.assertEqual((record['state'],record['cause']), ('NO_DATA','exact_claim_missing'))
        with closing(sqlite3.connect(self.fixture.path)) as db:
            db.execute('DELETE FROM budget_reservations'); db.commit()
        record = self.packet()['machine']['record']
        self.assertEqual(record['reservation'], {'state':'NO_DATA','cause':'reservation_inconsistent'})
        with closing(sqlite3.connect(self.fixture.path)) as db:
            db.execute('DROP TABLE journal_identity'); db.commit()
        self.assertEqual(self.packet()['machine']['record']['state'], 'NO_DATA')
