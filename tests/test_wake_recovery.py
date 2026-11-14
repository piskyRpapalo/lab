"""Six opaque synthetic identities;no physical addresses,plugs or executors."""
from dataclasses import replace,asdict
from datetime import datetime,timezone,timedelta
import unittest
from unittest.mock import patch
from meta_harness import wake_recovery as w


NOW=datetime(2026,11,14,12,tzinfo=timezone.utc)


def fixture(index=1,condition='SUSPENDED',method='WAKE_LAN'):
    i=w.Intent(str(index)*64,'a'*64,0,method)
    task={'schema':'preceptoros.meta-task/1','task_id':'wake-fixture','run_id':'wake-run','specialist':'recovery',
          'model_version':'b'*64,'source':'local-model','input_sha256':w.sha(asdict(i)),
          'max_tokens':64,'timeout_ms':1000,'depth':0,'privacy':'LOCAL_ONLY','transport':'local_function'}
    obs=[w.Observation(i.node_ref,str(n)*64,NOW.isoformat(),condition) for n in (7,8)]
    record={'schema':'preceptoros.lab.node-metadata/1',
            'scope':'host_witnessed_resource_checks_not_execution_or_permission','kind':'admission-evaluation','state':'VERIFIED','task_ref':w.sha(task),'promotion':'NOT_AUTHORIZED',
            'lease_ref':'c'*64,'choice':{'node':'node-b'},'observed_at':NOW.isoformat()}
    record['admission_ref']=w.sha(record)
    return dict(task=task,intent=i,observations=obs,capability=w.Capability(i.node_ref,method,NOW.isoformat(),'d'*64,True),
                ledger=w.Ledger(i.node_ref,0),now=NOW,verify_observation=lambda o:True,
                verify_capability=lambda c:True,admission=lambda t:record)


class WakeTests(unittest.TestCase):
    def check(self,d,cause=None):
        r=w.plan(**d);self.assertFalse(r['receipt']['dispatch_authorized'])
        self.assertEqual(r['receipt']['physical_actions'],0)
        self.assertLess(len(w.resources.encode(r['receipt'])),1024)
        if cause:self.assertEqual(r['receipt']['cause'],cause)
        return r

    def test_six_nodes_simulated_only(self):
        for n in range(1,7):
            with self.subTest(node=n):self.assertEqual(self.check(fixture(n))['receipt']['state'],'SIMULATED')

    def test_determinism(self):
        d=fixture();self.assertEqual(self.check(d),self.check(d))

    def test_wrong_identity_and_stale(self):
        d=fixture();d['observations'][0]=replace(d['observations'][0],node_ref='0'*64)
        self.check(d,'INPUT_OR_HOST_EVIDENCE_INVALID')
        d=fixture();d['observations']=[replace(o,observed_at=(NOW-timedelta(seconds=121)).isoformat()) for o in d['observations']]
        self.check(d,'OBSERVATION_STALE')

    def test_two_independent_witnesses(self):
        d=fixture();d['observations']=[d['observations'][0]]*2
        self.check(d,'INDEPENDENT_WITNESSES_MISSING')

    def test_model_claim_cannot_admit(self):
        for record in ({'authorized':True},{'state':'VERIFIED','lease_ref':'c'*64},None):
            d=fixture();d['admission']=lambda t:record
            self.check(d,'HOST_GRANT_ROUTE_RESOURCE_LEASE_NOT_WITNESSED')

    def test_reappearance_before_and_after_admission_cancels(self):
        for field in ('observations','after'):
            d=fixture();d[field]=[replace(o,condition='ONLINE',function_ready=True) for o in d['observations']]
            self.assertEqual(self.check(d)['receipt']['state'],'CANCELLED')

    def test_unknown_network_and_conflicts(self):
        for condition in ('NETWORK_DOWN','UNKNOWN'):
            self.check(fixture(condition=condition),'DEVICE_POWER_STATE_NOT_PROVEN')
        d=fixture();d['observations'][1]=replace(d['observations'][1],condition='POWERED_OFF')
        self.check(d,'DIAGNOSIS_CONFLICT')

    def test_plug_mapping_and_critical_owner(self):
        d=fixture(condition='POWERED_OFF',method='POWER_REQUEST')
        self.check(d,'PHYSICAL_MAPPING_MISSING')
        d['capability']=replace(d['capability'],mapping_ref='e'*64,critical=True)
        self.check(d,'CRITICAL_OWNER_INTERVENTION_REQUIRED')
        self.assertIsNone(self.check(d)['next_ledger'])

    def test_budget_cooldown_concurrency_replay_unknown(self):
        for changes,cause in [({'attempts':3},'DEVICE_RECOVERY_BUDGET_EXHAUSTED'),
            ({'active_attempt':'f'*64},'CONCURRENT_ATTEMPT_REQUIRES_HOST_CAS'),
            ({'last_attempt':'a'*64},'ATTEMPT_REPLAY'),({'outcome_unknown':True},'PREVIOUS_OUTCOME_UNKNOWN'),
            ({'cooldown_until':(NOW+timedelta(seconds=300)).isoformat()},'COOLDOWN_OR_CLOCK_INVALID')]:
            d=fixture();d['ledger']=replace(d['ledger'],**changes);self.check(d,cause)

    def test_old_generation(self):
        d=fixture();d['ledger']=replace(d['ledger'],version=1);self.check(d,'INPUT_OR_IDENTITY_INVALID')

    def test_capability_unknown_or_unwitnessed(self):
        d=fixture();d['capability']=replace(d['capability'],verified=False);self.check(d,'CAPABILITY_NOT_WITNESSED')
        d=fixture();d['verify_observation']=lambda o:False;self.check(d,'INPUT_OR_HOST_EVIDENCE_INVALID')

    def test_service_reconnect_and_wowlan(self):
        self.assertEqual(self.check(fixture(condition='SERVICE_FAILED',method='RECONNECT'))['receipt']['state'],'SIMULATED')
        self.assertEqual(self.check(fixture(method='WAKE_WLAN'))['receipt']['state'],'SIMULATED')

    def test_post_verification_is_explicitly_synthetic(self):
        d=fixture();d['post']=[replace(o,condition='ONLINE',function_ready=True,attempt_ref=d['intent'].attempt_ref) for o in d['observations']]
        self.assertEqual(self.check(d)['receipt']['verification'],'SIMULATED_FUNCTION_RESPONDS')
        d['post']=[replace(d['post'][0],function_ready=False)]
        self.assertEqual(self.check(d)['receipt']['verification'],'NO_DATA')

    def test_no_io_and_actor_admission_reuse(self):
        # Existing gate verifies the recovery actor,not the offline target. Its
        # complete record remains task-bound;it cannot be transplanted here.
        from tests.test_resource_admission import AdmissionTests
        from tests.test_meta_delegation import grant
        setup=AdmissionTests().fixture();task,_,_,_,gate,session,worker,_=setup
        self.assertTrue(gate(task,grant(task),worker,lambda:False))
        d=fixture();d['admission']=lambda t:gate.record(task)
        self.check(d,'HOST_GRANT_ROUTE_RESOURCE_LEASE_NOT_WITNESSED')
        with patch('socket.socket',side_effect=AssertionError('no net')),patch('subprocess.Popen',side_effect=AssertionError('no process')),patch('builtins.open',side_effect=AssertionError('no files')):
            self.check(fixture(),'PHYSICAL_ACTION_NOT_IMPLEMENTED')

    def test_post_proof_cannot_be_transplanted_or_precede_attempt(self):
        d=fixture();d['post']=[replace(o,condition='ONLINE',function_ready=True,attempt_ref='f'*64) for o in d['observations']]
        self.check(d,'VERIFICATION_ATTEMPT_MISMATCH')
        d['post']=[replace(o,attempt_ref=d['intent'].attempt_ref,observed_at=(NOW-timedelta(seconds=1)).isoformat()) for o in d['post']]
        self.check(d,'VERIFICATION_PRECEDES_OBSERVATION')

    def test_future_and_boundaries_and_callback_privacy(self):
        d=fixture();d['observations'][0]=replace(d['observations'][0],observed_at=(NOW+timedelta(seconds=1)).isoformat())
        self.check(d,'EVIDENCE_CLOCK_INVALID_OR_FUTURE')
        for changes in ({'observations':[]},{'observations':fixture()['observations']*5},{'task':{'private':object()}}):
            d=fixture();d.update(changes);self.assertEqual(self.check(d)['receipt']['state'],'ABSTAIN')
        d=fixture();d['verify_capability']=lambda c:(_ for _ in ()).throw(ValueError('PRIVATE_CANARY'))
        self.assertNotIn('PRIVATE_CANARY',str(self.check(d)))

    def test_existing_gate_for_exact_synthetic_recovery_task(self):
        from tests.test_resource_admission import AdmissionTests, fixtures
        from tests.test_meta_delegation import grant
        t,packets,profiles,policy,gate,session,worker,calls=AdmissionTests().fixture()
        d=fixture();t['input_sha256']=w.sha(asdict(d['intent']))
        profiles[0]['task_profile_ref']=w.resources.profile_key(t)
        profiles[0].pop('profile_ref');profiles[0]['profile_ref']=w.resources.sha(profiles[0])
        gate.witness=lambda p,task,record:p in profiles and task==t
        self.assertTrue(gate(t,grant(t),worker,lambda:False))
        d.update(task=t,now=fixtures.NOW,admission=gate.record)
        d['observations']=[replace(o,observed_at=fixtures.NOW.isoformat()) for o in d['observations']]
        d['capability']=replace(d['capability'],observed_at=fixtures.NOW.isoformat())
        self.check(d,'PHYSICAL_ACTION_NOT_IMPLEMENTED')
        self.assertEqual(calls,[])
        gate.lease=lambda *_:None
        self.assertFalse(gate(t,grant(t),worker,lambda:False))
        self.check(d,'HOST_GRANT_ROUTE_RESOURCE_LEASE_NOT_WITNESSED')

    def test_attempt_history_retained_and_no_concurrent_commit_claim(self):
        d=fixture();a=self.check(d);b=self.check(d)
        self.assertEqual(a['receipt']['expected_version'],b['receipt']['expected_version'])
        self.assertEqual(a['next_ledger'].seen_attempts,(d['intent'].attempt_ref,))
        # Two pure proposals can agree; only the host's CAS may commit one.
        d['ledger']=replace(d['ledger'],attempts=2,seen_attempts=('a'*64,'f'*64),last_attempt='f'*64)
        self.check(d,'ATTEMPT_REPLAY')
        d['ledger']=replace(d['ledger'],attempts=1,seen_attempts=(),last_attempt='f'*64)
        self.check(d,'ATTEMPT_HISTORY_INCOMPLETE')

    def test_critical_capability_and_wrong_method(self):
        d=fixture();d['capability']=replace(d['capability'],critical=True)
        self.check(d,'CRITICAL_INFRASTRUCTURE_REQUIRES_OWNER')
        self.check(fixture(condition='SERVICE_FAILED'),'METHOD_DIAGNOSIS_MISMATCH')

    def test_manual_unknown_and_host_cancel_never_admit(self):
        d=fixture(condition='UNKNOWN',method='MANUAL_RECOVERY')
        d['admission']=lambda t:self.fail('manual proposal must not enter admission')
        self.check(d,'OWNER_INTERVENTION_REQUIRED')
        d=fixture();d['cancelled']=True
        self.check(d,'CANCELLED_BY_HOST')

    def test_tampered_intent_and_admission_digest(self):
        d=fixture();d['intent']=replace(d['intent'],method='RECONNECT')
        self.check(d,'INPUT_OR_IDENTITY_INVALID')
        d=fixture();original=d['admission'](d['task']);original['lease_ref']='0'*64
        self.check(d,'HOST_GRANT_ROUTE_RESOURCE_LEASE_NOT_WITNESSED')
