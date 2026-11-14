"""Synthetic TEST DOUBLES only; no local checkpoint/accelerator fact is asserted."""
from dataclasses import asdict, replace
from datetime import timedelta
import copy
import unittest
from unittest.mock import patch
from meta_harness import c2c_preflight as c


def setup():
    from tests.test_resource_admission import AdmissionTests, fixtures
    from tests.test_meta_delegation import grant
    task,packets,profiles,policy,gate,session,worker,calls = AdmissionTests().fixture()
    receiver=c.Model(c.RECEIVER,'1'*40,task['model_version'],'2'*64,'Qwen3ForCausalLM',c.KV(28,8,128,'bfloat16','BHSD'))
    sharer=c.Model(c.SHARER,'3'*40,'4'*64,'5'*64,'Qwen2ForCausalLM',c.KV(28,2,128,'bfloat16','BHSD'))
    fuser=c.Fuser(c.FUSER,c.FUSER_PATH,'6'*40,'7'*64,c.sha([asdict(receiver),asdict(sharer)]),'8'*64,'9'*64)
    pair=c.Pair(receiver,sharer,fuser,'a'*40)
    pin=c.Pin(c.sha(asdict(pair)),'b'*64,fuser.runtime_ref,1)
    evaluation=c.Evaluation(('receiver','sharer','text','c2c'),'c'*64,'d'*64,'e'*64,True,True,True)
    task['input_sha256']=c.input_ref(pair,pin,evaluation)
    profiles[0]['task_profile_ref']=c.resources.profile_key(task)
    profiles[0].pop('profile_ref');profiles[0]['profile_ref']=c.resources.sha(profiles[0])
    # Explicit test-only re-pin of the whole pair resource profile, never a live witness.
    gate.witness=lambda p,t,r:p in profiles and t==task
    assert gate(task,grant(task),worker,lambda:False)
    host=c.resources.Host(lambda t:t==task,lambda t:'f'*64 if t==task else None,
                          lambda p:p in packets,lambda p,t,r:p in profiles and t==task)
    witness=c.Witness(pin.pair_ref,c.sha(asdict(pin)),pin.node_ref,packets[0]['record']['source_ref'],
                      fixtures.NOW.isoformat(),'MEASURED',True,True,True,True,True,True,'f'*64)
    return dict(task=task,pair=pair,pin=pin,evaluation=evaluation,witness=witness,packets=packets,
                profiles=profiles,policy=policy,host=host,now=fixtures.NOW,verify=lambda w,p,t:True,admission=gate.record)


class PreflightTests(unittest.TestCase):
    def run_case(self,d=None,cause=None):
        out=c.preflight(**(setup() if d is None else d))
        self.assertFalse(out['dispatch_authorized']);self.assertEqual(out['promotion'],'NOT_AUTHORIZED')
        self.assertLess(len(c.resources.encode(out)),1024)
        self.assertEqual(out['receipt_ref'],c.sha({k:v for k,v in out.items() if k!='receipt_ref'}))
        if cause:self.assertEqual(out['cause'],cause)
        return out

    def test_positive_uses_existing_gate_record_not_worker(self):
        self.assertEqual(self.run_case()['state'],'READY_FOR_ISOLATED_BENCH')

    def test_determinism_and_no_input_mutation(self):
        d=setup();before=copy.deepcopy(d['packets']);a=self.run_case(d);b=self.run_case(d)
        self.assertEqual(a,b);self.assertEqual(d['packets'],before)

    def test_wrong_pair_direction_or_model(self):
        d=setup();d['pair']=replace(d['pair'],receiver=d['pair'].sharer)
        self.run_case(d,'ARTIFACT_IDENTITY_OR_DIGEST_INVALID')

    def test_model_tag_and_mutable_revision_not_identity(self):
        for field,value in [('revision','main'),('weights_ref','qwen3:1.7b')]:
            d=setup();d['pair']=replace(d['pair'],receiver=replace(d['pair'].receiver,**{field:value}))
            self.run_case(d,'ARTIFACT_IDENTITY_OR_DIGEST_INVALID')

    def test_gguf_api_not_hf_kv_access(self):
        d=setup();d['pair']=replace(d['pair'],receiver=replace(d['pair'].receiver,format='GGUF'))
        self.run_case(d,'CHECKPOINT_FORMAT_UNSUPPORTED')

    def test_layout_architecture_dtype_and_bool_dimensions(self):
        for kv in (c.KV(28,2,128,'bfloat16','BHSD'),c.KV(28,8,128,'float16','BHSD'),
                   c.KV(28,8,128,'bfloat16','BSHD'),c.KV(True,8,128,'bfloat16','BHSD')):
            d=setup();d['pair']=replace(d['pair'],receiver=replace(d['pair'].receiver,kv=kv))
            self.run_case(d,'ARCHITECTURE_OR_KV_LAYOUT_MISMATCH')

    def test_fuser_trained_for_another_revision_or_head(self):
        d=setup();d['pair']=replace(d['pair'],receiver=replace(d['pair'].receiver,revision='0'*40))
        self.run_case(d,'FUSER_PAIR_OR_HEAD_MISMATCH')

    def test_generation_runtime_or_cache_pin_changed(self):
        for change in ({'generation':2},{'runtime_ref':'0'*64},{'pair_ref':'0'*64}):
            d=setup();d['pin']=replace(d['pin'],**change)
            self.run_case(d,'TASK_SESSION_OR_CACHE_PIN_MISMATCH')

    def test_checkpoint_url_not_local_bytes(self):
        d=setup();d['witness']=replace(d['witness'],checkpoints_local=False)
        self.run_case(d,'NO_DATA_LOCAL_CHECKPOINTS')

    def test_unbound_training_versions_and_host_runtime(self):
        for field,cause in [('training_revisions_bound','NO_DATA_FUSER_TRAINING_REVISIONS'),
                            ('runtime_compatible','NO_DATA_RUNTIME_HOST_COMPATIBILITY'),('kv_access','NO_DATA_KV_ACCESS')]:
            d=setup();d['witness']=replace(d['witness'],**{field:False});self.run_case(d,cause)

    def test_revoked_permission_and_license(self):
        for field,cause in [('permission_current','PERMISSION_DENIED'),('license_allowed','LICENSE_NOT_AUTHORIZED')]:
            d=setup();d['witness']=replace(d['witness'],**{field:False});self.run_case(d,cause)

    def test_stale_and_future_host_evidence(self):
        for delta,cause in [(-121,'HOST_EVIDENCE_STALE'),(1,'CLOCK_INVALID_OR_FUTURE')]:
            d=setup();d['witness']=replace(d['witness'],observed_at=(d['now']+timedelta(seconds=delta)).isoformat())
            self.run_case(d,cause)

    def test_forged_host_observation(self):
        d=setup();d['verify']=lambda *_:False;self.run_case(d,'PAIR_HOST_EVIDENCE_NOT_WITNESSED')
        d=setup();d['witness']=replace(d['witness'],node_ref='0'*64);self.run_case(d,'HOST_EVIDENCE_IDENTITY_MISMATCH')

    def test_missing_resources_or_forged_gpu_availability(self):
        d=setup();d['profiles']=[];self.run_case(d,'RESOURCE_TASK_RESOURCE_EVIDENCE_MISSING')
        d=setup();d['packets'][0]['record']['memory']['available_bytes']=1
        self.run_case(d,'RESOURCE_RESOURCE_SHORTFALL')

    def test_missing_revoked_or_transplanted_admission(self):
        for row in (None,{'authorized':True}):
            d=setup();d['admission']=lambda t:row;self.run_case(d,'HOST_ADMISSION_OR_LEASE_NOT_WITNESSED')
        d=setup();row=d['admission'](d['task']);row['task_ref']='0'*64
        row['admission_ref']=c.sha({k:v for k,v in row.items() if k!='admission_ref'})
        d['admission']=lambda t:row;self.run_case(d,'HOST_ADMISSION_OR_LEASE_NOT_WITNESSED')

        for field,value,reseal in [('lease_ref',None,True),('lease_ref','0'*64,False)]:
            d=setup();row=d['admission'](d['task']);row[field]=value
            if reseal:row['admission_ref']=c.sha({k:v for k,v in row.items() if k!='admission_ref'})
            d['admission']=lambda _:row
            self.run_case(d,'HOST_ADMISSION_OR_LEASE_NOT_WITNESSED')

    def test_wrong_physical_host_profile(self):
        d=setup();d['witness']=replace(d['witness'],resource_source_ref='0'*64)
        self.run_case(d,'ADMISSION_RESOURCE_PROFILE_OR_HOST_MISMATCH')

    def test_upstream_15_and_23_are_evaluation_constraints(self):
        for changes in ({'issue15_checkpoint_specific':False},{'issue23_no_assumed_gain':False},
                        {'baselines':('receiver','c2c')},{'synthetic_public_data_only':False}):
            d=setup();d['evaluation']=replace(d['evaluation'],**changes)
            d['task']['input_sha256']=c.input_ref(d['pair'],d['pin'],d['evaluation'])
            self.run_case(d,'UPSTREAM_NEGATIVE_EVALUATION_CONSTRAINTS_MISSING')

    def test_six_connected_nodes_still_abstain_without_witness(self):
        # Six opaque physical references; transport reachability supplies no authority.
        for n in range(1,7):
            d=setup();d['pin']=replace(d['pin'],node_ref=str(n)*64)
            d['task']['input_sha256']=c.input_ref(d['pair'],d['pin'],d['evaluation'])
            d['verify']=lambda *_:False
            self.assertEqual(self.run_case(d,'PAIR_HOST_EVIDENCE_NOT_WITNESSED')['state'],'ABSTAIN')

    def test_no_io_model_import_or_gpu(self):
        d=setup()
        with patch('socket.socket',side_effect=AssertionError('network')),patch('subprocess.Popen',side_effect=AssertionError('process')),patch('builtins.open',side_effect=AssertionError('file')):
            self.assertEqual(self.run_case(d)['state'],'READY_FOR_ISOLATED_BENCH')

    def test_bounded_invalid_input_and_private_callback_error(self):
        d=setup();d['head_inputs']=({},)*3;self.run_case(d,'INPUT_OR_HOST_CONTRACT_INVALID')
        d=setup();d['verify']=lambda *_:(_ for _ in ()).throw(ValueError('PRIVATE_CANARY'))
        self.assertNotIn('PRIVATE_CANARY',str(self.run_case(d)))

    def test_boolean_claims_are_strict_and_checkpoint_evidence_cannot_be_forged(self):
        d=setup();d['witness']=replace(d['witness'],checkpoints_local='true')
        self.run_case(d,'NO_DATA_LOCAL_CHECKPOINTS')
        d=setup();d['verify']=lambda *_:1
        self.run_case(d,'PAIR_HOST_EVIDENCE_NOT_WITNESSED')
        d=setup();d['profiles']=[{'padding':'x'*262144}]
        self.run_case(d,'INPUT_BOUND_EXCEEDED')

    def test_stale_admission_record(self):
        d=setup();d['witness']=replace(d['witness'],origin='SIMULATED')
        self.run_case(d,'RESOURCE_EVIDENCE_ORIGIN_MISMATCH')
        d=setup();row=d['admission'](d['task'])
        row['observed_at']=(d['now']-timedelta(seconds=121)).isoformat()
        row['admission_ref']=c.sha({k:v for k,v in row.items() if k!='admission_ref'})
        d['admission']=lambda _:row;self.run_case(d,'HOST_ADMISSION_STALE')

    def test_optional_lora_delegates_to_existing_head_evaluator(self):
        from tests.test_head_eligibility import setup as head_setup
        d=setup();spec=head_setup();manifest=spec['heads'][0]
        pair=replace(d['pair'],receiver=replace(d['pair'].receiver,head_ref=manifest['head_ref']))
        pair=replace(pair,fuser=replace(pair.fuser,models_ref=c.models_ref(pair)))
        d['pair']=pair;d['pin']=replace(d['pin'],pair_ref=c.sha(asdict(pair)))
        d['task']['input_sha256']=c.input_ref(pair,d['pin'],d['evaluation'])
        d['witness']=replace(d['witness'],pair_ref=d['pin'].pair_ref,pin_ref=c.sha(asdict(d['pin'])))
        self.run_case(d,'LORA_HEAD_EVIDENCE_MISSING')
        spec.update(task=d['task'],generation=d['pin'].generation,
                    pin=dict(base_ref=manifest['base_ref'],adapter_ref=manifest['adapter_ref'],head_ref=manifest['head_ref'],generation=d['pin'].generation))
        d['head_inputs']=(spec,)
        with patch.object(c.head_eligibility,'evaluate',wraps=c.head_eligibility.evaluate) as evaluate:
            self.run_case(d,'LORA_HEAD_NOT_ELIGIBLE');evaluate.assert_called_once()
        with patch.object(c.head_eligibility,'evaluate',return_value={'summary':{'state':'SIMULATED_ELIGIBLE'}}):
            self.run_case(d,'NO_DATA_LORA_PRODUCTION_ADMISSION')
