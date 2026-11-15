from datetime import datetime, timedelta, timezone
import unittest
from meta_harness.task_binding import BoundWorker
from meta_harness.delegation import Failure, Session, TokenBudget, sha, verify
from tests.test_meta_delegation import task, grant, result

NOW = datetime(2026, 11, 15, tzinfo=timezone.utc)
NODE = 'e'*64


def pin(**changes):
    return dict(dict(session_ref='1'*64, generation=3, node_ref=NODE, base_ref='a'*64,
        head_ref=None, runtime_ref='2'*64, selection_ref='3'*64,
        constraints_ref='4'*64, observed_at='2026-11-15T00:00:00Z'), **changes)


class BindingTests(unittest.TestCase):
    def build(self, t=None, p=None, **kw):
        return BoundWorker(t or task(), pin() if p is None else p, local_node_ref=NODE,
            worker=kw.pop('worker',result), witness=kw.pop('witness',lambda *_:True),
            now=kw.pop('now',lambda:NOW), **kw)

    def execute(self, b, authority=grant, session=None):
        s = session or Session(authority,TokenBudget(128))
        return s.execute(b.task(),b,observed_at='2026-11-15T00:00:00Z')

    def test_native_grant_execution_and_integrity(self):
        b=self.build();r=self.execute(b)
        self.assertEqual(r['phase'],'complete');self.assertTrue(verify(r))
        self.assertEqual(r['task_sha256'],sha(b.task()))
        self.assertNotEqual(b.task()['input_sha256'],task()['input_sha256'])
        self.assertEqual(b.record()['authority'],'none')
        self.assertFalse(b.record()['dispatch_authorized'])
        self.assertFalse(b.record()['remote_authorized'])

    def test_old_grant_does_not_authorize_bound_input(self):
        calls=[];b=self.build(worker=lambda *a:calls.append(1))
        r=self.execute(b,authority=lambda _:grant(task()))
        self.assertEqual(r['failure_class'],'PERMISSION');self.assertEqual(calls,[])

    def test_each_pin_changes_task_identity(self):
        for field in ('session_ref','node_ref','head_ref','runtime_ref','selection_ref','constraints_ref','generation','observed_at'):
            changes={field:4 if field=='generation' else (NOW-timedelta(seconds=1)).isoformat() if field=='observed_at' else 'f'*64}
            if field=='node_ref':
                with self.assertRaises(Failure):self.build(p=pin(**changes))
            else:self.assertNotEqual(sha(self.build().task()),sha(self.build(p=pin(**changes)).task()))

    def test_base_and_generation_invalid(self):
        for changes in ({'base_ref':'f'*64},{'generation':True},{'generation':-1},{'head_ref':'private'},{'runtime_ref':None}):
            with self.assertRaises(Failure):self.build(p=pin(**changes))

    def test_source_absent_or_changed_rejects_without_worker(self):
        for w in (lambda *_:False,lambda *_:1):
            calls=[];b=self.build(witness=w,worker=lambda *a:calls.append(1))
            self.assertEqual(self.execute(b)['outcome'],'UNKNOWN');self.assertEqual(calls,[])

    def test_future_expired_naive_clock(self):
        for stamp in ((NOW+timedelta(seconds=1)).isoformat(),(NOW-timedelta(seconds=121)).isoformat(),'bad','2026-11-15T00:00:00'):
            calls=[];b=self.build(p=pin(observed_at=stamp),worker=lambda *a:calls.append(1))
            self.assertEqual(self.execute(b)['failure_class'],'EVIDENCE');self.assertEqual(calls,[])
        self.assertEqual(self.execute(self.build(p=pin(observed_at=(NOW-timedelta(seconds=120)).isoformat())))['phase'],'complete')

    def test_post_execution_pin_change_suppresses_result(self):
        active=[True];calls=[]
        def work(t,c):
            calls.append(1);active[0]=False;return result(t,c)
        r=self.execute(self.build(worker=work,witness=lambda *_:active[0]))
        self.assertEqual(calls,[1]);self.assertEqual(r['outcome'],'UNKNOWN');self.assertIsNone(r['measurement'])

    def test_expiry_during_worker(self):
        current=[NOW]
        def work(t,c):current[0]+=timedelta(seconds=121);return result(t,c)
        r=self.execute(self.build(now=lambda:current[0],worker=work))
        self.assertEqual(r['outcome'],'UNKNOWN');self.assertIsNone(r['measurement'])

    def test_original_and_witness_mutation_isolated(self):
        t=task();p=pin();seen=[]
        def witness(t,p):t['input_sha256']='f'*64;p['generation']=999;return True
        def work(t,c):seen.append(t);return result(t,c)
        b=self.build(t,p,worker=work,witness=witness);t['input_sha256']='f'*64;p['generation']=9
        self.assertEqual(self.execute(b)['phase'],'complete');self.assertEqual(seen,[task()])
        d=b.task();d['model_version']='f'*64;self.assertNotEqual(d,b.task())

    def test_changed_task_and_remote_privacy_rejected(self):
        b=self.build()
        with self.assertRaises(Failure):b(dict(b.task(),run_id='other'),lambda:False)
        with self.assertRaises(Failure):self.build(t=task(privacy='FLEET_SCOPED'))

    def test_lora_switch_during_execution_is_not_delivered(self):
        active=['f'*64]
        def work(t,c):active[0]='9'*64;return result(t,c)
        b=self.build(p=pin(head_ref='f'*64),worker=work,witness=lambda t,p:p['head_ref']==active[0])
        r=self.execute(b)
        self.assertEqual(r['outcome'],'UNKNOWN');self.assertIsNone(r['measurement'])

    def test_two_device_bindings_do_not_share_grant(self):
        a=self.build()
        b=BoundWorker(task(),pin(node_ref='f'*64),local_node_ref='f'*64,
                      worker=result,witness=lambda *_:True,now=lambda:NOW)
        self.assertNotEqual(a.task()['input_sha256'],b.task()['input_sha256'])
        r=self.execute(b,authority=lambda _:grant(a.task()))
        self.assertEqual(r['failure_class'],'PERMISSION')

    def test_replay_never_runs_twice(self):
        calls=[]
        def work(t,c):calls.append(1);return result(t,c)
        b=self.build(worker=work);s=Session(grant,TokenBudget(128))
        a=self.execute(b,session=s);self.assertEqual(a,self.execute(b,session=s));self.assertEqual(calls,[1])

    def test_no_worker_retry_after_unknown(self):
        calls=[]
        def work(t,c):calls.append(1);raise RuntimeError('private-exception')
        b=self.build(worker=work);s=Session(grant,TokenBudget(128))
        a=self.execute(b,session=s);self.assertEqual(a['outcome'],'UNKNOWN')
        self.assertEqual(a,self.execute(b,session=s));self.assertEqual(calls,[1]);self.assertNotIn('private-exception',str(a))

    def test_expiry_inside_witness_prevents_worker(self):
        current=[NOW];calls=[]
        def witness(*_):current[0]+=timedelta(seconds=121);return True
        r=self.execute(self.build(now=lambda:current[0],witness=witness,worker=lambda *a:calls.append(1)))
        self.assertEqual(calls,[]);self.assertEqual(r['failure_class'],'EVIDENCE')

    def test_resource_gate_remains_mandatory_and_routes_wrapper(self):
        from tests.test_resource_admission import AdmissionTests, fixtures
        from meta_harness.resource_admission import AdmissionGate, resources
        t,packets,profiles,policy,_,_,worker,calls=AdmissionTests().fixture()
        b=self.build(t=t,p=pin(base_ref=t['model_version'],observed_at=fixtures.NOW.isoformat()),
                     now=lambda:fixtures.NOW,worker=worker)
        bound=b.task()
        profiles[0]['task_profile_ref']=resources.profile_key(bound)
        profiles[0].pop('profile_ref');profiles[0]['profile_ref']=resources.sha(profiles[0])
        gate=AdmissionGate(lambda _: (packets,profiles,policy),lambda p:p in packets,
            lambda p,t,r:p in profiles and t==bound,
            lambda t,w,n,backend:t==bound and w is b,
            lambda t,n,backend:'f'*64 if t==bound else None,
            now=lambda:fixtures.NOW,clock=lambda:1)
        s=Session(grant,TokenBudget(128),clock=lambda:1,admission=gate)
        r=s.execute(bound,b,observed_at=fixtures.NOW.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertEqual(r['phase'],'complete');self.assertEqual(calls,['dispatch'])
        gate.lease=lambda *_:None
        changed=self.build(t=dict(t,run_id='new-run'),p=pin(base_ref=t['model_version'],observed_at=fixtures.NOW.isoformat()),
                           now=lambda:fixtures.NOW,worker=worker)
        denied=s.execute(changed.task(),changed,observed_at=fixtures.NOW.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertNotEqual(denied['phase'],'complete');self.assertEqual(calls,['dispatch'])

    def test_existing_brain_accepts_bound_original_context(self):
        from tests.test_brain import BrainTests
        from meta_harness.brain import cycle, verify_projections, verify_cycle
        from meta_harness.cli import demo_gate
        args,kw,calls=BrainTests().prepare()
        native=kw['worker']
        stamp=kw['now']()
        current=datetime.fromisoformat(stamp.replace('Z','+00:00'))
        original_tasks=kw['baseline_tasks']+[kw['delegated_task']]
        proofs=tuple(BoundWorker(t,pin(base_ref=native.version,observed_at=stamp,
            selection_ref=args[1].record()['context_ref']),local_node_ref=NODE,
            worker=native,witness=lambda *_:True,now=lambda:current) for t in original_tasks)
        tasks=[b.task() for b in proofs]
        def routed(t,c):
            matches=[b for b in proofs if b.task()==t]
            if len(matches)!=1:raise Failure('EVIDENCE')
            return matches[0](t,c)
        routed.version=native.version
        kw.update(worker=routed,baseline_tasks=tasks[:2],delegated_task=tasks[2])
        kw['session'].authority=lambda t:demo_gate(tasks+[kw['planner_factory'].request],'d'*64)(t)
        kw['bindings']=proofs
        r=cycle(*args,**kw)
        self.assertEqual(r['record']['state'],'MEASURED',r['record'])
        self.assertTrue(verify_projections(r['views'],r['record']))
        self.assertEqual(calls,['planner','memory'])
        # Wrong-context binding is rejected before any new baseline dispatch.
        called=[]
        wrong=tuple(BoundWorker(t,pin(base_ref=native.version,observed_at=stamp),
            local_node_ref=NODE,worker=lambda *a:called.append(1),witness=lambda *_:True,
            now=lambda:current) for t in original_tasks)
        altered=dict(kw,bindings=wrong,baseline_tasks=[b.task() for b in wrong[:2]],
                     delegated_task=wrong[2].task())
        rejected=cycle(*args,**altered)
        self.assertEqual(rejected['record']['state'],'NO_DATA')
        self.assertEqual(rejected['receipts'],[]);self.assertEqual(called,[])
        self.assertEqual(len(r['receipts']),4)
        all_tasks=tasks+[kw['planner_factory'].request]
        self.assertFalse(verify_cycle(r,all_tasks,witness=kw['session'].attests))
        self.assertTrue(verify_cycle(r,all_tasks,witness=kw['session'].attests,bindings=proofs))
        from meta_harness.hexelion import capability_evidence
        import copy
        forged=copy.deepcopy(r['receipts'][0])
        forged['measurement']['output_sha256']='8'*64
        forged['receipt_ref']=sha({k:v for k,v in forged.items() if k!='receipt_ref'})
        self.assertTrue(verify(forged))  # checksum integrity alone is insufficient
        self.assertIsNone(capability_evidence([forged,r['receipts'][1]],tasks[:2],native.version,
            stamp,witness=kw['session'].attests,bindings=proofs,
            context_ref=args[1].record()['context_ref']))
        for bad_proofs,ctx in (((),args[1].record()['context_ref']),
                               (proofs+proofs[:1],args[1].record()['context_ref']),
                               (proofs,'f'*64)):
            self.assertIsNone(capability_evidence(r['receipts'][:2],tasks[:2],native.version,
                stamp,witness=kw['session'].attests,bindings=bad_proofs,context_ref=ctx))

    def test_hostile_metadata_hooks_not_called(self):
        class Evil:
            def __deepcopy__(self,memo):raise AssertionError('hook executed')
        for t,p in ((task(source=Evil()),pin()),(task(),pin(head_ref=Evil())),(dict(task(),unknown=Evil()),pin())):
            with self.assertRaises(Failure):self.build(t,p)

    def test_cancellation_during_worker(self):
        cancelled=[False]
        def work(t,c):cancelled[0]=True;return result(t,c)
        b=self.build(worker=work)
        r=Session(grant,TokenBudget(128)).execute(b.task(),b,observed_at='2026-11-15T00:00:00Z',cancelled=lambda:cancelled[0])
        self.assertEqual(r['failure_class'],'CANCELLED');self.assertIsNone(r['measurement'])


if __name__=='__main__':unittest.main()
