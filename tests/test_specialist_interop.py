"""Pure interoperability controls; all positive evidence is synthetic."""
import copy
import hashlib
import unittest
from datetime import datetime, timezone

from meta_harness.delegation import sha
from meta_harness.delegation import Session, TokenBudget
from meta_harness.specialist_interop import (
    ENVELOPE_SCHEMA, RECOMMENDATION_SCHEMA, evaluate,
    make_integrity_receipt, validate_evidence_envelope,
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


def envelope(t=None, admission=None):
    t = t or task(); admission = admission or admitted(t)
    benchmark_ref = '9' * 64
    value = {'schema': ENVELOPE_SCHEMA, 'origin': 'SYNTHETIC',
        'producer': {'producer_id': 'junie-model-lab', 'source_ref': '1' * 64,
                     'revision': '2' * 64, 'key_ref': '3' * 64},
        'model': {'model_id': 'specialist-model', 'digest': t['model_version'],
                  'version': 'v1', 'architecture': 'qwen-test'},
        'endpoint': {'node_id': 'node-a', 'backend': 'default', 'endpoint_ref': '4' * 64,
                     'model_digest': t['model_version'], 'state': 'OBSERVED',
                     'observed_at': '2026-11-16T11:59:00Z'},
        'task_ref': sha(t),
        'skill': {'skill_id': 'sort', 'quality_score': 0.94, 'safety_gate': True,
                  'security_risk': 0.05,
                  'independent_cases': 20, 'evidence_refs': [benchmark_ref]},
        'benchmark': {'benchmark_id': 'bench-r4', 'benchmark_sha256': '5' * 64,
                      'receipt_sha256': benchmark_ref, 'observed_at': '2026-11-16T11:59:00Z',
                      'expires_at': '2026-11-16T12:05:00Z', 'quality_score': 0.94,
                      'independent_cases': 20},
        'admission_ref': admission['admission_ref'],
        'hitl': {'status': 'APPROVED_FOR_PROPOSAL', 'decision_ref': '6' * 64},
        'signature': {'algorithm': 'NONE', 'key_ref': None, 'value': None}}
    value['envelope_sha256'] = sha(value)
    return value


_DEFAULT = object()


def verify_envelope(t=None, e=None, a=_DEFAULT, now=NOW):
    t = t or task(); a = admitted(t) if a is _DEFAULT else a
    e = envelope(t, a) if e is None else e
    return validate_evidence_envelope(t, e, a, now=now)


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

    def test_closed_synthetic_selector_envelope_is_inspectable_but_never_authorizes(self):
        value = verify_envelope()
        self.assertEqual(value['state'], 'SIMULATED_PROPOSAL')
        self.assertEqual(value['source'], 'SIMULATED')
        self.assertEqual(value['benchmark_ref'], '9' * 64)
        self.assertEqual(value['independent_cases'], 20)
        self.assertEqual(value['authority'], 'none')
        self.assertFalse(value['dispatch_authorized'])
        self.assertEqual(value, verify_envelope())

    def test_real_signed_shape_and_unknown_producer_abstain_without_trust_anchor(self):
        e = envelope(); e['origin'] = 'MEASURED'
        e['signature'] = {'algorithm': 'Ed25519', 'key_ref': e['producer']['key_ref'], 'value': 'a' * 128}
        e['envelope_sha256'] = sha({k:v for k,v in e.items() if k!='envelope_sha256'})
        value = verify_envelope(e=e)
        self.assertEqual((value['state'], value['cause']),
                         ('NO_DATA', 'authenticated_producer_trust_anchor_unavailable'))
        self.assertFalse(value['dispatch_authorized'])
        e['producer']['producer_id'] = 'unregistered-lab-producer'
        e['envelope_sha256'] = sha({k:v for k,v in e.items() if k!='envelope_sha256'})
        unknown = verify_envelope(e=e)
        self.assertEqual(unknown['cause'], 'authenticated_producer_trust_anchor_unavailable')
        self.assertFalse(unknown['dispatch_authorized'])

    def test_signature_corruption_is_rejected_and_signature_never_becomes_trust(self):
        e = envelope(); e['origin'] = 'MEASURED'
        e['signature'] = {'algorithm': 'Ed25519', 'key_ref': e['producer']['key_ref'], 'value': 'a' * 127}
        e['envelope_sha256'] = sha({k:v for k,v in e.items() if k!='envelope_sha256'})
        malformed = verify_envelope(e=e)
        self.assertEqual(malformed['cause'], 'SIGNATURE_ENVELOPE_INVALID')
        self.assertFalse(malformed['dispatch_authorized'])
        e = envelope(); e['signature'] = {'algorithm': 'Ed25519', 'key_ref': '3' * 64, 'value': 'a' * 128}
        tampered = verify_envelope(e=e)
        self.assertEqual(tampered['cause'], 'ENVELOPE_INTEGRITY_MISMATCH')
        self.assertFalse(tampered['dispatch_authorized'])
        # Recomputing an unsigned integrity hash cannot authenticate a forged signature.
        e['origin'] = 'MEASURED'; e['envelope_sha256'] = sha({k:v for k,v in e.items() if k!='envelope_sha256'})
        untrusted = verify_envelope(e=e)
        self.assertEqual(untrusted['cause'], 'authenticated_producer_trust_anchor_unavailable')
        self.assertFalse(untrusted['dispatch_authorized'])

    def test_envelope_rejects_task_model_endpoint_score_and_receipt_mutations(self):
        e = envelope(); e['task_ref'] = '0' * 64
        self.assertEqual(verify_envelope(e=e)['cause'], 'ENVELOPE_INTEGRITY_MISMATCH')
        e['envelope_sha256'] = sha({k:v for k,v in e.items() if k!='envelope_sha256'})
        self.assertEqual(verify_envelope(e=e)['cause'], 'TASK_OR_ORIGIN_MISMATCH')
        e = envelope(); e['model']['digest'] = '0' * 64; e['envelope_sha256'] = sha({k:v for k,v in e.items() if k!='envelope_sha256'})
        self.assertEqual(verify_envelope(e=e)['cause'], 'MODEL_IDENTITY_MISMATCH')
        e = envelope(); e['endpoint']['node_id'] = 'node-b'; e['envelope_sha256'] = sha({k:v for k,v in e.items() if k!='envelope_sha256'})
        self.assertEqual(verify_envelope(e=e)['cause'], 'RESOURCE_TARGET_MISMATCH')
        e = envelope(); e['skill']['quality_score'] = 0.99; e['envelope_sha256'] = sha({k:v for k,v in e.items() if k!='envelope_sha256'})
        self.assertEqual(verify_envelope(e=e)['cause'], 'BENCHMARK_RECEIPT_INVALID')
        e = envelope(); e['benchmark']['receipt_sha256'] = '0' * 64; e['envelope_sha256'] = sha({k:v for k,v in e.items() if k!='envelope_sha256'})
        self.assertEqual(verify_envelope(e=e)['cause'], 'BENCHMARK_RECEIPT_INVALID')

    def test_expired_evidence_missing_admission_and_human_review_do_not_propose(self):
        e = envelope(); e['benchmark']['expires_at'] = '2026-11-16T11:00:00Z'
        e['envelope_sha256'] = sha({k:v for k,v in e.items() if k!='envelope_sha256'})
        self.assertEqual(verify_envelope(e=e)['cause'], 'BENCHMARK_EVIDENCE_EXPIRED')
        self.assertEqual(verify_envelope(a=None)['cause'], 'RESOURCE_ADMISSION_MISSING')
        e = envelope(); e['hitl']['status'] = 'PENDING'; e['envelope_sha256'] = sha({k:v for k,v in e.items() if k!='envelope_sha256'})
        value = verify_envelope(e=e)
        self.assertEqual(value['cause'], 'HUMAN_REVIEW_MISSING')
        self.assertFalse(value['dispatch_authorized'])

    def test_risk_above_limit_is_rejected(self):
        e = envelope(); e['skill']['security_risk'] = 0.9
        e['envelope_sha256'] = sha({k:v for k,v in e.items() if k!='envelope_sha256'})
        value = verify_envelope(e=e)
        self.assertEqual(value['cause'], 'SKILL_EVIDENCE_INVALID')
        self.assertFalse(value['dispatch_authorized'])


if __name__ == '__main__':
    unittest.main()
