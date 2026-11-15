"""Pure metadata consultation, not a presence publisher, task registry or authority."""
from dataclasses import asdict,dataclass
from datetime import datetime,timedelta
import re
from typing import Callable,Optional,TypedDict,Literal
from .delegation import LABEL,HEX,sha,encode,validate_task,verify
from .resource_admission import resources
from .self_build_git_witness import HEX40

CAUSES=frozenset(('AMBIGUOUS_PUBLICATION', 'CAPABILITY_INVALID', 'CAPABILITY_NOT_WITNESSED', 'CLAIM_BINDING_MISMATCH', 'CLAIM_INVALID', 'CLAIM_OWNER_CHANGED', 'CLAIM_SOURCE_NOT_WITNESSED', 'CLAIM_SOURCE_STALE', 'CLOCK_INVALID_OR_FUTURE', 'DECLARATION_STALE', 'DISCLOSURE_NOT_WITNESSED', 'DUPLICATE_CAPABILITY_EVIDENCE', 'EVIDENCE_SELECTION_OR_HEAD_MISMATCH', 'EXECUTION_EVIDENCE_STALE', 'EXECUTION_NOT_OBSERVED', 'EXECUTION_OUTCOME_NOT_KNOWN', 'INPUT_BOUND_EXCEEDED', 'INPUT_INVALID', 'INPUT_OR_HOST_CONTRACT_INVALID', 'INPUT_OR_HOST_EVIDENCE_INVALID', 'JOURNAL_EVIDENCE_NOT_WITNESSED', 'PUBLICATION_INVALID', 'PUBLICATION_TIME_INVALID', 'RECENT_EXACT_CONTEXT_EXECUTION_EVIDENCE_ONLY', 'SELECTED_ACTIVATION_MISSING', 'SOURCE_TYPE_INVALID', 'WORKTREE_CLAIM_CONFLICT'))
TTL=15
OMIT=frozenset({'label','repository','branch','head','mission','scope','capabilities','review'})
BRANCH=re.compile(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,95}\Z')


@dataclass(frozen=True)
class Selection:
    session_ref: str
    instance_ref: str
    generation: int
    repo_ref: str
    clone_ref: str
    worktree_ref: str
    head: str


@dataclass(frozen=True)
class Declaration:
    selection: Selection
    label: str
    repository: str
    branch: str
    mission: str
    claim_ref: str
    scope_ref: str
    declared_at: str
    heartbeat_at: str
    omissions: tuple=()


@dataclass(frozen=True)
class Claim:
    source_ref: str  # Current host-witnessed Mesa projection, never a new assignment.
    session_ref: str
    instance_ref: str
    repo_ref: str
    worktree_ref: str
    mission: str
    scope_ref: str
    generation: int
    observed_at: str
    review_pending: bool


@dataclass(frozen=True)
class Observation:
    selection: Selection
    claim_ref: str
    source_ref: str  # Host-pinned journal/source identity, not authentication by hash.
    task: dict
    receipt: dict  # Original native Session receipt, never copied into the output.


@dataclass(frozen=True)
class Capability:
    name: str
    evidence_ref: str
    task_ref: str
    scope_ref: str


class Snapshot(TypedDict):
    schema: str
    state: Literal['DECLARED','OBSERVED','STALE','NO_DATA']
    cause: str
    authority: Literal['none']
    ownerReply: bool
    selection_ref: Optional[str]
    identity: Optional[dict]
    publication: Optional[dict]
    source_ref: Optional[str]
    journal_source_ref: Optional[str]
    evidence_basis: Optional[str]
    metadata_kind: str
    claim_ref: Optional[str]
    evidence_ref: Optional[str]
    declared_at: Optional[str]
    observed_at: Optional[str]
    expires_at: Optional[str]
    projected_at: Optional[str]
    ttl_seconds: int
    has_recent_execution_evidence: bool
    liveness: str
    human_review: str
    capabilities: list
    scope: str
    omissions: list
    unknowns: list
    snapshot_ref: str


def _hex(x):return type(x) is str and HEX.fullmatch(x) is not None

def _label(x):return type(x) is str and LABEL.fullmatch(x) is not None

def _selection(x):
    return (type(x) is Selection and all(_hex(getattr(x,k)) for k in
            ('session_ref','instance_ref','repo_ref','clone_ref','worktree_ref'))
            and type(x.generation) is int and 1<=x.generation<2**63
            and type(x.head) is str and HEX40.fullmatch(x.head) is not None)


def project(selection: Selection,declarations: list,claim: Optional[Claim],observation: Optional[Observation],
            capabilities: list,*,now: datetime,allow_publication: Callable,
            verify_claim: Callable,verify_observation: Callable,verify_capability: Callable) -> Snapshot:
    """All callbacks belong to trusted host; a model supplies neither witnesses nor paths.

    Input is a bounded selected-activation capture from existing Mesa/journal adapters.
    No source is read, polled, modified or refreshed here. OBSERVED means a recent
    exact-context KNOWN execution receipt was independently witnessed, not a live
    process, completed mission, capability to run new work or exclusive writer lock.
    """
    row=dict(schema='agent-presence-snapshot/1',state='NO_DATA',cause='INPUT_INVALID',authority='none',
             ownerReply=False,selection_ref=None,identity=None,publication=None,source_ref=None,
             claim_ref=None,evidence_ref=None,journal_source_ref=None,evidence_basis=None,metadata_kind='DECLARED_PUBLICATION',declared_at=None,observed_at=None,expires_at=None,
             projected_at=None,ttl_seconds=TTL,has_recent_execution_evidence=False,
             liveness='NO_DATA(process_liveness_not_proven)',human_review='NO_DATA(review_status_unwitnessed)',
             capabilities=[],scope='published_metadata_only',omissions=['private-context','tool-output'],
             unknowns=['reachability','exclusive-writer-ownership','owner-decision','cross-cli-live-presence'])
    def finish(state,cause):
        row.update(state=state,cause=cause,has_recent_execution_evidence=state=='OBSERVED')
        row['snapshot_ref']=sha(row)
        if len(encode(row))>=16384:raise ValueError('snapshot_bound')
        return row
    try:
        # Check host time even when no source exists; never replace source time with query time.
        resources.age_seconds(now.isoformat(),now)
        row['projected_at']=now.isoformat()
        if (not _selection(selection) or type(declarations) is not list or len(declarations)>32
                or type(capabilities) is not list or len(capabilities)>8
                or not all(callable(f) for f in (allow_publication,verify_claim,verify_observation,verify_capability))):
            return finish('NO_DATA','INPUT_OR_HOST_CONTRACT_INVALID')
        if any(type(d) is not Declaration or not _selection(d.selection) for d in declarations):
            return finish('NO_DATA','PUBLICATION_INVALID')
        if (claim is not None and type(claim) is not Claim) or (observation is not None and type(observation) is not Observation):
            return finish('NO_DATA','SOURCE_TYPE_INVALID')
        if any(type(c) is not Capability for c in capabilities):return finish('NO_DATA','CAPABILITY_INVALID')
        if len(encode([asdict(selection),[asdict(d) for d in declarations],asdict(claim) if claim else None,
                       asdict(observation) if observation else None,[asdict(c) for c in capabilities]]))>262144:
            return finish('NO_DATA','INPUT_BOUND_EXCEEDED')
        row['selection_ref']=sha(asdict(selection))
        selected=[d for d in declarations if d.selection==selection]
        if len(selected)!=1:
            return finish('NO_DATA','SELECTED_ACTIVATION_MISSING' if not selected else 'AMBIGUOUS_PUBLICATION')
        d=selected[0]
        if (not all(_label(getattr(d,k)) for k in ('label','repository','mission'))
                or type(d.branch) is not str or not BRANCH.fullmatch(d.branch) or '..' in d.branch or '//' in d.branch
                or not _hex(d.claim_ref) or not _hex(d.scope_ref) or type(d.omissions) is not tuple
                or len(set(d.omissions))!=len(d.omissions) or not set(d.omissions)<=OMIT):
            return finish('NO_DATA','PUBLICATION_INVALID')
        if allow_publication(d) is not True:return finish('NO_DATA','DISCLOSURE_NOT_WITNESSED')
        # Only fixed whitelisted metadata; private activity/text never enters this model.
        row['identity']={k:getattr(selection,k) for k in ('session_ref','instance_ref','generation','repo_ref','clone_ref','worktree_ref')}
        row['publication']={k:None if k in d.omissions else getattr(d,k) for k in ('label','repository','branch','mission')}
        row['publication'].update(head=None if 'head' in d.omissions else selection.head,
                                  scope_ref=None if 'scope' in d.omissions else d.scope_ref)
        row['omissions']=sorted(set(row['omissions'])|set(d.omissions))
        if any(type(t) is not str or len(t)>40 for t in (d.declared_at,d.heartbeat_at)):
            return finish('NO_DATA','PUBLICATION_TIME_INVALID')
        age=resources.age_seconds(d.declared_at,now)
        resources.age_seconds(d.heartbeat_at,now)  # A heartbeat is untrusted recency, not execution.
        row['declared_at']=d.declared_at
        row['expires_at']=(now-timedelta(seconds=age)+timedelta(seconds=TTL)).isoformat()
        if age>TTL:return finish('STALE','DECLARATION_STALE')
        for peer in declarations:
            if (peer.selection!=selection and peer.selection.worktree_ref==selection.worktree_ref
                    and resources.age_seconds(peer.declared_at,now)<=TTL):
                return finish('NO_DATA','WORKTREE_CLAIM_CONFLICT')
        if claim is None or verify_claim(claim) is not True:
            return finish('DECLARED','CLAIM_SOURCE_NOT_WITNESSED')
        if (not all(_hex(getattr(claim,k)) for k in ('source_ref','session_ref','instance_ref','repo_ref','worktree_ref','scope_ref'))
                or not _label(claim.mission) or type(claim.generation) is not int or claim.generation<1
                or type(claim.review_pending) is not bool):return finish('NO_DATA','CLAIM_INVALID')
        if resources.age_seconds(claim.observed_at,now)>120:return finish('DECLARED','CLAIM_SOURCE_STALE')
        if (claim.session_ref,claim.instance_ref)!=(selection.session_ref,selection.instance_ref):
            return finish('NO_DATA','CLAIM_OWNER_CHANGED')
        if (claim.repo_ref!=selection.repo_ref or claim.worktree_ref!=selection.worktree_ref
                or claim.mission!=d.mission or claim.scope_ref!=d.scope_ref or sha(asdict(claim))!=d.claim_ref):
            return finish('NO_DATA','CLAIM_BINDING_MISMATCH')
        row['claim_ref']=d.claim_ref
        row['source_ref']=claim.source_ref
        if 'review' not in d.omissions:
            row['human_review']='WAITING_FOR_HUMAN_REVIEW' if claim.review_pending else 'NO_PENDING_REVIEW_REPORTED_NOT_APPROVAL'
        if observation is None:return finish('DECLARED','EXECUTION_NOT_OBSERVED')
        if observation.selection!=selection or observation.claim_ref!=d.claim_ref or not _hex(observation.source_ref):
            return finish('NO_DATA','EVIDENCE_SELECTION_OR_HEAD_MISMATCH')
        validate_task(observation.task)
        receipt=observation.receipt
        if (not verify(receipt) or receipt['task_sha256']!=sha(observation.task)
                or receipt['run_id']!=observation.task['run_id']
                or verify_observation(observation,d,claim) is not True):
            return finish('NO_DATA','JOURNAL_EVIDENCE_NOT_WITNESSED')
        row['evidence_ref']=sha(receipt)
        row['journal_source_ref']=observation.source_ref
        row['evidence_basis']=receipt['confidence_basis']
        row['observed_at']=receipt['observed_at']
        evidence_age=resources.age_seconds(receipt['observed_at'],now)
        row['expires_at']=(now-timedelta(seconds=max(age,evidence_age))+timedelta(seconds=TTL)).isoformat()
        if evidence_age>TTL:return finish('STALE','EXECUTION_EVIDENCE_STALE')
        if receipt['outcome']!='KNOWN':return finish('NO_DATA','EXECUTION_OUTCOME_NOT_KNOWN')
        if len({sha(asdict(c)) for c in capabilities})!=len(capabilities):
            return finish('NO_DATA','DUPLICATE_CAPABILITY_EVIDENCE')
        for c in capabilities:
            if (not _label(c.name) or not all(_hex(getattr(c,k)) for k in ('evidence_ref','task_ref','scope_ref'))
                    or c.evidence_ref!=row['evidence_ref'] or c.task_ref!=sha(observation.task)
                    or c.scope_ref!=d.scope_ref or receipt['phase']!='complete'
                    or receipt['measurement']['grade']!='PASS' or verify_capability(c,observation) is not True):
                return finish('NO_DATA','CAPABILITY_NOT_WITNESSED')
        if 'capabilities' not in d.omissions:
            row['capabilities']=[dict(asdict(c),state='OBSERVED',evidence_basis=receipt['confidence_basis'])
                                 for c in sorted(capabilities,key=lambda c:(c.name,c.evidence_ref))]
        return finish('OBSERVED','RECENT_EXACT_CONTEXT_EXECUTION_EVIDENCE_ONLY')
    except resources.EvidenceTimeError:
        return finish('NO_DATA','CLOCK_INVALID_OR_FUTURE')
    except Exception:
        return finish('NO_DATA','INPUT_OR_HOST_EVIDENCE_INVALID')


def receipt(snapshot: Snapshot) -> dict:
    """Compact consultation receipt; self-integrity is not source authentication."""
    if (type(snapshot) is not dict or set(snapshot)!=set(Snapshot.__annotations__)
            or snapshot.get('schema')!='agent-presence-snapshot/1'
            or snapshot.get('state') not in ('DECLARED','OBSERVED','STALE','NO_DATA')
            or snapshot.get('scope')!='published_metadata_only'
            or snapshot.get('cause') not in CAUSES
            or snapshot.get('has_recent_execution_evidence') is not (snapshot.get('state')=='OBSERVED')
            or any(snapshot.get(k) is not None and not _hex(snapshot.get(k))
                   for k in ('selection_ref','claim_ref','journal_source_ref','evidence_ref','snapshot_ref'))
            or len(encode(snapshot))>=16384 or snapshot.get('authority')!='none'
            or snapshot.get('ownerReply') is not False
            or snapshot.get('snapshot_ref')!=sha({k:v for k,v in snapshot.items() if k!='snapshot_ref'})):
        raise ValueError('snapshot_invalid')
    row={k:snapshot[k] for k in ('state','cause','selection_ref','claim_ref','journal_source_ref','evidence_ref','observed_at','expires_at')}
    row.update(schema='agent-presence-receipt/1',snapshot_ref=snapshot['snapshot_ref'],authority='none',ownerReply=False)
    row['receipt_ref']=sha(row)
    if len(encode(row))>=1024:raise ValueError('receipt_bound')
    return row
