"""Fail-closed bridge for specialist recommendations; never dispatches work.

This adapts a recommendation into an inspectable proposal while reusing the
canonical task hash and host resource admission record. Hashes provide integrity,
not producer authentication. The current Junie selector has no authenticated
receipt/endpoint binding, so non-synthetic recommendations abstain.
"""
from datetime import datetime
import copy
import re

from .delegation import sha, validate_task
from .resource_admission import resources

RECOMMENDATION_SCHEMA = 'hexelion.skill-recommendation/1'
RECEIPT_SCHEMA = 'hexelion.skill-recommendation-receipt/1'
EVIDENCE_KEYS = {'state', 'origin', 'subject_ref', 'observed_at', 'evidence_ref'}
ENVELOPE_SCHEMA = 'hexelion.specialist-evidence-envelope/1'
ID = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,95}\Z')


def _digest(value):
    return type(value) is str and resources.HEX.fullmatch(value) is not None


def _evidence(item, subject, now, max_age):
    if type(item) is not dict or set(item) not in (
            EVIDENCE_KEYS, EVIDENCE_KEYS | {'risk_score'},
            EVIDENCE_KEYS | {'measured_score', 'independent_cases'}):
        return 'EVIDENCE_SCHEMA_INVALID'
    if (item['state'] != 'VERIFIED' or item['origin'] not in ('MEASURED', 'SYNTHETIC')
            or item['subject_ref'] != subject or not _digest(item['evidence_ref'])):
        return 'EVIDENCE_NOT_BOUND'
    age = resources.age_seconds(item['observed_at'], now)
    if age > max_age:
        return 'EVIDENCE_STALE'
    return None


def evaluate(task, recommendation, receipt, evidence, admission_record, *, now,
             min_quality=0.8, max_age_seconds=120):
    """Return a proposal only. Callers must use Session/S1 for any later execution.

    Expected evidence keys are endpoint, quality, security, context, provenance,
    hitl, and hitl_status. Positive fixture output is SIMULATED and never
    authorizes dispatch; the status is descriptive, not a real human signature.
    """
    task_ref = None
    specialist = None
    fallback_model = None

    def result(state, cause, *, model=None, node=None, source='NO_DATA'):
        value = {'schema': 'hexelion.specialist-proposal/1', 'state': state,
                 'cause': cause, 'task_ref': task_ref, 'specialist': specialist,
                 'model_digest': model, 'node': node, 'source': source,
                 'fallback_model': fallback_model,
                 'fallback_state': 'NO_DATA',
                 'fallback_cause': 'fallback_model_not_admitted',
                 'authority': 'none', 'dispatch_authorized': False,
                 'requires_human_authorization': True}
        value['decision_ref'] = sha(value)
        return value

    try:
        validate_task(task)
        task = copy.deepcopy(task)
        task_ref = sha(task)
        if type(now) is not datetime or now.utcoffset() is None:
            return result('NO_DATA', 'CLOCK_INVALID')
        if (type(max_age_seconds) is not int or not 0 <= max_age_seconds <= 3600
                or type(min_quality) not in (int, float) or not 0 <= min_quality <= 1
                or len(resources.encode([recommendation, receipt, evidence, admission_record])) > 65536):
            return result('REJECTED', 'INPUT_BOUND_OR_THRESHOLD_INVALID')
        if (type(recommendation) is not dict or set(recommendation) != {
                'schema', 'task_ref', 'skill_id', 'model_digest', 'node', 'backend',
                'quality_score', 'safety_gate', 'fallback_model', 'requires_hitl', 'origin'}
                or recommendation['schema'] != RECOMMENDATION_SCHEMA
                or recommendation['task_ref'] != sha(task)
                or recommendation['model_digest'] != task['model_version']
                or type(recommendation['skill_id']) is not str
                or type(recommendation['node']) is not str
                or type(recommendation['backend']) is not str
                or recommendation['origin'] not in ('MEASURED', 'SYNTHETIC')
                or type(recommendation['requires_hitl']) is not bool):
            return result('REJECTED', 'RECOMMENDATION_INVALID')
        specialist = recommendation['skill_id']
        fallback_model = recommendation['fallback_model']
        if (type(recommendation['quality_score']) not in (int, float)
                or not 0 <= recommendation['quality_score'] <= 1):
            return result('REJECTED', 'QUALITY_INVALID')
        body = {'schema': RECEIPT_SCHEMA, 'recommendation_ref': sha(recommendation),
                'task_ref': sha(task), 'origin': recommendation['origin']}
        if type(receipt) is not dict or set(receipt) != set(body) | {'receipt_ref'}:
            return result('NO_DATA', 'SELECTOR_RECEIPT_MISSING')
        if any(receipt.get(k) != v for k, v in body.items()) or receipt.get('receipt_ref') != sha(body):
            return result('REJECTED', 'SELECTOR_RECEIPT_MISMATCH')
        # Receipt hashes bind bytes only. The selector has no authenticated producer
        # verifier in the current contract; its real-world provenance is unavailable.
        if recommendation['origin'] != 'SYNTHETIC':
            return result('NO_DATA', 'selector_receipt_or_authenticated_producer_unavailable',
                          model=recommendation['model_digest'])
        if recommendation['quality_score'] < min_quality:
            return result('REJECTED', 'QUALITY_BELOW_THRESHOLD', model=recommendation['model_digest'])
        if recommendation['safety_gate'] != 'PASS':
            return result('REJECTED', 'SPECIALIST_SAFETY_NOT_PASSED', model=recommendation['model_digest'])
        if type(evidence) is not dict or set(evidence) != {
                'endpoint', 'quality', 'security', 'context', 'provenance', 'hitl', 'hitl_status'}:
            return result('NO_DATA', 'SPECIALIST_EVIDENCE_MISSING', model=recommendation['model_digest'])
        if evidence['hitl_status'] != 'APPROVED_FOR_PROPOSAL':
            return result('NO_DATA', 'HITL_NOT_APPROVED_FOR_PROPOSAL', model=recommendation['model_digest'])
        endpoint_subject = sha({'task_ref': sha(task), 'node': recommendation['node'],
                                'backend': recommendation['backend'],
                                'model_digest': recommendation['model_digest']})
        evidence_subjects = {'endpoint': endpoint_subject, 'quality': sha(recommendation),
                             'security': sha(task), 'context': sha(task),
                             'provenance': sha(recommendation), 'hitl': sha(task)}
        for key, subject in evidence_subjects.items():
            row = evidence[key]
            if key == 'quality' and type(row) is dict:
                score = row.get('measured_score')
                cases = row.get('independent_cases')
                if (type(score) not in (int, float) or score != recommendation['quality_score']
                        or type(cases) is not int or cases < 1):
                    return result('REJECTED', 'QUALITY_MEASUREMENT_INVALID', model=recommendation['model_digest'])
                row = {k: v for k, v in row.items() if k not in ('measured_score', 'independent_cases')}
            if key == 'security' and type(row) is dict:
                risk = row.get('risk_score')
                if type(risk) not in (int, float) or not 0 <= risk <= 1:
                    return result('REJECTED', 'SECURITY_RISK_INVALID', model=recommendation['model_digest'])
                if risk > 0.2:
                    return result('REJECTED', 'SECURITY_RISK_ABOVE_THRESHOLD', model=recommendation['model_digest'])
                row = {k: v for k, v in row.items() if k != 'risk_score'}
            cause = _evidence(row, subject, now, max_age_seconds)
            if cause:
                return result('NO_DATA' if cause in ('EVIDENCE_STALE',) else 'REJECTED',
                              key.upper() + '_' + cause, model=recommendation['model_digest'])
        if evidence['endpoint']['origin'] != 'SYNTHETIC':
            return result('NO_DATA', 'endpoint_accreditation_unavailable', model=recommendation['model_digest'])
        if recommendation['requires_hitl'] is not True:
            return result('REJECTED', 'HITL_REQUIREMENT_DROPPED', model=recommendation['model_digest'])
        if type(admission_record) is not dict:
            return result('NO_DATA', 'resource_admission_missing', model=recommendation['model_digest'])
        admission = copy.deepcopy(admission_record)
        ref = admission.pop('admission_ref', None)
        if ref != sha(admission) or admission.get('task_ref') != sha(task):
            return result('REJECTED', 'RESOURCE_ADMISSION_BINDING_INVALID', model=recommendation['model_digest'])
        choice = admission.get('choice') or {}
        if admission.get('state') != 'VERIFIED' or admission.get('promotion') != 'NOT_AUTHORIZED':
            return result('NO_DATA', 'resource_not_admitted', model=recommendation['model_digest'])
        if choice.get('node') != recommendation['node'] or choice.get('backend') != recommendation['backend']:
            return result('REJECTED', 'RESOURCE_TARGET_MISMATCH', model=recommendation['model_digest'])
        if choice.get('model_version') != recommendation['model_digest']:
            return result('REJECTED', 'RESOURCE_MODEL_MISMATCH', model=recommendation['model_digest'])
        return result('SIMULATED_PROPOSAL', 'SYNTHETIC_FIXTURE_ONLY', model=recommendation['model_digest'],
                      node=recommendation['node'], source='SIMULATED')
    except Exception:
        return result('NO_DATA', 'contract_validation_unavailable')


def make_integrity_receipt(recommendation, task):
    """Fixture/helper for tests and offline examples; not an authenticity proof."""
    body = {'schema': RECEIPT_SCHEMA, 'recommendation_ref': sha(recommendation),
            'task_ref': sha(task), 'origin': recommendation.get('origin')}
    return {**body, 'receipt_ref': sha(body)}


def validate_evidence_envelope(task, envelope, admission_record, *, now,
                               min_quality=0.8, max_age_seconds=120):
    """Validate a closed selector evidence envelope; never authenticates or dispatches.

    MEASURED envelopes remain NO_DATA until a separately governed producer trust
    source/verifier is connected. Synthetic envelopes can exercise structure only.
    """
    def done(state, cause, *, source='NO_DATA', producer=None, model=None, node=None,
             skill=None, quality=None, cases=None, benchmark=None):
        out = {'schema': 'hexelion.specialist-proposal/1', 'state': state,
               'cause': cause, 'source': source, 'producer_ref': producer,
               'model_digest': model, 'node': node, 'skill_id': skill,
               'quality_score': quality, 'independent_cases': cases,
               'benchmark_ref': benchmark, 'task_ref': sha(task) if type(task) is dict else None,
               'authority': 'none', 'dispatch_authorized': False,
               'requires_human_authorization': True}
        out['decision_ref'] = sha(out)
        return out

    try:
        validate_task(task)
        if (type(now) is not datetime or now.utcoffset() is None
                or type(max_age_seconds) is not int or not 0 <= max_age_seconds <= 3600
                or type(min_quality) not in (int, float) or not 0 <= min_quality <= 1
                or len(resources.encode(envelope)) > 65536):
            return done('REJECTED', 'INPUT_BOUND_OR_CLOCK_INVALID')
        keys = {'schema', 'origin', 'producer', 'model', 'endpoint', 'task_ref',
                'skill', 'benchmark', 'admission_ref', 'hitl', 'signature', 'envelope_sha256'}
        if type(envelope) is not dict or set(envelope) != keys or envelope['schema'] != ENVELOPE_SCHEMA:
            return done('REJECTED', 'ENVELOPE_SCHEMA_INVALID')
        body = {k: v for k, v in envelope.items() if k != 'envelope_sha256'}
        if not _digest(envelope['envelope_sha256']) or envelope['envelope_sha256'] != sha(body):
            return done('REJECTED', 'ENVELOPE_INTEGRITY_MISMATCH')
        if envelope['origin'] not in ('MEASURED', 'SYNTHETIC') or envelope['task_ref'] != sha(task):
            return done('REJECTED', 'TASK_OR_ORIGIN_MISMATCH')
        producer = envelope['producer']; model = envelope['model']; endpoint = envelope['endpoint']
        skill = envelope['skill']; benchmark = envelope['benchmark']; hitl = envelope['hitl']
        if (type(producer) is not dict or set(producer) != {'producer_id', 'source_ref', 'revision', 'key_ref'}
                or type(producer['producer_id']) is not str or not ID.fullmatch(producer['producer_id'])
                or not _digest(producer['source_ref']) or not _digest(producer['revision'])
                or not _digest(producer['key_ref'])):
            return done('REJECTED', 'PRODUCER_IDENTITY_INVALID')
        if (type(model) is not dict or set(model) != {'model_id', 'digest', 'version', 'architecture'}
                or type(model['model_id']) is not str or not ID.fullmatch(model['model_id'])
                or not _digest(model['digest']) or model['digest'] != task['model_version']
                or type(model['version']) is not str or not ID.fullmatch(model['version'])
                or type(model['architecture']) is not str or not ID.fullmatch(model['architecture'])):
            return done('REJECTED', 'MODEL_IDENTITY_MISMATCH', producer=producer.get('source_ref') if type(producer) is dict else None)
        if (type(endpoint) is not dict or set(endpoint) != {
                'node_id', 'backend', 'endpoint_ref', 'model_digest', 'state', 'observed_at'}
                or type(endpoint['node_id']) is not str or not ID.fullmatch(endpoint['node_id'])
                or type(endpoint['backend']) is not str or not ID.fullmatch(endpoint['backend'])
                or not _digest(endpoint['endpoint_ref']) or endpoint['model_digest'] != model['digest']
                or endpoint['state'] != 'OBSERVED'):
            return done('REJECTED', 'ENDPOINT_IDENTITY_INVALID', producer=producer['source_ref'], model=model['digest'])
        endpoint_age = resources.age_seconds(endpoint['observed_at'], now)
        if endpoint_age > max_age_seconds:
            return done('NO_DATA', 'ENDPOINT_EVIDENCE_STALE', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'])
        if (type(skill) is not dict or set(skill) != {
                'skill_id', 'quality_score', 'safety_gate', 'security_risk',
                'independent_cases', 'evidence_refs'}
                or type(skill['skill_id']) is not str or not ID.fullmatch(skill['skill_id'])
                or type(skill['quality_score']) not in (int, float) or not 0 <= skill['quality_score'] <= 1
                or skill['quality_score'] < min_quality
                or skill['safety_gate'] is not True
                or type(skill['security_risk']) not in (int, float)
                or not 0 <= skill['security_risk'] <= 0.2
                or type(skill['independent_cases']) is not int
                or skill['independent_cases'] < 1 or type(skill['evidence_refs']) is not list
                or not skill['evidence_refs'] or len(skill['evidence_refs']) > 32
                or any(not _digest(ref) for ref in skill['evidence_refs'])):
            return done('REJECTED', 'SKILL_EVIDENCE_INVALID', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'])
        if (type(benchmark) is not dict or set(benchmark) != {
                'benchmark_id', 'benchmark_sha256', 'receipt_sha256', 'observed_at', 'expires_at',
                'quality_score', 'independent_cases'}
                or type(benchmark['benchmark_id']) is not str or not ID.fullmatch(benchmark['benchmark_id'])
                or not _digest(benchmark['benchmark_sha256']) or not _digest(benchmark['receipt_sha256'])
                or benchmark['quality_score'] != skill['quality_score']
                or benchmark['independent_cases'] != skill['independent_cases']
                or benchmark['receipt_sha256'] not in skill['evidence_refs']):
            return done('REJECTED', 'BENCHMARK_RECEIPT_INVALID', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'], skill=skill['skill_id'], quality=skill['quality_score'], cases=skill['independent_cases'])
        measured_age = resources.age_seconds(benchmark['observed_at'], now)
        try:
            expires = datetime.fromisoformat(benchmark['expires_at'].replace('Z', '+00:00'))
        except (AttributeError, TypeError, ValueError):
            return done('REJECTED', 'BENCHMARK_EXPIRY_INVALID', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'], skill=skill['skill_id'], quality=skill['quality_score'], cases=skill['independent_cases'], benchmark=benchmark['receipt_sha256'])
        if expires.utcoffset() is None:
            return done('REJECTED', 'BENCHMARK_EXPIRY_INVALID', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'], skill=skill['skill_id'], quality=skill['quality_score'], cases=skill['independent_cases'], benchmark=benchmark['receipt_sha256'])
        if measured_age > max_age_seconds or expires <= now:
            return done('NO_DATA', 'BENCHMARK_EVIDENCE_EXPIRED', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'], skill=skill['skill_id'], quality=skill['quality_score'], cases=skill['independent_cases'], benchmark=benchmark['receipt_sha256'])
        if type(admission_record) is not dict:
            return done('NO_DATA', 'RESOURCE_ADMISSION_MISSING', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'], skill=skill['skill_id'], quality=skill['quality_score'], cases=skill['independent_cases'], benchmark=benchmark['receipt_sha256'])
        admission = copy.deepcopy(admission_record); admission_ref = admission.pop('admission_ref', None)
        if (admission_ref != sha(admission) or admission_ref != envelope['admission_ref']
                or admission.get('task_ref') != sha(task) or admission.get('state') != 'VERIFIED'
                or admission.get('promotion') != 'NOT_AUTHORIZED'):
            return done('REJECTED', 'RESOURCE_ADMISSION_INVALID', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'], skill=skill['skill_id'], quality=skill['quality_score'], cases=skill['independent_cases'], benchmark=benchmark['receipt_sha256'])
        choice = admission.get('choice') or {}
        if (choice.get('node') != endpoint['node_id'] or choice.get('backend') != endpoint['backend']
                or choice.get('model_version') != model['digest']):
            return done('REJECTED', 'RESOURCE_TARGET_MISMATCH', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'], skill=skill['skill_id'], quality=skill['quality_score'], cases=skill['independent_cases'], benchmark=benchmark['receipt_sha256'])
        if resources.age_seconds(admission.get('observed_at'), now) > max_age_seconds:
            return done('NO_DATA', 'RESOURCE_ADMISSION_STALE', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'], skill=skill['skill_id'], quality=skill['quality_score'], cases=skill['independent_cases'], benchmark=benchmark['receipt_sha256'])
        if type(hitl) is not dict or set(hitl) != {'status', 'decision_ref'} or hitl['status'] != 'APPROVED_FOR_PROPOSAL' or not _digest(hitl['decision_ref']):
            return done('NO_DATA', 'HUMAN_REVIEW_MISSING', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'], skill=skill['skill_id'], quality=skill['quality_score'], cases=skill['independent_cases'], benchmark=benchmark['receipt_sha256'])
        signature = envelope['signature']
        if envelope['origin'] == 'MEASURED':
            if (type(signature) is not dict or set(signature) != {'algorithm', 'key_ref', 'value'}
                    or signature.get('algorithm') != 'Ed25519' or signature.get('key_ref') != producer['key_ref']
                    or type(signature.get('value')) is not str or not re.fullmatch(r'[0-9a-f]{128}', signature['value'])):
                return done('REJECTED', 'SIGNATURE_ENVELOPE_INVALID', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'], skill=skill['skill_id'], quality=skill['quality_score'], cases=skill['independent_cases'], benchmark=benchmark['receipt_sha256'])
            # No trusted producer root/verifier is present in LAB. Never treat an
            # included key reference or a valid-looking signature as authentication.
            return done('NO_DATA', 'authenticated_producer_trust_anchor_unavailable', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'], skill=skill['skill_id'], quality=skill['quality_score'], cases=skill['independent_cases'], benchmark=benchmark['receipt_sha256'])
        if signature != {'algorithm': 'NONE', 'key_ref': None, 'value': None}:
            return done('REJECTED', 'SYNTHETIC_SIGNATURE_MUST_BE_ABSENT', producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'], skill=skill['skill_id'], quality=skill['quality_score'], cases=skill['independent_cases'], benchmark=benchmark['receipt_sha256'])
        return done('SIMULATED_PROPOSAL', 'SYNTHETIC_ENVELOPE_ONLY', source='SIMULATED',
                    producer=producer['source_ref'], model=model['digest'], node=endpoint['node_id'],
                    skill=skill['skill_id'], quality=skill['quality_score'],
                    cases=skill['independent_cases'], benchmark=benchmark['receipt_sha256'])
    except resources.EvidenceTimeError:
        return done('NO_DATA', 'evidence_time_invalid_or_future')
    except Exception:
        return done('NO_DATA', 'envelope_validation_unavailable')
