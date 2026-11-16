"""Fail-closed bridge for specialist recommendations; never dispatches work.

This adapts a recommendation into an inspectable proposal while reusing the
canonical task hash and host resource admission record. Hashes provide integrity,
not producer authentication. The current Junie selector has no authenticated
receipt/endpoint binding, so non-synthetic recommendations abstain.
"""
from datetime import datetime
import copy

from .delegation import sha, validate_task
from .resource_admission import resources

RECOMMENDATION_SCHEMA = 'hexelion.skill-recommendation/1'
RECEIPT_SCHEMA = 'hexelion.skill-recommendation-receipt/1'
EVIDENCE_KEYS = {'state', 'origin', 'subject_ref', 'observed_at', 'evidence_ref'}


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
