import copy
from datetime import datetime,timedelta,timezone
from pathlib import Path
import tempfile
import unittest
from meta_harness import brain
from meta_harness.delegation import Session,sha
from meta_harness.execution_journal import ExecutionJournal,DurableTokenBudget
from meta_harness.task_binding import BoundWorker
from meta_harness.resource_admission import AdmissionGate,resources
from tests import test_resource_admission as admission_fixtures
fixtures=admission_fixtures.fixtures
from tests.test_meta_delegation import grant


class DeliveryTests(unittest.TestCase):
    def setup_bridge(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);Path(tmp.name).chmod(0o700)
        journal=ExecutionJournal.create(Path(tmp.name)/'journal.db');journal.initialize_budget(256)
        t,packets,profiles,policy,_,_,worker,calls=admission_fixtures.AdmissionTests().fixture()
        active={'grant':True,'pin':True,'lease':True,'ack':True,'effect':True,'cancel':False}
        clock=[fixtures.NOW]
        pin=dict(session_ref='1'*64,generation=1,node_ref='2'*64,base_ref=t['model_version'],head_ref=None,
                 runtime_ref='3'*64,selection_ref='4'*64,constraints_ref='5'*64,observed_at=fixtures.NOW.isoformat())
        bound=BoundWorker(t,pin,local_node_ref=pin['node_ref'],worker=worker,
                          witness=lambda *_:active['pin'],now=lambda:clock[0])
        task=bound.task();profiles[0]['task_profile_ref']=resources.profile_key(task)
        profiles[0].pop('profile_ref');profiles[0]['profile_ref']=resources.sha(profiles[0])
        gate=AdmissionGate(lambda _: (packets,profiles,policy),lambda p:p in packets,
            lambda p,t,r:p in profiles and t==task,lambda t,w,n,b:t==task and w is bound,
            lambda *a:'f'*64 if active['lease'] else None,now=lambda:clock[0],clock=lambda:1)
        session=Session(lambda t:grant(t) if active['grant'] else None,DurableTokenBudget(journal),
                        journal=journal,admission=gate,clock=lambda:1)
        deliveries=[]
        def receive(envelope):
            deliveries.append(copy.deepcopy(envelope))
            return dict(schema='preceptoros.mission-ack/0',delivery_ref=envelope['delivery_ref'],
                agent_ref=envelope['agent_ref'],node_ref=envelope['node_ref'],
                context_ref=envelope['context_ref'],state='RECEIVED',observed_at=clock[0].strftime('%Y-%m-%dT%H:%M:%SZ'))
        kw=dict(session=session,receive=receive,attest_ack=lambda *_:active['ack'],
                witness_execution=lambda *a:active['effect'] and len(calls)==1,
                now=lambda:clock[0],cancelled=lambda:active['cancel'])
        return bound,kw,active,calls,deliveries,clock

    def test_controlled_receiver_native_chain_and_replay(self):
        b,k,a,c,d,_=self.setup_bridge();r=brain.deliver_bound(b,**k)
        self.assertEqual(r['state'],'VERIFIED');self.assertEqual(c,['dispatch']);self.assertEqual(len(d),1)
        self.assertEqual(r['stages'],dict(observed='NO_DATA',received='RECEIVED',authorized='AUTHORIZED',executed='EXECUTED',verified='VERIFIED'))
        self.assertFalse(r['live']);self.assertFalse(r['remote_authorized']);self.assertEqual(r['authority'],'none')
        self.assertLess(len(resources.encode(r)),1024)
        self.assertEqual(brain.deliver_bound(b,**k)['state'],'REPLAY');self.assertEqual(len(d),1);self.assertEqual(c,['dispatch'])

    def test_denied_or_cancelled_before_delivery(self):
        for flag in ('grant','pin','cancel','lease'):
            b,k,a,c,d,_=self.setup_bridge();a[flag]=flag=='cancel'
            r=brain.deliver_bound(b,**k);self.assertNotEqual(r['state'],'VERIFIED');self.assertEqual(c,[])
            self.assertEqual(d,[])

    def test_ack_node_context_and_agent_forgery(self):
        for field,value in [('delivery_ref','f'*64),('node_ref','f'*64),('context_ref','f'*64),('agent_ref','f'*64),('state','AUTHORIZED'),('schema','other')]:
            b,k,a,c,d,_=self.setup_bridge();original=k['receive']
            k['receive']=lambda e,field=field,value=value:dict(original(e),**{field:value})
            self.assertEqual(brain.deliver_bound(b,**k)['cause'],'ack_mismatch');self.assertEqual(c,[])

    def test_ack_not_witnessed_no_execution(self):
        b,k,a,c,d,_=self.setup_bridge();a['ack']=False
        self.assertEqual(brain.deliver_bound(b,**k)['cause'],'ack_not_witnessed_or_expired');self.assertEqual(c,[])

    def test_missing_execution_witness_is_not_verified(self):
        b,k,a,c,d,_=self.setup_bridge();a['effect']=False
        r=brain.deliver_bound(b,**k);self.assertEqual(r['cause'],'execution_witness_missing')
        self.assertEqual(c,['dispatch']);self.assertEqual(r['stages']['verified'],'NO_DATA')

    def test_network_timeout_and_cancel_during_ack(self):
        for failure in (TimeoutError,OSError):
            b,k,a,c,d,_=self.setup_bridge()
            def fail(_):raise failure('synthetic-private')
            k['receive']=fail;r=brain.deliver_bound(b,**k)
            self.assertEqual(c,[]);self.assertNotIn('synthetic-private',str(r))
        b,k,a,c,d,_=self.setup_bridge();original=k['receive']
        def cancel(e):a['cancel']=True;return original(e)
        k['receive']=cancel
        self.assertEqual(brain.deliver_bound(b,**k)['state'],'CANCELLED');self.assertEqual(c,[])

    def test_revoke_permission_lease_or_model_after_execution(self):
        for flag in ('grant','lease','pin','cancel'):
            b,k,a,c,d,_=self.setup_bridge()
            def witness(*args,flag=flag):a[flag]=flag=='cancel';return True
            k['witness_execution']=witness
            r=brain.deliver_bound(b,**k);self.assertNotEqual(r['state'],'VERIFIED');self.assertEqual(c,['dispatch'])
            self.assertEqual(r['stages']['authorized'],'NO_DATA')

    def test_restart_never_delivers_or_executes_again(self):
        b,k,a,c,d,_=self.setup_bridge();first=brain.deliver_bound(b,**k)
        old=k['session'];j=ExecutionJournal(old.journal.path)
        k['session']=Session(old.authority,DurableTokenBudget(j),admission=old.admission,journal=j,clock=lambda:1)
        r=brain.deliver_bound(b,**k);self.assertEqual(r['state'],'REPLAY')
        self.assertEqual(r['execution_ref'],first['execution_ref']);self.assertEqual(c,['dispatch']);self.assertEqual(len(d),1)

    def test_old_receipt_never_live(self):
        b,k,a,c,d,clock=self.setup_bridge();brain.deliver_bound(b,**k)
        clock[0]+=timedelta(seconds=121)
        r=brain.deliver_bound(b,**k);self.assertNotEqual(r['state'],'VERIFIED');self.assertFalse(r['live'])

    def test_concurrent_duplicate_does_not_execute_twice(self):
        import threading
        from tests.test_meta_delegation import result
        b,k,a,c,d,_=self.setup_bridge();entered=threading.Event();release=threading.Event()
        def block(t,cancelled):
            c.append('dispatch');entered.set()
            if not release.wait(2):raise TimeoutError()
            return result(t,cancelled)
        b._worker=block;results=[]
        thread=threading.Thread(target=lambda:results.append(brain.deliver_bound(b,**k)))
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            other=brain.deliver_bound(b,**k)
            self.assertNotEqual(other['state'],'VERIFIED')
        finally:release.set();thread.join(3)
        self.assertFalse(thread.is_alive());self.assertEqual(c,['dispatch'])
        self.assertEqual(results[0]['state'],'VERIFIED')

    def test_cancel_while_worker_is_executing(self):
        from tests.test_meta_delegation import result
        b,k,a,c,d,_=self.setup_bridge()
        def stop(t,cancelled):c.append('dispatch');a['cancel']=True;return result(t,cancelled)
        b._worker=stop
        r=brain.deliver_bound(b,**k)
        self.assertEqual(r['state'],'CANCELLED');self.assertEqual(c,['dispatch'])
        self.assertEqual(r['stages']['verified'],'NO_DATA')

    def test_cancelled_after_claim_is_not_relabelled_unknown_on_replay(self):
        b,k,a,c,d,_=self.setup_bridge();journal=k['session'].journal;claim=journal.claim
        def stop_after_claim(*args,**kwargs):
            r=claim(*args,**kwargs);a['cancel']=True;return r
        journal.claim=stop_after_claim
        first=brain.deliver_bound(b,**k)
        self.assertEqual(first['state'],'CANCELLED');self.assertEqual(c,[])
        a['cancel']=False
        second=brain.deliver_bound(b,**k)
        self.assertEqual(second['cause'],'prior_not_started_requires_new_request')
        self.assertEqual(len(d),1);self.assertEqual(c,[])

    def test_expired_grant_never_delivers(self):
        b,k,a,c,d,_=self.setup_bridge()
        k['session'].authority=lambda t:dict(grant(t),expires_ns=0)
        r=brain.deliver_bound(b,**k)
        self.assertEqual(r['cause'],'permission');self.assertEqual(d,[]);self.assertEqual(c,[])

    def test_unknown_execution_no_repeat_after_restart(self):
        b,k,a,c,d,_=self.setup_bridge()
        def fail(t,cancelled):c.append('uncertain');raise OSError('synthetic-private')
        b._worker=fail
        self.assertNotEqual(brain.deliver_bound(b,**k)['state'],'VERIFIED')
        old=k['session'];j=ExecutionJournal(old.journal.path)
        k['session']=Session(old.authority,DurableTokenBudget(j),admission=old.admission,journal=j,clock=lambda:1)
        r=brain.deliver_bound(b,**k)
        self.assertEqual(r['cause'],'prior_outcome_unknown');self.assertEqual(c,['uncertain']);self.assertEqual(len(d),1)
        self.assertNotIn('synthetic-private',str(r))

    def test_foreign_checksum_valid_receipt_not_attested_by_local_journal(self):
        b,k,a,c,d,_=self.setup_bridge();brain.deliver_bound(b,**k)
        receipt=k['session'].journal.lookup(b.task()['run_id'],sha(b.task()))
        other,kw,active,calls,deliveries,_=self.setup_bridge()
        kw['session'].execute=lambda *args,**kwargs:copy.deepcopy(receipt)
        # An optimistic downstream callback cannot replace native journal attestation.
        kw['witness_execution']=lambda *_:True
        r=brain.deliver_bound(other,**kw)
        self.assertNotEqual(r['state'],'VERIFIED');self.assertEqual(calls,[])

    def test_missing_durable_journal_or_admission_closes_delivery(self):
        for field in ('journal','admission'):
            b,k,a,c,d,_=self.setup_bridge();setattr(k['session'],field,None)
            self.assertEqual(brain.deliver_bound(b,**k)['cause'],'durable_session_admission_and_host_callbacks_required')
            self.assertEqual(c,[]);self.assertEqual(d,[])


if __name__=='__main__':unittest.main()
