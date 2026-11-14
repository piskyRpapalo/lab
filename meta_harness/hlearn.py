"""H-LEARN P0: compose existing proposals/admission without an execution path."""
from datetime import datetime
from typing import Callable, Optional, TypedDict
from .delegation import Failure, check_grant, sha, validate_task, verify
from .resource_admission import AdmissionGate, resources
from . import wake_recovery


class Receipt(TypedDict):
    schema: str
    state: str
    cause: str
    task_ref: Optional[str]
    decision_ref: Optional[str]
    admission_ref: Optional[str]
    recovery_ref: Optional[str]
    prior_ref: Optional[str]
    reservation: str
    dispatch_authorized: bool
    physical_actions: int
    promotion: str
    receipt_ref: str


class Trace(TypedDict):
    receipt: Receipt
    decision: Optional[dict]
    admission: Optional[dict]
    recovery: Optional[wake_recovery.RecoveryProposal]


def evaluate(task: dict, *, packets: list, profiles: list, policy: dict, host,
             gate: AdmissionGate, grant: dict, worker: Callable, now: datetime,
             wake_inputs: Optional[dict] = None, prior: Optional[dict] = None,
             attests_prior: Optional[Callable] = None,
             cancelled: Callable[[], bool] = lambda: False) -> Trace:
    """Trusted host inputs only; worker is a route identity, NEVER invoked here.

    Original resource decision and AdmissionGate record are returned unchanged.
    An optional native Session receipt needs its host's attestation, not only a hash.
    No journal claim, token/resource reservation or execution is requested. A future
    effect must use existing Session/ExecutionJournal plus final host authorization;
    this receipt is not a dispatch token or a device-level atomic lock.
    """
    task_ref = None
    decision = admission = recovery = None
    prior_ref = None
    def finish(state, cause):
        row = dict(schema='preceptoros.hlearn-proposal/0', state=state, cause=cause,
                   task_ref=task_ref, decision_ref=decision['decision_ref'] if decision else None,
                   admission_ref=admission['admission_ref'] if admission else None,
                   recovery_ref=recovery['receipt']['receipt_ref'] if recovery else None,
                   prior_ref=prior_ref, reservation='NOT_REQUESTED', dispatch_authorized=False,
                   physical_actions=0, promotion='NOT_AUTHORIZED')
        row['receipt_ref'] = sha(row)
        if len(resources.encode(row)) >= 1024:
            raise ValueError('receipt_bound')
        return dict(receipt=row, decision=decision, admission=admission, recovery=recovery)
    try:
        validate_task(task)
        task_ref = sha(task)
        if (type(gate) is not AdmissionGate or not callable(worker) or not callable(cancelled)
                or type(packets) is not list or type(profiles) is not list
                or len(resources.encode([task,packets,profiles,policy,prior])) > 262144):
            return finish('ABSTAIN','INPUT_OR_HOST_CONTRACT_INVALID')
        if prior is not None:
            if (type(prior) is not dict or not verify(prior) or prior.get('task_sha256') != task_ref
                    or prior.get('run_id') != task['run_id'] or not callable(attests_prior)
                    or attests_prior(prior,task) is not True):
                return finish('ABSTAIN','PRIOR_RECEIPT_NOT_HOST_WITNESSED')
            prior_ref = sha(prior)
            return finish('ABSTAIN','PREVIOUS_OUTCOME_UNKNOWN' if prior['outcome']=='UNKNOWN'
                          else 'PRIOR_RECEIPT_SESSION_REPLAY_ONLY')
        decision = resources.decide(task,packets,profiles,policy,host=host,now=now,cancelled=cancelled)
        if decision['cause'] == 'CANCELLED':
            return finish('CANCELLED','CANCELLED')
        if decision['cause'] not in ('TASK_AND_RESOURCES_WITNESSED','PRODUCTION_ADMISSION_NOT_CONNECTED'):
            return finish('ABSTAIN',decision['cause'])
        # Canonical grant validator: no parallel permission rules or generated grant.
        try:
            check_grant(grant,task,gate.clock())
        except Failure as error:
            return finish('ABSTAIN','GRANT_'+error.category)
        admitted = gate(task,grant,worker,cancelled)
        admission = gate.record(task)
        if admitted is not True or admission is None:
            return finish('ABSTAIN',admission['cause'] if admission else 'ADMISSION_EVIDENCE_MISSING')
        choice = admission['choice']
        if (choice.get('model_version') != task['model_version']
                or not any(p.get('profile_ref') == choice.get('profile_ref')
                    and p.get('node') == choice.get('node') and p.get('backend') == choice.get('backend')
                    and p.get('source_ref') == choice.get('source_ref')
                    and p.get('model_version') == task['model_version']
                    and p.get('task_profile_ref') == resources.profile_key(task) for p in profiles)
                or not any(p.get('record',{}).get('node') == choice.get('node')
                    and p.get('record',{}).get('backend') == choice.get('backend')
                    and p.get('record',{}).get('source_ref') == choice.get('source_ref') for p in packets)):
            return finish('ABSTAIN','ADMISSION_RESOURCE_BINDING_MISMATCH')
        if wake_inputs is not None:
            required = {'intent','observations','capability','ledger','verify_observation','verify_capability'}
            allowed = required | {'after','post'}
            if (type(wake_inputs) is not dict or not required <= set(wake_inputs)
                    or not set(wake_inputs) <= allowed):
                return finish('ABSTAIN','RECOVERY_BOUNDARY_INVALID')
            recovery = wake_recovery.plan(task, **wake_inputs, now=now,
                                          admission=gate.record,cancelled=cancelled() is True)
            return finish(recovery['receipt']['state'],recovery['receipt']['cause'])
        # Measured resource proposal remains ABSTAIN even if host checks passed.
        # Admission is evidence, never production execution authority.
        return finish(decision['state'],decision['cause'])
    except resources.EvidenceTimeError:
        return finish('ABSTAIN','CLOCK_INVALID_OR_FUTURE')
    except Exception:
        return finish('ABSTAIN','INPUT_OR_HOST_EVIDENCE_INVALID')
