import copy
import unittest
from meta_harness.a2a_correlation import correlate, synthetic_fixture
from meta_harness.delegation import encode, sha

class A2ACorrelationTests(unittest.TestCase):
    def setUp(self):
        self.req,self.obs=synthetic_fixture()
        self.now='2026-11-15T02:50:09Z'

    def run_case(self,request=None,observation=None,witness='default',now=None,seen=()):
        callback=(lambda *args:True) if witness=='default' else witness
        return correlate(self.req if request is None else request,
                         self.obs if observation is None else observation,
                         now=now if now is not None else self.now,
                         witness=callback,seen_request_refs=seen)

    def tweak(self,key,value):
        obs=copy.deepcopy(self.obs);obs[key]=value
        return self.run_case(observation=obs)

    def test_ack_unverified(self):
        x=self.run_case();self.assertEqual(x['state'],'CORRELATED_UNVERIFIED')
        self.assertEqual(x['permissions'],'none');self.assertEqual(x['authority'],'none')
        self.assertIn('NO_DATA',x['authentication'])

    def test_not_real_junie(self):
        self.assertIn('synthetic',self.req['trace_id'])
        self.assertEqual(self.run_case()['evidence'],'HOST_SUPPLIED_UNVERIFIED')

    def test_grant_refused(self):
        req=copy.deepcopy(self.req);req['human_signoff']=True
        self.assertEqual(self.run_case(request=req)['state'],'NO_DATA')
        req=copy.deepcopy(self.req);req['mode']='EXEC'
        self.assertEqual(self.run_case(request=req)['state'],'NO_DATA')

    def test_missing_witness(self):
        self.assertEqual(self.run_case(witness=None)['cause'],'host_capture_missing')

    def test_false_witness(self):
        self.assertEqual(self.run_case(witness=lambda *x:False)['state'],'NO_DATA')

    def test_witness_error_scrubbed(self):
        def bad(*x):raise ValueError('FAKE_SECRET')
        r=self.run_case(witness=bad)
        self.assertEqual(r['cause'],'host_capture_error')
        self.assertNotIn('FAKE_SECRET',repr(r))

    def test_swapped_agent(self):
        self.assertEqual(self.tweak('agent','hexelion')['cause'],'response_binding_mismatch')
    def test_swapped_session(self):
        self.assertEqual(self.tweak('session_ref','0'*64)['cause'],'response_binding_mismatch')
    def test_swapped_epoch(self):
        self.assertEqual(self.tweak('generation',2)['cause'],'response_binding_mismatch')
    def test_swapped_source(self):
        self.assertEqual(self.tweak('source_ref','0'*64)['cause'],'response_binding_mismatch')
    def test_swapped_request(self):
        self.assertEqual(self.tweak('request_ref','0'*64)['cause'],'response_binding_mismatch')

    def test_replay_is_detected_if_provided(self):
        self.assertEqual(self.run_case(seen=[sha(self.req)])['cause'],'replay_observed')
    def test_replay_store_not_claimed(self):
        self.assertIn('NO_DATA',self.run_case()['replay'])

    def test_future(self):
        self.assertEqual(self.run_case(now='2026-11-15T02:50:02Z')['cause'],'invalid_chronology')
    def test_expired(self):
        self.assertEqual(self.run_case(now='2026-11-15T02:51:01Z')['cause'],'expired')

    def test_oversized_ttl(self):
        req=copy.deepcopy(self.req);req['expires_at']='2026-11-15T04:00:00Z'
        obs=copy.deepcopy(self.obs);obs['request_ref']=sha(req)
        self.assertEqual(self.run_case(request=req,observation=obs)['cause'],'invalid_lifetime')

    def test_nack_not_ack(self):
        self.assertEqual(self.tweak('kind','NACK')['state'],'DECLINED_UNVERIFIED')
    def test_error_not_ack(self):
        self.assertEqual(self.tweak('kind','ERROR')['state'],'NO_DATA')
    def test_nonzero_ack_not_ack(self):
        self.assertEqual(self.tweak('exit_code',7)['state'],'NO_DATA')
    def test_boolean_exit_not_int(self):
        self.assertEqual(self.tweak('exit_code',True)['state'],'NO_DATA')
    def test_boolean_epoch_not_int(self):
        self.assertEqual(self.tweak('generation',True)['state'],'NO_DATA')

    def test_raw_tool_output_rejected(self):
        obs=copy.deepcopy(self.obs);obs['raw']='SECRET_FIXTURE'
        r=self.run_case(observation=obs)
        self.assertEqual(r['state'],'NO_DATA');self.assertNotIn('SECRET_FIXTURE',repr(r))
    def test_raw_prompt_rejected(self):
        req=copy.deepcopy(self.req);req['prompt']='SECRET_FIXTURE'
        r=self.run_case(request=req)
        self.assertEqual(r['state'],'NO_DATA');self.assertNotIn('SECRET_FIXTURE',repr(r))

    def test_invalid_kind_not_verified(self):
        self.assertEqual(self.tweak('kind','VERIFIED')['state'],'NO_DATA')
    def test_reply_digest_no_identity(self):
        self.assertEqual(self.tweak('reply_ref','f'*64)['state'],'CORRELATED_UNVERIFIED')
    def test_bad_replay_list(self):
        self.assertEqual(self.run_case(seen=['bad'])['state'],'NO_DATA')
    def test_missing_observation(self):
        self.assertEqual(self.run_case(observation={})['state'],'NO_DATA')
    def test_invalid_timestamp(self):
        self.assertEqual(self.tweak('observed_at','2026-11-15T02:50:07+00:00')['state'],'NO_DATA')
    def test_no_command_override(self):
        req=copy.deepcopy(self.req);req['command']='/bin/sh'
        self.assertEqual(self.run_case(request=req)['state'],'NO_DATA')
    def test_mutating_witness_cannot_change_validated_evidence(self):
        req,obs=synthetic_fixture()
        def adversary(r,o):
            o['agent']='hexelion'
            o['session_ref']='0'*64
            r['scope_ref']='0'*64
            return True
        out=correlate(req,obs,now=self.now,witness=adversary)
        self.assertEqual(out['state'],'CORRELATED_UNVERIFIED')
        self.assertEqual(out['observation_ref'],sha(obs))
        self.assertEqual(out['request_ref'],sha(req))
        self.assertEqual(obs['agent'],'junie')
        self.assertEqual(req['scope_ref'],'c'*64)

    def test_external_alias_mutation_cannot_change_pinned_receipt(self):
        req,obs=synthetic_fixture()
        expected=sha(obs)
        def adversary(r,o):
            obs['agent']='hexelion'
            obs['session_ref']='0'*64
            return True
        out=correlate(req,obs,now=self.now,witness=adversary)
        self.assertEqual(out['state'],'CORRELATED_UNVERIFIED')
        self.assertEqual(out['observation_ref'],expected)

    def test_untrusted_deepcopy_hook_never_runs(self):
        class Hostile:
            called=False
            def __deepcopy__(self,memo):
                self.called=True
                raise RuntimeError('unsafe_hook')
        bad=Hostile()
        req=copy.deepcopy(self.req);req['agent']=bad
        out=self.run_case(request=req)
        self.assertEqual(out['state'],'NO_DATA')
        self.assertFalse(bad.called)

    def test_non_dict_envelope_hook_never_runs(self):
        class Hostile:
            called=False
            def __deepcopy__(self,memo):
                self.called=True
                raise RuntimeError('unsafe_hook')
        bad=Hostile()
        out=self.run_case(request=bad)
        self.assertEqual(out['state'],'NO_DATA')
        self.assertFalse(bad.called)

    def test_deterministic_compact_receipt(self):
        r=self.run_case();self.assertEqual(r,self.run_case())
        self.assertLess(len(encode(r)),1024)
        self.assertEqual(r['receipt_ref'],sha({k:v for k,v in r.items() if k!='receipt_ref'}))
if __name__=='__main__':unittest.main()
