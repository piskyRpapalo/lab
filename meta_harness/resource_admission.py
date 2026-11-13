"""Host composition of the existing resource instrument and Session grant.

No dispatcher, discovery, fallback, lease allocator or permission issuer. A host
must independently witness exact worker routing and an already-held lease. An
unknown execution outcome must keep that lease until reconciliation. The legacy
offline instrument stays unchanged and never grants execution on its own.
"""
import copy
from datetime import datetime, timezone
import time

from .delegation import Failure, check_grant, sha, validate_task
from .reuse import instrument

resources = instrument('resources')


class AdmissionGate:
    """Inject into Session(admission=gate), so brain uses the same execution path.

    provide(task) -> (packets, independent profiles, host policy).
    verify_projection and witness have the original instrument signatures.
    route(task, worker, node, backend) -> strictly True for the host-bound target.
    lease(task, node, backend) -> ref of a live, exact-task lease, else None.
    A serialized proposal/hash/profile is never a substitute for these callbacks.
    """
    def __init__(self, provide, verify_projection, witness, route, lease, *,
                 human_signature=None, now=lambda: datetime.now(timezone.utc),
                 clock=time.monotonic_ns):
        self.provide, self.verify_projection, self.witness = provide, verify_projection, witness
        self.route, self.lease = route, lease
        self.human_signature, self.now, self.clock = human_signature, now, clock
        self.records = {}

    def record(self, task):
        row = self.records.get(task.get('run_id'))
        return copy.deepcopy(row) if row and row['task_ref'] == sha(task) else None

    def __call__(self, task, grant, worker, cancelled):
        def finish(cause, selected=None, lease_ref=None):
            value = {'schema': 'preceptoros.lab.node-metadata/1', 'kind': 'admission-evaluation',
                     'state': 'VERIFIED' if selected else 'NO_DATA', 'cause': cause,
                     'scope': 'host_witnessed_resource_checks_not_execution_or_permission',
                     'task_ref': sha(task), 'choice': selected, 'lease_ref': lease_ref,
                     'observed_at': self.now().isoformat(), 'promotion': 'NOT_AUTHORIZED'}
            value['admission_ref'] = sha(value)
            if len(resources.encode(value)) >= 1024:
                raise ValueError('admission_record_budget')
            self.records[task['run_id']] = value
            return selected is not None
        try:
            validate_task(task)
            check_grant(grant, task, self.clock())
            if cancelled():
                return finish('CANCELLED')
            if not all(callable(v) for v in (self.provide, self.verify_projection,
                                            self.witness, self.route, self.lease)):
                return finish('HOST_CONTRACT_MISSING')
            packets, profiles, policy = copy.deepcopy(self.provide(copy.deepcopy(task)))
            if type(packets) is not list or not 1 <= len(packets) <= 8:
                return finish('INPUT_BOUND_EXCEEDED')

            def validate(t):
                try:
                    validate_task(t)
                    return True
                except Failure:
                    return False

            def authorize(t):
                try:
                    check_grant(grant, t, self.clock())
                    return grant['approval_ref']
                except Failure:
                    return None

            host = resources.Host(validate, authorize, self.verify_projection,
                                  self.witness, self.human_signature)
            candidates, causes = [], []
            for packet in packets:
                proposal = resources.decide(task, [packet], profiles, policy, host=host,
                                             now=self.now(), cancelled=cancelled)
                # This internal result proves only the instrument's envelope checks.
                # Session permission, exact route and live lease remain separate gates.
                if proposal['cause'] == 'PRODUCTION_ADMISSION_NOT_CONNECTED':
                    record = packet['record']
                    matching = [p for p in profiles if p['origin'] == 'MEASURED'
                        and p['node'] == record['node'] and p['backend'] == record['backend']
                        and p['source_ref'] == record['source_ref']
                        and p['model_version'] == task['model_version']
                        and p['task_profile_ref'] == resources.profile_key(task)]
                    if len(matching) != 1:
                        return finish('TASK_RESOURCE_EVIDENCE_MISSING')
                    candidates.append((record, matching[0], packet))
                else:
                    causes.append('SYNTHETIC_NOT_ADMISSIBLE' if proposal['state'] == 'SIMULATED_ELIGIBLE'
                                  else proposal['cause'])
            if len(candidates) != 1:
                return finish('MULTIPLE_ELIGIBLE_REQUIRES_HOST_CHOICE' if candidates else
                              causes[0] if causes and len(set(causes)) == 1 else 'EVIDENCE_INSUFFICIENT')
            record, profile, packet = candidates[0]
            node, backend = record['node'], record['backend']
            if self.route(copy.deepcopy(task), worker, node, backend) is not True:
                return finish('TRANSPORT_BINDING_NOT_WITNESSED')
            lease_ref = self.lease(copy.deepcopy(task), node, backend)
            if type(lease_ref) is not str or not resources.HEX.fullmatch(lease_ref):
                return finish('RESOURCE_LEASE_MISSING')
            # Re-evaluate at the current host time after potentially slow route/lease checks.
            final = resources.decide(task, [packet], profiles, policy, host=host,
                                     now=self.now(), cancelled=cancelled)
            check_grant(grant, task, self.clock())
            if (cancelled() or final['cause'] != 'PRODUCTION_ADMISSION_NOT_CONNECTED'
                    or self.route(copy.deepcopy(task), worker, node, backend) is not True
                    or self.lease(copy.deepcopy(task), node, backend) != lease_ref):
                return finish('FINAL_HOST_RECHECK_FAILED')
            return finish('RESOURCE_CHECKS_AND_HOST_LEASE_WITNESSED',
                {'node': node, 'backend': backend, 'model_version': task['model_version'],
                 'source_ref': record['source_ref'], 'profile_ref': profile['profile_ref']}, lease_ref)
        except Exception:
            return finish('HOST_OR_EVIDENCE_ERROR')
