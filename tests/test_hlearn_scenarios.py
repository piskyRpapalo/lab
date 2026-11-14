"""Eight executable H-LEARN scenarios plus final-observation adversaries.

All grants/MEASURED labels/leases/physical identities are synthetic TEST DOUBLES.
Only the existing journal tests use isolated temporary local files, never devices.
"""
from dataclasses import replace,asdict
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from meta_harness import hlearn as h
from meta_harness.delegation import Session,TokenBudget,Failure
from meta_harness.execution_journal import ExecutionJournal,DurableTokenBudget


def setup():
    from tests.test_resource_admission import AdmissionTests,fixtures
    from tests.test_meta_delegation import grant
    from tests.test_wake_recovery import fixture
    t,packets,profiles,policy,gate,session,worker,calls = AdmissionTests().fixture()
    wake=fixture();t['input_sha256']=h.sha(asdict(wake['intent']))
    profiles[0]['task_profile_ref']=h.resources.profile_key(t)
    profiles[0].pop('profile_ref');profiles[0]['profile_ref']=h.resources.sha(profiles[0])
    gate.witness=lambda p,task,r:p in profiles and task==t
    for phase in ('observations','after'):
        wake[phase]=[replace(o,observed_at=fixtures.NOW.isoformat()) for o in wake[phase]]
    wake['capability']=replace(wake['capability'],observed_at=fixtures.NOW.isoformat())
    for key in ('task','now','admission'):wake.pop(key)
    host=h.resources.Host(lambda task:task==t,lambda task:'c'*64 if task==t else None,
                          lambda p:p in packets,lambda p,task,r:p in profiles and task==t)
    return dict(task=t,packets=packets,profiles=profiles,policy=policy,host=host,gate=gate,
                grant=grant(t),worker=worker,now=fixtures.NOW,wake_inputs=wake),calls


class HlearnScenarios(unittest.TestCase):
    def check(self,d,cause=None):
        r=h.evaluate(**d);row=r['receipt']
        self.assertFalse(row['dispatch_authorized']);self.assertEqual(row['physical_actions'],0)
        self.assertEqual(row['reservation'],'NOT_REQUESTED');self.assertEqual(row['promotion'],'NOT_AUTHORIZED')
        self.assertLess(len(h.resources.encode(row)),1024)
        self.assertEqual(row['receipt_ref'],h.sha({k:v for k,v in row.items() if k!='receipt_ref'}))
        if r['decision'] is not None:self.assertEqual(row['decision_ref'],r['decision']['decision_ref'])
        if cause:self.assertEqual(row['cause'],cause)
        return r

    def test_01_fresh_valid_typed_proposal_without_effect(self):
        d,calls=setup();a=self.check(d,'PHYSICAL_ACTION_NOT_IMPLEMENTED');b=self.check(d)
        self.assertEqual(a,b);self.assertEqual(calls,[])
        self.assertEqual(a['receipt']['state'],'SIMULATED')
        self.assertEqual(a['admission']['state'],'VERIFIED')
        self.assertEqual(a['decision']['state'],'ABSTAIN')
        self.assertEqual(a['decision']['cause'],'PRODUCTION_ADMISSION_NOT_CONNECTED')
        d['wake_inputs']=None
        self.check(d,'PRODUCTION_ADMISSION_NOT_CONNECTED')

    def test_02_incorrect_node_identity_rejected(self):
        d,calls=setup();d['packets'][0]['record']['node']='unbound-alias'
        self.check(d,'NODE_EVIDENCE_INVALID');self.assertEqual(calls,[])
        d,calls=setup();w=d['wake_inputs'];w['observations'][0]=replace(w['observations'][0],node_ref='0'*64)
        self.check(d,'INPUT_OR_HOST_EVIDENCE_INVALID')

    def test_03_stale_evidence_rejected(self):
        d,calls=setup();d['packets'][0]['record']['state']='STALE'
        self.check(d,'EVIDENCE_STALE');self.assertEqual(calls,[])

    def test_04_missing_or_revoked_grant_rejected(self):
        for grant in (None,{},dict(setup()[0]['grant'],approved=False)):
            d,calls=setup();d['grant']=grant;self.check(d,'GRANT_PERMISSION');self.assertEqual(calls,[])
        # A host denial before selection must also prevent the proposal.
        d,calls=setup();d['host']=replace(d['host'],authorize=lambda _:None)
        self.check(d,'PERMISSION_DENIED')
        d,calls=setup()
        def revoke(*_):d['grant']['approved']=False;return 'f'*64
        d['gate'].lease=revoke
        self.check(d,'HOST_OR_EVIDENCE_ERROR');self.assertEqual(calls,[])

    def test_05_invalid_or_changed_lease_rejected(self):
        d,calls=setup();d['gate'].lease=lambda *_:None
        self.check(d,'RESOURCE_LEASE_MISSING');self.assertEqual(calls,[])
        d,calls=setup();leases=iter(['f'*64,'0'*64])
        d['gate'].lease=lambda *_:next(leases)
        self.check(d,'FINAL_HOST_RECHECK_FAILED');self.assertEqual(calls,[])

    def test_06_duplicate_concurrent_never_claims_twice(self):
        d,calls=setup();w=d['wake_inputs'];w['ledger']=replace(w['ledger'],active_attempt='f'*64)
        self.check(d,'CONCURRENT_ATTEMPT_REQUIRES_HOST_CAS');self.assertEqual(calls,[])
        # Actual existing host journal primitive, not an H-LEARN allocator.
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'journal.sqlite';journal=ExecutionJournal.create(path)
            journal.initialize_budget(128)
            barrier=threading.Barrier(2);wins=[];losses=[]
            def claim():
                barrier.wait(timeout=3)
                try:ExecutionJournal(path).claim(d['task']['run_id'],h.sha(d['task']),budget_cap=64);wins.append(1)
                except Failure:losses.append(1)
            threads=[threading.Thread(target=claim) for _ in range(2)]
            for thread in threads:thread.start()
            for thread in threads:thread.join(4);self.assertFalse(thread.is_alive())
            self.assertEqual((len(wins),len(losses)),(1,1));self.assertEqual(journal.remaining_budget(),64)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM claims').fetchone()[0],1)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM budget_reservations').fetchone()[0],1)

    def test_07_unknown_cannot_resume_until_reconciled(self):
        d,calls=setup()
        from tests.test_meta_delegation import grant
        def uncertain(t,cancelled):calls.append(1);raise OSError('synthetic')
        d['gate'].route=lambda t,w,n,b:w is uncertain
        with tempfile.TemporaryDirectory() as tmp:
            journal=ExecutionJournal.create(Path(tmp)/'journal.sqlite')
            journal.initialize_budget(128)
            session=Session(grant,DurableTokenBudget(journal),admission=d['gate'],journal=journal,clock=lambda:1)
            prior=session.execute(d['task'],uncertain,observed_at=d['now'].strftime('%Y-%m-%dT%H:%M:%SZ'))
            self.assertEqual(prior['outcome'],'UNKNOWN');self.assertEqual(calls,[1])
            d.update(prior=prior,attests_prior=session.attests)
            self.check(d,'PREVIOUS_OUTCOME_UNKNOWN')
            # A new Session still cannot repeat uncertain work or reclaim its budget.
            reopened=ExecutionJournal(journal.path)
            second=Session(grant,DurableTokenBudget(reopened),admission=d['gate'],journal=reopened,clock=lambda:1)
            again=second.execute(d['task'],uncertain,observed_at=d['now'].strftime('%Y-%m-%dT%H:%M:%SZ'))
            self.assertEqual(again,prior);self.assertEqual(calls,[1])
            self.assertEqual(session.budget.remaining,64)
            self.assertEqual(second.budget.remaining,64);self.assertEqual(reopened.remaining_budget(),64)
            with self.assertRaises(Failure):
                second.execute(dict(d['task'],run_id='another-run'),uncertain,
                               observed_at=d['now'].strftime('%Y-%m-%dT%H:%M:%SZ'))
            self.assertEqual(calls,[1])
        d,calls=setup();w=d['wake_inputs'];w['ledger']=replace(w['ledger'],outcome_unknown=True)
        self.check(d,'PREVIOUS_OUTCOME_UNKNOWN')

    def test_08_spontaneous_recovery_cancels_proposal(self):
        d,calls=setup();w=d['wake_inputs'];w['after']=[replace(o,condition='ONLINE',function_ready=True) for o in w['after']]
        r=self.check(d,'REAPPEARED_BEFORE_SIMULATION')
        self.assertEqual(r['receipt']['state'],'CANCELLED');self.assertEqual(calls,[])
        self.assertIsNone(r['recovery']['next_ledger'])

    def test_09_missing_conflicting_duplicate_or_old_final_observations(self):
        from datetime import timedelta
        for mode,cause in [('missing','FINAL_WITNESSES_MISSING'),('conflict','FINAL_OBSERVATIONS_CONFLICT'),
                           ('duplicate','FINAL_WITNESSES_MISSING'),('old','FINAL_OBSERVATIONS_PRECEDE_DIAGNOSIS')]:
            d,calls=setup();w=d['wake_inputs']
            if mode=='missing':w['after']=[]
            if mode=='conflict':w['after'][1]=replace(w['after'][1],condition='POWERED_OFF')
            if mode=='duplicate':w['after']=[w['after'][0]]*2
            if mode=='old':w['after']=[replace(o,observed_at=(d['now']-timedelta(seconds=1)).isoformat()) for o in w['after']]
            r=self.check(d,cause);self.assertEqual(r['receipt']['state'],'ABSTAIN')
            self.assertIsNone(r['recovery']['next_ledger']);self.assertEqual(calls,[])

    def test_10_unwitnessed_prior_and_recovery_boundary_rejected(self):
        d,calls=setup();d['prior']={'outcome':'UNKNOWN','authorized':True}
        self.check(d,'PRIOR_RECEIPT_NOT_HOST_WITNESSED')
        d,calls=setup();d['wake_inputs']['verify_observation']=lambda _:False
        self.check(d,'INPUT_OR_HOST_EVIDENCE_INVALID')
        # Different witness digests are insufficient when the trusted host rejects
        # shared physical provenance; the proposal cannot override that refusal.
        d,calls=setup();d['wake_inputs']['admission']=lambda _:dict(authorized=True)
        self.check(d,'RECOVERY_BOUNDARY_INVALID')

    def test_11_no_io_tools_or_private_errors_in_proposal(self):
        d,calls=setup()
        with patch('socket.socket',side_effect=AssertionError('network')),patch('subprocess.Popen',side_effect=AssertionError('process')),patch('builtins.open',side_effect=AssertionError('disk')):
            self.check(d,'PHYSICAL_ACTION_NOT_IMPLEMENTED')
        self.assertEqual(calls,[])
        d,calls=setup();d['gate'].lease=lambda *_:(_ for _ in ()).throw(ValueError('PRIVATE_CANARY'))
        self.assertNotIn('PRIVATE_CANARY',str(self.check(d)))

    def test_12_gate_resource_binding_cannot_be_crosswired(self):
        d,calls=setup();original=d['gate'].record
        def crosswired(task):
            row=original(task);row['choice']['source_ref']='0'*64
            row['admission_ref']=h.sha({k:v for k,v in row.items() if k!='admission_ref'})
            return row
        d['gate'].record=crosswired
        self.check(d,'ADMISSION_RESOURCE_BINDING_MISMATCH');self.assertEqual(calls,[])
