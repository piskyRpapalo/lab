"""WAKE-01 pure recovery proposal. No executor, discovery, power or network API."""
from dataclasses import dataclass, asdict
from typing import Optional, Callable, Sequence, TypedDict
from datetime import datetime, timedelta
from .delegation import validate_task, sha, HEX
from .resource_admission import resources


@dataclass(frozen=True)
class Intent:
    node_ref: str
    attempt_ref: str
    generation: int
    method: str


@dataclass(frozen=True)
class Observation:
    node_ref: str
    witness_ref: str
    observed_at: str
    condition: str
    function_ready: bool = False
    attempt_ref: Optional[str] = None


@dataclass(frozen=True)
class Capability:
    node_ref: str
    method: str
    observed_at: str
    evidence_ref: str
    verified: bool
    critical: bool = False
    mapping_ref: Optional[str] = None


@dataclass(frozen=True)
class Ledger:
    node_ref: str
    version: int
    attempts: int = 0
    cooldown_until: Optional[str] = None
    active_attempt: Optional[str] = None
    last_attempt: Optional[str] = None
    outcome_unknown: bool = False
    seen_attempts: tuple = ()


class RecoveryReceipt(TypedDict):
    schema: str
    state: str
    cause: str
    task_ref: Optional[str]
    method: Optional[str]
    stages: list[str]
    verification: str
    verification_cause: Optional[str]
    dispatch_authorized: bool
    physical_actions: int
    promotion: str
    expected_version: Optional[int]
    next_ledger_ref: Optional[str]
    receipt_ref: str


class RecoveryProposal(TypedDict):
    receipt: RecoveryReceipt
    next_ledger: Optional[Ledger]


METHODS = {'SERVICE_FAILED':'RECONNECT','SUSPENDED':'WAKE_LAN','POWERED_OFF':'POWER_REQUEST'}


class _EvidenceRejected(ValueError):
    pass


def _hex(v):
    return type(v) is str and HEX.fullmatch(v) is not None


def plan(task: dict, intent: Intent, observations: Sequence[Observation],
         capability: Capability, ledger: Ledger, *, now: datetime,
         verify_observation: Callable[[Observation], bool],
         verify_capability: Callable[[Capability], bool],
         admission: Callable[[dict], Optional[dict]], after: Sequence[Observation] = (),
         post: Sequence[Observation] = (), cancelled: bool = False) -> RecoveryProposal:
    """Trusted bounded read-only witnesses; admission(task) reads AdmissionGate record.

    Ledger is an externally witnessed per-device snapshot. Returned next-ledger
    is a CAS proposal only; host must atomically acquire version/reservation before
    any future real action. No atomic allocator/permission issuer is implemented.
    after is the final pre-action recheck; post is attempt-bound simulated proof.
    Trusted callbacks belong to the host, never to model-authored JSON.
    """
    stages=[]
    task_ref=None
    def finish(state,cause,method=None,verified=False,next_ledger=None):
        row={'schema':'preceptoros.wake-proposal/0','state':state,'cause':cause,
             'task_ref':task_ref,'method':method,
             'stages':stages+['RECEIPT'],'verification':'SIMULATED_FUNCTION_RESPONDS' if verified else 'NO_DATA',
             'verification_cause':None if verified else 'fresh_device_and_function_witness_missing',
             'dispatch_authorized':False,'physical_actions':0,'promotion':'NOT_AUTHORIZED',
             'expected_version':ledger.version if type(ledger) is Ledger and type(ledger.version) is int and 0<=ledger.version<=10**9 else None,
             'next_ledger_ref':sha(asdict(next_ledger)) if next_ledger else None}
        row['receipt_ref']=sha(row)
        if len(resources.encode(row))>=1024:raise ValueError('receipt_bound')
        return {'receipt':row,'next_ledger':next_ledger}
    try:
        validate_task(task)
        task_ref=sha(task)
        if (type(intent) is not Intent or type(ledger) is not Ledger or type(capability) is not Capability
                or not all(callable(x) for x in (verify_observation,verify_capability,admission))
                or type(observations) not in (list,tuple) or not 1<=len(observations)<=8
                or type(after) not in (list,tuple) or len(after)>8
                or type(post) not in (list,tuple) or len(post)>8 or type(cancelled) is not bool
                or not _hex(intent.node_ref) or not _hex(intent.attempt_ref)
                or type(intent.generation) is not int or not 0<=intent.generation<=10**9
                or task['input_sha256']!=sha(asdict(intent))
                or ledger.node_ref!=intent.node_ref or capability.node_ref!=intent.node_ref
                or type(ledger.version) is not int or ledger.version!=intent.generation
                or type(ledger.attempts) is not int or not 0<=ledger.attempts<=3
                or type(ledger.outcome_unknown) is not bool or type(ledger.seen_attempts) is not tuple):
            return finish('ABSTAIN','INPUT_OR_IDENTITY_INVALID')
        stages.append('OBSERVE')
        def checked(items):
            result=[]
            for o in items:
                if (type(o) is not Observation or o.node_ref!=intent.node_ref or not _hex(o.witness_ref)
                        or type(o.function_ready) is not bool or verify_observation(o) is not True):
                    raise ValueError('observation_unwitnessed')
                if resources.age_seconds(o.observed_at,now)>120:raise _EvidenceRejected('OBSERVATION_STALE')
                if o.condition not in ('ONLINE','NETWORK_DOWN','SERVICE_FAILED','SUSPENDED','POWERED_OFF','UNKNOWN'):
                    raise ValueError('condition_invalid')
                result.append(o)
            return result
        obs=checked(observations)
        if cancelled:return finish('CANCELLED','CANCELLED_BY_HOST')
        if any(o.condition=='ONLINE' and o.function_ready for o in obs):
            return finish('CANCELLED','ALREADY_RESPONDING')
        stages.append('DIAGNOSE')
        if len({o.witness_ref for o in obs})<2:return finish('ABSTAIN','INDEPENDENT_WITNESSES_MISSING')
        if len({o.condition for o in obs})!=1:return finish('ABSTAIN','DIAGNOSIS_CONFLICT')
        condition=obs[0].condition
        if condition in ('UNKNOWN','NETWORK_DOWN','ONLINE'):
            if intent.method=='MANUAL_RECOVERY':
                return finish('PROPOSED','OWNER_INTERVENTION_REQUIRED','MANUAL_RECOVERY')
            return finish('ABSTAIN','DEVICE_POWER_STATE_NOT_PROVEN')
        stages.append('SELECT_METHOD')
        method=intent.method
        if method not in ('RECONNECT','WAKE_LAN','WAKE_WLAN','POWER_REQUEST','MANUAL_RECOVERY'):
            return finish('ABSTAIN','METHOD_INVALID')
        if method=='MANUAL_RECOVERY':return finish('PROPOSED','OWNER_INTERVENTION_REQUIRED',method)
        if capability.method!=method or verify_capability(capability) is not True or capability.verified is not True:
            return finish('ABSTAIN','CAPABILITY_NOT_WITNESSED')
        if (not _hex(capability.evidence_ref) or type(capability.critical) is not bool
                or resources.age_seconds(capability.observed_at,now)>120):
            return finish('ABSTAIN','CAPABILITY_INVALID_OR_STALE')
        if method=='POWER_REQUEST':
            if not _hex(capability.mapping_ref):return finish('ABSTAIN','PHYSICAL_MAPPING_MISSING')
            return finish('PROPOSED','CRITICAL_OWNER_INTERVENTION_REQUIRED' if capability.critical else 'POWER_OWNER_AUTHORIZATION_REQUIRED',method)
        if capability.critical and method in ('WAKE_LAN','WAKE_WLAN'):
            return finish('ABSTAIN','CRITICAL_INFRASTRUCTURE_REQUIRES_OWNER')
        if method!=METHODS.get(condition) and not(method=='WAKE_WLAN' and condition=='SUSPENDED') and not(method=='WAKE_LAN' and condition=='POWERED_OFF'):
            return finish('ABSTAIN','METHOD_DIAGNOSIS_MISMATCH')
        if ledger.outcome_unknown:return finish('ABSTAIN','PREVIOUS_OUTCOME_UNKNOWN')
        if ledger.active_attempt is not None:return finish('ABSTAIN','CONCURRENT_ATTEMPT_REQUIRES_HOST_CAS')
        if ledger.last_attempt==intent.attempt_ref or intent.attempt_ref in ledger.seen_attempts:return finish('ABSTAIN','ATTEMPT_REPLAY')
        if ledger.attempts>=3:return finish('ABSTAIN','DEVICE_RECOVERY_BUDGET_EXHAUSTED')
        if (type(ledger.seen_attempts) is not tuple or len(ledger.seen_attempts)!=ledger.attempts
                or any(not _hex(a) for a in ledger.seen_attempts)
                or len(set(ledger.seen_attempts))!=len(ledger.seen_attempts)):
            return finish('ABSTAIN','ATTEMPT_HISTORY_INCOMPLETE')
        if ledger.cooldown_until is not None:
            # age_seconds rejects future timestamps: here a future deadline means cooling.
            try:resources.age_seconds(ledger.cooldown_until,now)
            except resources.EvidenceTimeError:return finish('ABSTAIN','COOLDOWN_OR_CLOCK_INVALID')
        stages.append('ADMIT')
        record=admission(task)
        if (type(record) is not dict or record.get('kind')!='admission-evaluation'
                or record.get('schema')!='preceptoros.lab.node-metadata/1'
                or record.get('scope')!='host_witnessed_resource_checks_not_execution_or_permission'
                or record.get('admission_ref')!=sha({k:v for k,v in record.items() if k!='admission_ref'})
                or record.get('state')!='VERIFIED' or record.get('task_ref')!=sha(task)
                or record.get('promotion')!='NOT_AUTHORIZED' or not _hex(record.get('lease_ref'))
                or type(record.get('choice')) is not dict
                or resources.age_seconds(record.get('observed_at'),now)>120):
            return finish('ABSTAIN','HOST_GRANT_ROUTE_RESOURCE_LEASE_NOT_WITNESSED')
        latest=checked(after)
        if any(o.condition=='ONLINE' and o.function_ready for o in latest):
            return finish('CANCELLED','REAPPEARED_BEFORE_SIMULATION',method)
        stages.extend(['EXECUTE_SIMULATED','VERIFY'])
        deadline=(now+timedelta(seconds=300)).isoformat()
        next_state=Ledger(intent.node_ref,ledger.version+1,ledger.attempts+1,deadline,
                          None,intent.attempt_ref,False,ledger.seen_attempts+(intent.attempt_ref,))
        proof=checked(post)
        if any(o.attempt_ref!=intent.attempt_ref for o in proof):
            return finish('ABSTAIN','VERIFICATION_ATTEMPT_MISMATCH')
        if any(resources.age_seconds(o.observed_at,now)>min(resources.age_seconds(x.observed_at,now) for x in obs) for o in proof):
            return finish('ABSTAIN','VERIFICATION_PRECEDES_OBSERVATION')
        verified=len({o.witness_ref for o in proof})>=2 and all(o.condition=='ONLINE' and o.function_ready for o in proof)
        return finish('SIMULATED','PHYSICAL_ACTION_NOT_IMPLEMENTED',method,verified=verified,next_ledger=next_state)
    except _EvidenceRejected as error:
        return finish('ABSTAIN',str(error))
    except resources.EvidenceTimeError:
        return finish('ABSTAIN','EVIDENCE_CLOCK_INVALID_OR_FUTURE')
    except Exception:
        return finish('ABSTAIN','INPUT_OR_HOST_EVIDENCE_INVALID')
