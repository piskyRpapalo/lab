"""Pure head filter composed with canonical resources. Never loads or dispatches.

Host callbacks are injected trusted checks, never supplied by model JSON.
Synthetic controls are eligible only as simulation; measured admission stays separate.
"""
import copy

from .resource_admission import resources

HEAD_KEYS = {'base_ref', 'adapter_ref', 'revision_ref', 'architecture', 'rank',
             'alpha', 'targets', 'runtime_ref', 'node', 'backend', 'head_ref'}
CHECK_KEYS = {'head_ref', 'task_ref', 'generation', 'base_ref', 'architecture',
              'max_rank', 'targets', 'runtime_ref', 'license_allowed', 'provenance_ref',
              'permission', 'observed_at', 'origin', 'profile_ref'}


def _hex(value):
    return type(value) is str and resources.HEX.fullmatch(value) is not None


def evaluate(task, heads, checks, *, packets, profiles, policy, host, verify_head,
             now, generation, pin=None, cache=None):
    """Return bounded local details plus compact proposal; no registry/Host/lease.

    Up to32 heads/32 compatibility reports,256KiB total input. Each compatibility
    report is independently checked by verify_head(head,report,task). Its booleans
    are not self-authenticating. Existing resource host validation runs first.
    pin/cache are either None or exact {base_ref,adapter_ref,head_ref,generation} bindings.
    Base fallback must be a separate future policy; no implicit head switch here.
    """
    task_ref, resource_ref, details = None, None, []
    def finish(cause):
        eligible = sorted(d['head_ref'] for d in details if d['cause'] == 'SYNTHETIC_HEAD_ELIGIBLE')
        summary = {'kind': 'head-eligibility-proposal', 'state': 'SIMULATED_ELIGIBLE' if eligible else 'ABSTAIN',
                   'cause': cause, 'task_ref': task_ref, 'resource_ref': resource_ref,
                   'candidate_count': len(eligible), 'candidates_ref': resources.sha(eligible),
                   'details_ref': resources.sha(details), 'dispatch_authorized': False,
                   'memory_promotion_authorized': False}
        summary['decision_ref'] = resources.sha(summary)
        if len(resources.encode(summary)) >= 1024:
            raise ValueError('summary bound')
        return {'summary': summary, 'details': copy.deepcopy(details)}
    try:
        if (type(generation) is not int or not 0 <= generation < 2**63
                or type(heads) is not list or not 1 <= len(heads) <= 32
                or type(checks) is not list or len(checks) > 32
                or not callable(verify_head)
                or len(resources.encode([task, heads, checks, packets, profiles, policy, pin, cache])) > 262144):
            return finish('INPUT_OR_HOST_CONTRACT_INVALID')
        task, heads, checks, packets, profiles, policy, pin, cache = copy.deepcopy(
            (task, heads, checks, packets, profiles, policy, pin, cache))
        resource = resources.decide(task, packets, profiles, policy, host=host, now=now)
        task_ref, resource_ref = resource.get('task_ref'), resource['decision_ref']
        if resource['state'] != 'SIMULATED_ELIGIBLE':
            return finish(resource['cause'])
        choice = resource['choice']
        for binding in (pin, cache):
            if binding is not None and (type(binding) is not dict or set(binding) != {'base_ref','adapter_ref','head_ref','generation'}
                    or not _hex(binding['base_ref']) or not _hex(binding['adapter_ref']) or not _hex(binding['head_ref'])
                    or type(binding['generation']) is not int or binding['generation'] != generation):
                return finish('SESSION_OR_CACHE_BINDING_INVALID')
        seen = set()
        for head in heads:
            if (type(head) is not dict or set(head) != HEAD_KEYS
                    or not all(_hex(head[k]) for k in ('base_ref','adapter_ref','revision_ref','runtime_ref','head_ref'))
                    or type(head['architecture']) is not str or not 1 <= len(head['architecture']) <= 64
                    or type(head['rank']) is not int or not 1 <= head['rank'] <= 256
                    or type(head['alpha']) is not int or not 1 <= head['alpha'] <= 1024
                    or type(head['targets']) is not list or not 1 <= len(head['targets']) <= 32
                    or any(type(t) is not str or not 1 <= len(t) <= 64 for t in head['targets'])
                    or len(set(head['targets'])) != len(head['targets'])
                    or head['head_ref'] != resources.sha({k:v for k,v in head.items() if k!='head_ref'})):
                return finish('HEAD_MANIFEST_INVALID')
            if head['head_ref'] in seen:
                return finish('DUPLICATE_HEAD')
            seen.add(head['head_ref'])
        for head in sorted(heads, key=lambda h:h['head_ref']):
            cause = None
            matches = [c for c in checks if type(c) is dict and c.get('head_ref') == head['head_ref']]
            if head['base_ref'] != task['model_version']:
                cause = 'BASE_IDENTITY_MISMATCH'
            elif head['node'] != choice['node'] or head['backend'] != choice['backend']:
                cause = 'DEVICE_RESOURCE_MISMATCH'
            elif any(b is not None and (b['base_ref'] != head['base_ref'] or b['adapter_ref'] != head['adapter_ref'] or b['head_ref'] != head['head_ref']) for b in (pin,cache)):
                cause = 'SESSION_OR_CACHE_HEAD_MISMATCH'
            elif len(matches) != 1 or set(matches[0]) != CHECK_KEYS:
                cause = 'COMPATIBILITY_EVIDENCE_MISSING'
            else:
                check = matches[0]
                if verify_head(copy.deepcopy(head), copy.deepcopy(check), copy.deepcopy(task)) is not True:
                    cause = 'HEAD_NOT_WITNESSED'
                elif (check['task_ref'] != task_ref or type(check['generation']) is not int
                      or check['generation'] != generation or not _hex(check['provenance_ref'])):
                    cause = 'PROVENANCE_OR_GENERATION_MISMATCH'
                elif check['profile_ref'] != choice['profile_ref']:
                    cause = 'HEAD_RESOURCE_PROFILE_MISMATCH'
                elif (check['base_ref'] != head['base_ref'] or check['runtime_ref'] != head['runtime_ref']
                      or check['architecture'] != head['architecture']
                      or type(check['max_rank']) is not int or check['max_rank'] < head['rank']
                      or type(check['targets']) is not list or not set(head['targets']) <= set(check['targets'])):
                    cause = 'HEAD_RUNTIME_INCOMPATIBLE'
                elif check['license_allowed'] is not True:
                    cause = 'LICENSE_NOT_AUTHORIZED'
                elif check['permission'] != 'ALLOWED':
                    cause = 'HEAD_PERMISSION_DENIED'
                else:
                    age = resources.age_seconds(check['observed_at'], now)
                    if age > 120:
                        cause = 'HEAD_EVIDENCE_STALE'
                    elif check['origin'] != 'SYNTHETIC':
                        cause = 'HEAD_PRODUCTION_ADMISSION_NOT_CONNECTED'
            details.append({'head_ref':head['head_ref'], 'cause':cause or 'SYNTHETIC_HEAD_ELIGIBLE'})
        return finish('SYNTHETIC_CANDIDATES_ONLY' if any(d['cause']=='SYNTHETIC_HEAD_ELIGIBLE' for d in details)
                      else details[0]['cause'] if len({d['cause'] for d in details})==1 else 'NO_ELIGIBLE_HEAD')
    except resources.EvidenceTimeError as error:
        details.clear()
        return finish(str(error))
    except Exception:
        details.clear()
        return finish('HOST_OR_EVIDENCE_ERROR')
