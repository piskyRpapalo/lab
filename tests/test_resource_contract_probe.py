import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'bin'))
import resource_contract_probe as p
import resource_decision as r
import resource_decision_probe as fixtures


class RealContracts(unittest.TestCase):
    def test_actual_source_and_validators_abstain_without_profiles(self):
        report = p.report()
        self.assertEqual(report['model_calls'], 0)
        expected = {'no_profile': 'TASK_RESOURCE_EVIDENCE_MISSING',
                    'tampered': 'PROJECTION_NOT_WITNESSED', 'expired': 'EVIDENCE_STALE',
                    'malicious': 'TASK_CONTRACT_INVALID'}
        for key, cause in expected.items():
            self.assertEqual(report[key]['cause'], cause)
            self.assertFalse(report[key]['dispatch_authorized'])
        self.assertEqual(report, p.report())

    def test_missing_observation_is_unavailable_not_invalid_clock(self):
        task, packets, profiles, policy = fixtures.fixture()
        packets[0]['record'].update(state='NO_DATA', observed_at=None)
        host = fixtures.host_for(task, packets, profiles)
        self.assertEqual(r.decide(task, packets, profiles, policy, host=host,
                                 now=fixtures.NOW)['cause'], 'NODE_UNAVAILABLE')
