"""Host-wiring controls only; all profiles/leases here are TEST DOUBLES."""
import copy
from datetime import timedelta
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'bin'))
import resource_decision_probe as fixtures
from meta_harness.delegation import Session, TokenBudget, sha, verify
from meta_harness.resource_admission import AdmissionGate, resources
from tests.test_meta_delegation import grant, result


class AdmissionTests(unittest.TestCase):
    def fixture(self, *, origin='MEASURED'):
        task, packets, profiles, policy = fixtures.fixture()
        profiles[0]['origin'] = origin
        profiles[0].pop('profile_ref'); profiles[0]['profile_ref'] = resources.sha(profiles[0])
        originals = copy.deepcopy((packets, profiles))
        calls = []
        def worker(t, cancelled):
            calls.append('dispatch')
            return result(t, cancelled)
        gate = AdmissionGate(lambda t: (packets, profiles, policy),
            lambda p: p in originals[0],
            lambda p,t,r: p in originals[1] and t == task,
            lambda t,w,n,b: w is worker and t == task and (n,b)==('node-b','default'),
            lambda t,n,b: 'f'*64 if t == task else None,
            now=lambda: fixtures.NOW, clock=lambda: 1)
        session = Session(grant, TokenBudget(128), clock=lambda: 1, admission=gate)
        return task, packets, profiles, policy, gate, session, worker, calls

    def execute(self, setup):
        t,n,p,policy,g,s,w,calls=setup
        receipt=s.execute(t,w,observed_at=fixtures.NOW.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertTrue(verify(receipt))
        return receipt,g.record(t),calls

    def test_measured_test_double_witness_and_exact_route_lease_use_original_session(self):
        setup=self.fixture()
        receipt,record,calls=self.execute(setup)
        self.assertEqual(receipt['phase'],'complete')
        self.assertEqual(record['state'],'VERIFIED')
        self.assertEqual(record['task_ref'],receipt['task_sha256'])
        self.assertEqual(calls,['dispatch'])
        self.assertEqual(self.execute(setup)[0],receipt)
        self.assertEqual(calls,['dispatch'])  # Session idempotency remains authoritative.

    def test_proposal_or_missing_profile_never_becomes_permission(self):
        receipt,record,calls=self.execute(self.fixture(origin='SYNTHETIC'))
        self.assertEqual((receipt['phase'],record['cause'],calls),
                         ('blocked','SYNTHETIC_NOT_ADMISSIBLE',[]))
        setup=self.fixture();setup[2].clear()
        self.assertEqual(self.execute(setup)[1]['cause'],'TASK_RESOURCE_EVIDENCE_MISSING')

    def test_lease_route_source_and_calibration_fail_closed(self):
        for field,value,cause in [('lease',lambda *_:None,'RESOURCE_LEASE_MISSING'),
            ('route',lambda *_:False,'TRANSPORT_BINDING_NOT_WITNESSED'),
            ('verify_projection',lambda *_:False,'PROJECTION_NOT_WITNESSED'),
            ('witness',lambda *_:False,'PROFILE_NOT_WITNESSED')]:
            setup=self.fixture();setattr(setup[4],field,value)
            receipt,record,calls=self.execute(setup)
            self.assertEqual((receipt['phase'],record['cause'],calls),('blocked',cause,[]))

    def test_saturation_missing_pressure_budget_and_quality_are_separate(self):
        for edit,cause in [(lambda t,n,p,policy: policy.update(active_jobs=1),'NODE_SATURATION'),
            (lambda t,n,p,policy: n[0]['record']['resources'].update(pressure={'state':'NO_DATA'}),'RESOURCE_TELEMETRY_MISSING'),
            (lambda t,n,p,policy: policy.update(tokens_remaining=0),'BUDGET_INSUFFICIENT')]:
            setup=self.fixture();edit(*setup[:4])
            # Source witness deliberately re-pins a newly observed TEST DOUBLE.
            setup[4].verify_projection=lambda v:v in setup[1]
            self.assertEqual(self.execute(setup)[1]['cause'],cause)

    def test_revoked_lease_and_clock_expiry_before_dispatch(self):
        setup=self.fixture();counter=[]
        def lease(*_):
            counter.append(1);return 'f'*64 if len(counter)==1 else None
        setup[4].lease=lease
        self.assertEqual(self.execute(setup)[1]['cause'],'FINAL_HOST_RECHECK_FAILED')
        setup=self.fixture();times=iter([fixtures.NOW, fixtures.NOW+timedelta(seconds=121)])
        # finish also reads time; keep it stable after expiry.
        setup[4].now=lambda:next(times,fixtures.NOW+timedelta(seconds=121))
        self.assertEqual(self.execute(setup)[0]['phase'],'blocked')

    def test_grant_denial_never_enters_resource_gate_and_no_budget_leak(self):
        setup=self.fixture();setup[5].authority=lambda _:None
        receipt,record,calls=self.execute(setup)
        self.assertEqual(receipt['failure_class'],'PERMISSION')
        self.assertIsNone(record);self.assertEqual(calls,[])
        self.assertEqual(setup[5].budget.remaining,128)

    def test_permission_revoked_during_resource_checks_prevents_dispatch(self):
        setup=self.fixture();calls=[]
        def authority(t):
            calls.append(1)
            return grant(t) if len(calls)==1 else None
        setup[5].authority=authority
        receipt,record,dispatched=self.execute(setup)
        self.assertEqual(receipt['failure_class'],'PERMISSION')
        self.assertEqual(dispatched,[])
        self.assertEqual(setup[5].budget.remaining,128)
        setup=self.fixture();setup[4].lease=lambda *_:None
        self.execute(setup)
        self.assertEqual(setup[5].budget.remaining,128)

    def test_unknown_execution_keeps_lease_and_token_reservation_without_retry(self):
        setup=self.fixture();t,n,p,policy,g,s,w,calls=setup
        def uncertain(t,c):
            calls.append('uncertain');raise OSError('PRIVATE_CANARY')
        g.route=lambda t,w,n,b:w is uncertain
        receipt=s.execute(t,uncertain,observed_at=fixtures.NOW.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual((receipt['outcome'],receipt['failure_class']),('UNKNOWN','UNKNOWN'))
        self.assertEqual(s.budget.remaining,64)
        self.assertEqual(g.lease(t,'node-b','default'),'f'*64)
        self.assertEqual(s.execute(t,uncertain,observed_at=fixtures.NOW.strftime('%Y-%m-%dT%H:%M:%SZ')),receipt)
        self.assertEqual(calls,['uncertain'])
        self.assertNotIn('PRIVATE_CANARY',str(receipt))

    def test_cancellation_inside_gate_and_callback_errors_never_dispatch(self):
        setup=self.fixture();setup[4].lease=lambda *_:(_ for _ in ()).throw(ValueError('PRIVATE'))
        self.assertEqual(self.execute(setup)[1]['cause'],'HOST_OR_EVIDENCE_ERROR')
        setup=self.fixture();t,n,p,policy,g,s,w,calls=setup
        signals=[False]
        def lease(*_):signals[0]=True;return 'f'*64
        g.lease=lease
        receipt=s.execute(t,w,observed_at=fixtures.NOW.strftime('%Y-%m-%dT%H:%M:%SZ'),cancelled=lambda:signals[0])
        self.assertEqual(calls,[])
        self.assertEqual(receipt['outcome'],'NOT_STARTED')

    def test_existing_brain_cycle_uses_same_admission_hook_and_unchanged_contract(self):
        from tests.test_brain import BrainTests
        from meta_harness.brain import cycle,verify_cycle
        harness=BrainTests();args,kw,calls=harness.prepare()
        seen=[]
        def guard(t,grant,worker,cancelled):seen.append(t['run_id']);return True
        kw['session'].admission=guard
        out=cycle(*args,**kw)
        self.assertEqual(out['record']['schema'],'preceptoros.brain-cycle/1')
        self.assertEqual(out['record']['state'],'MEASURED')
        self.assertEqual(len(seen),4)
        tasks=kw['baseline_tasks']+[kw['delegated_task'],kw['planner_factory'].request]
        self.assertTrue(verify_cycle(out,tasks,witness=kw['session'].attests))
        harness=BrainTests();args,kw,calls=harness.prepare()
        kw['session'].admission=lambda *_:False
        out=cycle(*args,**kw)
        self.assertEqual(out['record']['state'],'NO_DATA')
        self.assertEqual(calls,[])

