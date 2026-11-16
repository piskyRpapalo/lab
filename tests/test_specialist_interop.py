"""Pure interoperability controls; all positive evidence is synthetic."""
import copy
import hashlib
import unittest
from datetime import datetime, timezone

from meta_harness.delegation import sha
from meta_harness.delegation import Session, TokenBudget
from meta_harness.specialist_interop import (
    RECOMMENDATION_SCHEMA, evaluate, make_integrity_receipt,
)
from meta_harness import cli
from meta_harness.reuse import PATHS, ROOT

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)


def task():
    return {'schema': 'preceptoros.meta-task/1', 'task_id': 'sort', 'run_id': 'run-one',
            'specialist': 'serion-sort', 'source': 'local-model', 'model_version': 'a' * 64,
            'input_sha256': 'b' * 64, 'max_tokens': 64, 'timeout_ms': 1000,
            'depth': 1, 'privacy': 'LOCAL_ONLY', 'transport': 'ollama_loopback'}


def recommendation(t):
    return {'schema': RECOMMENDATION_SCHEMA, 'task_ref': sha(t), 'skill_id': 'sort',
            'model_digest': t['model_version'], 'node': 'node-a', 'backend': 'default',
            'quality_score': 0.94, 'safety_gate': 'PASS', 'fallback_model': None,
            'requires_hitl': True, 'origin': 'SYNTHETIC'}


def evidence(t=None, r=None):
    def item(subject):
        return {'state': 'VERIFIED', 'origin': 'SYNTHETIC', 'subject_ref': subject,
                'observed_at': '2026-11-16T11:59:00Z', 'evidence_ref': 'c' * 64}
    t = t or task(); r = r or recommendation(t)
    endpoint = sha({'task_ref': sha(t), 'node': r['node'], 'backend': r['backend'],
                    'model_digest': r['model_digest']})
    security = item(sha(t)); security['risk_score'] = 0.05
    quality = item(sha(r)); quality['measured_score'] = r['quality_score']; quality['independent_cases'] = 20
    return {'endpoint': item(endpoint), 'quality': quality, 'security': security,
            'context': item(sha(t)), 'provenance': item(sha(r)), 'hitl': item(sha(t)),
            'hitl_status': 'APPROVED_FOR_PROPOSAL'}


def admitted(t=None):
    t = t or task()
    value = {'schema': 'preceptoros.lab.node-metadata/1', 'kind': 'admission-evaluation',
             'state': 'VERIFIED', 'cause': 'RESOURCE_CHECKS_AND_HOST_LEASE_WITNESSED',
             'scope': 'host_witnessed_resource_checks_not_execution_or_permission',
             'task_ref': sha(t), 'choice': {'node': 'node-a', 'backend': 'default',
             'model_version': t['model_version'], 'source_ref': 'd' * 64, 'profile_ref': 'e' * 64},
             'lease_ref': 'f' * 64, 'observed_at': '2026-11-16T11:59:00+00:00',
             'promotion': 'NOT_AUTHORIZED'}
    value['admission_ref'] = sha(value)
    return value


_DEFAULT = object()


def run(t=None, r=None, ev=None, admission=_DEFAULT, now=NOW, receipt=None):
    t = t or task(); r = r or recommendation(t)
    return evaluate(t, r, receipt or make_integrity_receipt(r, t),
                    evidence(t, r) if ev is None else ev,
                    admitted(t) if admission is _DEFAULT else admission,
                    now=now)


class SpecialistInteropTests(unittest.TestCase):
    def test_synthetic_proposal_is_deterministic_and_never_dispatchable(self):
        decision = run()
        self.assertEqual(decision['state'], 'SIMULATED_PROPOSAL')
        self.assertEqual(decision['source'], 'SIMULATED')
        self.assertEqual(decision['authority'], 'none')
        self.assertFalse(decision['dispatch_authorized'])
        self.assertTrue(decision['requires_human_authorization'])
        self.assertEqual(decision, run())

    def test_disqualified_candidate_cannot_produce_proposal(self):
        r = recommendation(task()); r['quality_score'] = 0.2
        self.assertEqual(run(r=r)['cause'], 'QUALITY_BELOW_THRESHOLD')
        r = recommendation(task()); r['safety_gate'] = 'FAIL'
        self.assertEqual(run(r=r)['cause'], 'SPECIALIST_SAFETY_NOT_PASSED')

    def test_missing_or_tampered_selector_receipt_abstains_or_rejects(self):
        t, r = task(), recommendation(task())
        self.assertEqual(evaluate(t, r, None, evidence(), admitted(t), now=NOW)['cause'],
                         'SELECTOR_RECEIPT_MISSING')
        receipt = make_integrity_receipt(r, t); receipt['recommendation_ref'] = '0' * 64
        self.assertEqual(run(r=r, receipt=receipt)['cause'], 'SELECTOR_RECEIPT_MISMATCH')

    def test_recommendation_bound_to_another_task_is_rejected(self):
        t, r = task(), recommendation(task()); r['task_ref'] = 'f' * 64
        self.assertEqual(run(t=t, r=r)['cause'], 'RECOMMENDATION_INVALID')

    def test_real_declared_selector_without_authenticated_producer_is_no_data(self):
        t, r = task(), recommendation(task()); r['origin'] = 'MEASURED'
        receipt = make_integrity_receipt(r, t)
        self.assertEqual(run(t=t, r=r, receipt=receipt)['state'], 'NO_DATA')
        self.assertEqual(run(t=t, r=r, receipt=receipt)['cause'],
                         'selector_receipt_or_authenticated_producer_unavailable')

    def test_missing_resource_and_unadmitted_resource_never_propose(self):
        self.assertEqual(run(admission=None)['cause'], 'resource_admission_missing')
        row = admitted(); row['state'] = 'NO_DATA'; row['admission_ref'] = sha({k:v for k,v in row.items() if k!='admission_ref'})
        self.assertEqual(run(admission=row)['cause'], 'resource_not_admitted')

    def test_changed_task_or_target_in_admission_is_rejected(self):
        row = admitted(); row['task_ref'] = '0' * 64
        row['admission_ref'] = sha({k:v for k,v in row.items() if k!='admission_ref'})
        self.assertEqual(run(admission=row)['cause'], 'RESOURCE_ADMISSION_BINDING_INVALID')
        row = admitted(); row['choice']['node'] = 'node-b'
        row['admission_ref'] = sha({k:v for k,v in row.items() if k!='admission_ref'})
        self.assertEqual(run(admission=row)['cause'], 'RESOURCE_TARGET_MISMATCH')

    def test_expired_context_evidence_and_unapproved_hitl_do_not_propose(self):
        ev = evidence(); ev['context']['observed_at'] = '2026-11-16T11:00:00Z'
        self.assertEqual(run(ev=ev)['cause'], 'CONTEXT_EVIDENCE_STALE')
        ev = evidence(); ev['hitl_status'] = 'PENDING'
        self.assertEqual(run(ev=ev)['cause'], 'HITL_NOT_APPROVED_FOR_PROPOSAL')

    def test_security_risk_and_missing_session_grant_never_dispatch(self):
        ev = evidence(); ev['security']['risk_score'] = 0.9
        self.assertEqual(run(ev=ev)['cause'], 'SECURITY_RISK_ABOVE_THRESHOLD')
        calls = []
        session = Session(lambda _task: None, TokenBudget(64))
        receipt = session.execute(task(), lambda *_: calls.append('dispatch'),
                                  observed_at='2026-11-16T12:00:00Z')
        self.assertEqual(receipt['failure_class'], 'PERMISSION')
        self.assertEqual(calls, [])

    def test_proposal_distribution_is_stably_sorted_and_not_dispatch(self):
        outputs = []
        for run_id in ('run-z', 'run-a'):
            t = {**task(), 'run_id': run_id}
            r = recommendation(t)
            outputs.append(run(t=t, r=r))
        ordered = sorted(outputs, key=lambda item: item['task_ref'])
        self.assertEqual([item['task_ref'] for item in ordered], sorted(item['task_ref'] for item in outputs))
        self.assertTrue(all(item['state'] == 'SIMULATED_PROPOSAL' for item in ordered))
        self.assertTrue(all(not item['dispatch_authorized'] for item in ordered))

    def test_provenance_report_references_full_manifest_without_embedding_it(self):
        value = cli.provenance()
        paths = sorted((ROOT / 'meta_harness').glob('*.py')) + [
            ROOT / 'benchmarks/fixtures/meta-harness-public-v1.json',
            cli.throughput.FIXTURE]
        paths += [ROOT / path for path in PATHS.values()]
        hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in paths}
        self.assertEqual(value['source_sha256'], sha(hashes))
        self.assertEqual(value['source_file_count'], len(hashes))
        self.assertNotIn('files', value)


if __name__ == '__main__':
    unittest.main()
