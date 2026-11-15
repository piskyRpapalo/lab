"""Pure same-host C2C eligibility. No checkpoint reader, loader or dispatcher."""
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Callable, Literal, Optional, TypedDict
from .delegation import sha, validate_task
from .resource_admission import resources
from . import head_eligibility

RECEIVER = 'Qwen/Qwen3-1.7B'
SHARER = 'Qwen/Qwen2.5-1.5B-Instruct'
FUSER = 'nics-efc/C2C_Fuser'
FUSER_PATH = 'qwen3_1.7b+qwen2.5_1.5b_Fuser'


@dataclass(frozen=True)
class KV:
    layers: int
    heads: int
    head_dim: int
    dtype: str
    layout: str


@dataclass(frozen=True)
class Model:
    repo: str
    revision: str
    weights_ref: str  # Digest of complete ordered file/digest manifest, not model tag.
    config_ref: str
    architecture: str
    kv: KV
    format: str = 'HF_SAFETENSORS'
    head_ref: Optional[str] = None  # Genuine LoRA manifest; never the C2C fuser.


@dataclass(frozen=True)
class Fuser:
    repo: str
    path: str
    revision: str
    files_ref: str  # Includes every projector tensor AND every configuration file.
    models_ref: str  # Exact two Model manifests, including revisions and head pins.
    layout_ref: str  # Mapping/projector configuration digest, independently witnessed.
    runtime_ref: str


@dataclass(frozen=True)
class Pair:
    receiver: Model
    sharer: Model
    fuser: Fuser
    upstream_revision: str


@dataclass(frozen=True)
class Pin:
    pair_ref: str
    node_ref: str
    runtime_ref: str
    generation: int


@dataclass(frozen=True)
class Evaluation:
    baselines: tuple  # receiver, sharer, text, c2c
    heldout_ref: str
    judge_ref: str
    quality_policy_ref: str
    issue15_checkpoint_specific: bool
    issue23_no_assumed_gain: bool
    synthetic_public_data_only: bool


@dataclass(frozen=True)
class Witness:
    pair_ref: str
    pin_ref: str
    node_ref: str
    resource_source_ref: str
    observed_at: str
    origin: str  # SIMULATED or MEASURED, only after independent host verification.
    checkpoints_local: bool
    training_revisions_bound: bool
    runtime_compatible: bool
    kv_access: bool
    permission_current: bool
    license_allowed: bool
    license_provenance_ref: str


class Decision(TypedDict):
    schema: str
    state: Literal['READY_FOR_ISOLATED_BENCH', 'ABSTAIN']
    cause: str
    origin: str
    task_ref: Optional[str]
    pair_ref: Optional[str]
    pin_ref: Optional[str]
    evidence_ref: Optional[str]
    evaluation_ref: Optional[str]
    resource_ref: Optional[str]
    admission_ref: Optional[str]
    dispatch_authorized: bool
    promotion: str
    receipt_ref: str


def _hex(value):
    return type(value) is str and resources.HEX.fullmatch(value) is not None


def _revision(value):
    return type(value) is str and len(value) == 40 and all(c in '0123456789abcdef' for c in value)


def models_ref(pair: Pair) -> str:
    return sha([asdict(pair.receiver), asdict(pair.sharer)])


def input_ref(pair: Pair, pin: Pin, evaluation: Evaluation) -> str:
    return sha({'pair': asdict(pair), 'pin': asdict(pin), 'evaluation': asdict(evaluation)})


def preflight(task: dict, pair: Pair, pin: Pin, evaluation: Evaluation, witness: Witness, *,
              packets: list, profiles: list, policy: dict, host, now: datetime,
              verify: Callable[[Witness, Pair, dict], bool],
              admission: Callable[[dict], Optional[dict]], head_inputs: tuple = ()) -> Decision:
    """Host-owned witnesses and AdmissionGate.record view; never model-authored authority.

    Resource profiles must measure the whole pinned same-host pair/fuser workload,
    not the receiver alone. Runtime_ref binds reviewed code and package/backend/host
    versions. verify must independently witness checkpoint bytes, trained-pair
    provenance, KV access, licenses, freshness, physical identity and permission.
    head_inputs, when needed, are trusted inputs to the existing head evaluator.
    READY means preconditions only; neither execution nor quality is authorized.
    """
    refs = dict(task_ref=None, pair_ref=None, pin_ref=None, evidence_ref=None,
                evaluation_ref=None, resource_ref=None, admission_ref=None)
    origin = 'NO_DATA'
    def finish(cause, ready=False):
        row = dict(schema='preceptoros.c2c-preflight/0',
                   state='READY_FOR_ISOLATED_BENCH' if ready else 'ABSTAIN', cause=cause,
                   origin=origin, **refs, dispatch_authorized=False, promotion='NOT_AUTHORIZED')
        row['receipt_ref'] = sha(row)
        if len(resources.encode(row)) >= 1024:
            raise ValueError('receipt_bound')
        return row
    try:
        validate_task(task)
        refs['task_ref'] = sha(task)
        if (type(pair) is not Pair or type(pin) is not Pin or type(evaluation) is not Evaluation
                or type(witness) is not Witness or not callable(verify) or not callable(admission)
                or type(head_inputs) is not tuple or len(head_inputs) > 2):
            return finish('INPUT_OR_HOST_CONTRACT_INVALID')
        if type(pair.receiver) is not Model or type(pair.sharer) is not Model or type(pair.fuser) is not Fuser:
            return finish('MANIFEST_INVALID')
        if len(resources.encode([task,asdict(pair),asdict(pin),asdict(evaluation),
                                 asdict(witness),packets,profiles,policy])) > 262144:
            return finish('INPUT_BOUND_EXCEEDED')
        refs.update(pair_ref=sha(asdict(pair)), pin_ref=sha(asdict(pin)), evaluation_ref=sha(asdict(evaluation)))
        r, s, f = pair.receiver, pair.sharer, pair.fuser
        if ((r.repo, s.repo, f.repo, f.path) != (RECEIVER, SHARER, FUSER, FUSER_PATH)
                or not all(_revision(v) for v in (r.revision, s.revision, f.revision, pair.upstream_revision))
                or not all(_hex(v) for v in (r.weights_ref, s.weights_ref, r.config_ref, s.config_ref,
                                              f.files_ref, f.models_ref, f.layout_ref, f.runtime_ref))
                or r.weights_ref == s.weights_ref):
            return finish('ARTIFACT_IDENTITY_OR_DIGEST_INVALID')
        if r.format != 'HF_SAFETENSORS' or s.format != 'HF_SAFETENSORS':
            return finish('CHECKPOINT_FORMAT_UNSUPPORTED')
        # This first pair's published projector has 28 aligned layers, BF16, 2->8 KV heads.
        if (r.architecture != 'Qwen3ForCausalLM' or s.architecture != 'Qwen2ForCausalLM'
                or type(r.kv) is not KV or type(s.kv) is not KV
                or any(type(n) is not int for m in (r, s) for n in (m.kv.layers,m.kv.heads,m.kv.head_dim))
                or r.kv != KV(28,8,128,'bfloat16','BHSD')
                or s.kv != KV(28,2,128,'bfloat16','BHSD')):
            return finish('ARCHITECTURE_OR_KV_LAYOUT_MISMATCH')
        if f.models_ref != models_ref(pair):
            return finish('FUSER_PAIR_OR_HEAD_MISMATCH')
        if (not _hex(pin.node_ref) or type(pin.generation) is not int or not 0 <= pin.generation < 2**63
                or pin.pair_ref != refs['pair_ref'] or pin.runtime_ref != f.runtime_ref
                or task['model_version'] != r.weights_ref
                or task['input_sha256'] != input_ref(pair,pin,evaluation)):
            return finish('TASK_SESSION_OR_CACHE_PIN_MISMATCH')
        if (evaluation.baselines != ('receiver','sharer','text','c2c')
                or type(evaluation.baselines) is not tuple
                or not all(_hex(v) for v in (evaluation.heldout_ref,evaluation.judge_ref,evaluation.quality_policy_ref))
                or evaluation.issue15_checkpoint_specific is not True
                or evaluation.issue23_no_assumed_gain is not True
                or evaluation.synthetic_public_data_only is not True):
            return finish('UPSTREAM_NEGATIVE_EVALUATION_CONSTRAINTS_MISSING')
        if verify(witness,pair,task) is not True:
            return finish('PAIR_HOST_EVIDENCE_NOT_WITNESSED')
        if (witness.pair_ref != refs['pair_ref'] or witness.pin_ref != refs['pin_ref']
                or witness.node_ref != pin.node_ref or not _hex(witness.resource_source_ref)
                or not _hex(witness.license_provenance_ref)
                or witness.origin not in ('SIMULATED','MEASURED')):
            return finish('HOST_EVIDENCE_IDENTITY_MISMATCH')
        if resources.age_seconds(witness.observed_at,now) > 120:
            return finish('HOST_EVIDENCE_STALE')
        origin = witness.origin
        refs['evidence_ref'] = sha(asdict(witness))
        for field,cause in (
                ('checkpoints_local','NO_DATA_LOCAL_CHECKPOINTS'),
                ('training_revisions_bound','NO_DATA_FUSER_TRAINING_REVISIONS'),
                ('runtime_compatible','NO_DATA_RUNTIME_HOST_COMPATIBILITY'),
                ('kv_access','NO_DATA_KV_ACCESS'),
                ('permission_current','PERMISSION_DENIED'),
                ('license_allowed','LICENSE_NOT_AUTHORIZED')):
            if getattr(witness,field) is not True:
                return finish(cause)
        # Optional genuine LoRA manifests stay under #207, never disguised as a fuser.
        if s.head_ref is not None:
            return finish('SHARER_LORA_NOT_QUALIFIED_R0')
        needed = [m for m in (r,s) if m.head_ref is not None]
        if len(needed) != len(head_inputs):
            return finish('LORA_HEAD_EVIDENCE_MISSING')
        for model,spec in zip(needed,head_inputs):
            if (not _hex(model.head_ref) or type(spec) is not dict
                    or spec.get('task') != task or spec.get('generation') != pin.generation
                    or len(spec.get('heads',[])) != 1
                    or spec['heads'][0].get('head_ref') != model.head_ref
                    or spec['heads'][0].get('base_ref') != model.weights_ref
                    or spec.get('pin') != dict(base_ref=model.weights_ref,
                        adapter_ref=spec['heads'][0].get('adapter_ref'),head_ref=model.head_ref,generation=pin.generation)):
                return finish('LORA_HEAD_PIN_MISMATCH')
            qualified = head_eligibility.evaluate(**spec)
            if qualified['summary']['state'] != 'SIMULATED_ELIGIBLE':
                return finish('LORA_HEAD_NOT_ELIGIBLE')
            if origin != 'SIMULATED':
                return finish('NO_DATA_LORA_PRODUCTION_ADMISSION')
        resource = resources.decide(task,packets,profiles,policy,host=host,now=now)
        refs['resource_ref'] = resource['decision_ref']
        if resource['cause'] not in ('TASK_AND_RESOURCES_WITNESSED','PRODUCTION_ADMISSION_NOT_CONNECTED'):
            return finish('RESOURCE_'+resource['cause'])
        if ((origin == 'SIMULATED') != (resource['state'] == 'SIMULATED_ELIGIBLE')):
            return finish('RESOURCE_EVIDENCE_ORIGIN_MISMATCH')
        # AdmissionGate remains authoritative for choosing a measured route/lease.
        record = admission(task)
        if (type(record) is not dict or len(resources.encode(record)) >= 1024
                or record.get('schema') != 'preceptoros.lab.node-metadata/1'
                or record.get('kind') != 'admission-evaluation' or record.get('state') != 'VERIFIED'
                or record.get('task_ref') != refs['task_ref'] or record.get('promotion') != 'NOT_AUTHORIZED'
                or record.get('scope') != 'host_witnessed_resource_checks_not_execution_or_permission'
                or record.get('admission_ref') != sha({k:v for k,v in record.items() if k!='admission_ref'})
                or not _hex(record.get('lease_ref')) or type(record.get('choice')) is not dict):
            return finish('HOST_ADMISSION_OR_LEASE_NOT_WITNESSED')
        choice = record['choice']
        if (choice.get('model_version') != r.weights_ref
                or choice.get('source_ref') != witness.resource_source_ref
                or not any(p.get('profile_ref') == choice.get('profile_ref')
                           and p.get('node') == choice.get('node') and p.get('backend') == choice.get('backend')
                           and p.get('source_ref') == choice.get('source_ref')
                           and p.get('model_version') == r.weights_ref
                           and p.get('task_profile_ref') == resources.profile_key(task) for p in profiles)):
            return finish('ADMISSION_RESOURCE_PROFILE_OR_HOST_MISMATCH')
        if resources.age_seconds(record.get('observed_at'),now) > 120:
            return finish('HOST_ADMISSION_STALE')
        refs['admission_ref'] = record['admission_ref']
        return finish('PRECONDITIONS_ONLY_NOT_AUTHORIZATION_OR_QUALITY',True)
    except resources.EvidenceTimeError:
        return finish('CLOCK_INVALID_OR_FUTURE')
    except Exception:
        return finish('INPUT_OR_HOST_EVIDENCE_INVALID')


@dataclass(frozen=True)
class CacheKey:
    task_ref: str
    pair_ref: str  # both exact base/LoRA manifests and the trained fuser
    pin_ref: str  # host/runtime/generation
    session_ref: str
    context_ref: str  # original selected sources and revisions
    tool_scope_ref: str  # host-approved MCP/tool schemas and policy revision
    permission_ref: str  # live grant/revocation revision; hash alone is not authority


@dataclass(frozen=True)
class CacheRecord:
    key: CacheKey
    cache_ref: str  # complete cache manifest digest, never raw KV data here
    observed_at: str
    origin: str


def cache_preflight(*, cache, expected, verify_cache=None, **inputs):
    """Compose native C2C preflight and isolated cache-scope source checks.

    Host-owned expected key and live verifier are mandatory. No cache loader,
    model/head switch, latent transport, permission or automatic text fallback.
    A changed source/ACL/tool/head/session invalidates reuse even if tensors fit.
    """
    row=dict(schema='preceptoros.c2c-cache-scope/0',state='ABSTAIN',cause='CACHE_EVIDENCE_MISSING',
        origin='NO_DATA',preflight_ref=None,scope_ref=None,cache_ref=None,
        dispatch_authorized=False,cache_reuse_authorized=False,promotion='NOT_AUTHORIZED',
        fallback='TEXT_REQUIRES_NEW_ADMISSION')
    def finish(cause,ready=False):
        row.update(state='READY_FOR_ISOLATED_BENCH' if ready else 'ABSTAIN',cause=cause)
        row['receipt_ref']=sha(row)
        if len(resources.encode(row))>=1024:raise ValueError('receipt_bound')
        return row
    try:
        # Primitive refs checked BEFORE asdict/deepcopy of caller-owned values.
        def key_valid(key):
            return type(key) is CacheKey and all(_hex(getattr(key,k)) for k in CacheKey.__dataclass_fields__)
        if (not key_valid(expected) or type(cache) is not CacheRecord or not key_valid(cache.key)
                or not _hex(cache.cache_ref) or type(cache.observed_at) is not str
                or len(cache.observed_at)>64 or type(cache.origin) is not str
                or cache.origin not in ('SIMULATED','MEASURED')):
            return finish('CACHE_MANIFEST_INVALID')
        expected_fields=asdict(expected)
        saved=CacheRecord(CacheKey(**asdict(cache.key)),cache.cache_ref,cache.observed_at,cache.origin)
        row.update(scope_ref=sha(expected_fields),cache_ref=saved.cache_ref)
        if not callable(verify_cache):return finish('CACHE_LIVE_WITNESS_MISSING')
        first=preflight(**inputs)
        row.update(preflight_ref=first['receipt_ref'],origin=first['origin'])
        if first['state']!='READY_FOR_ISOLATED_BENCH':return finish(first['cause'])
        if (expected_fields['task_ref']!=first['task_ref'] or expected_fields['pair_ref']!=first['pair_ref']
                or expected_fields['pin_ref']!=first['pin_ref']):
            return finish('CACHE_TASK_PAIR_OR_PIN_MISMATCH')
        if asdict(saved.key)!=expected_fields:return finish('CACHE_SCOPE_MISMATCH')
        if saved.origin!=first['origin']:return finish('CACHE_ORIGIN_MISMATCH')
        if resources.age_seconds(saved.observed_at,inputs['now'])>120:return finish('CACHE_STALE')
        def witnessed():
            # Each callback gets fresh isolated values. It cannot alter the compared key.
            copy=CacheRecord(CacheKey(**asdict(saved.key)),saved.cache_ref,saved.observed_at,saved.origin)
            return verify_cache(copy,CacheKey(**expected_fields)) is True
        if not witnessed():return finish('CACHE_NOT_CURRENTLY_WITNESSED')
        # Re-read canonical preconditions after source/permission checks.
        final=preflight(**inputs)
        if (final['state']!='READY_FOR_ISOLATED_BENCH' or any(final[k]!=first[k]
                for k in ('task_ref','pair_ref','pin_ref','evidence_ref','admission_ref','evaluation_ref','resource_ref','origin'))):
            return finish('CACHE_FINAL_PREFLIGHT_CHANGED')
        if not witnessed():return finish('CACHE_WITNESS_REVOKED')
        return finish('CACHE_PRECONDITIONS_ONLY_NOT_AUTHORIZATION',True)
    except resources.EvidenceTimeError:
        return finish('CACHE_CLOCK_INVALID_OR_FUTURE')
    except Exception:
        return finish('CACHE_HOST_OR_EVIDENCE_ERROR')
