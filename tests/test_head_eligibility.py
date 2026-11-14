"""Synthetic controls only; canonical Host identity shared with AdmissionGate."""
import copy
from datetime import timedelta
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).parents[1]/'bin'))
import resource_decision_probe as fixture
from meta_harness import head_eligibility as h


def setup():
    task,packets,profiles,policy=fixture.fixture()
    original=fixture.host_for(task,packets,profiles)
    host=h.resources.Host(original.validate_task,original.authorize,original.verify_projection,original.witness)
    head=dict(base_ref=task['model_version'],adapter_ref='1'*64,revision_ref='2'*64,
              architecture='fixture-architecture',rank=8,alpha=16,targets=['q_proj'],runtime_ref='3'*64,node='node-b',backend='default')
    head['head_ref']=h.resources.sha(head)
    check=dict(head_ref=head['head_ref'],task_ref=h.resources.sha(task),generation=1,base_ref=head['base_ref'],
               architecture=head['architecture'],max_rank=16,targets=['q_proj'],runtime_ref=head['runtime_ref'],
               license_allowed=True,provenance_ref='4'*64,permission='ALLOWED',observed_at=fixture.NOW.isoformat(),origin='SYNTHETIC')
    return dict(task=task,heads=[head],checks=[check],packets=packets,profiles=profiles,policy=policy,host=host,
                verify_head=lambda a,b,t:a==head and b==check and t==task,now=fixture.NOW,generation=1)


class Eligibility(unittest.TestCase):
    def run_case(self,edit=lambda d:None):
        d=setup();edit(d);r=h.evaluate(**d)
        self.assertFalse(r['summary']['dispatch_authorized'])
        self.assertFalse(r['summary']['memory_promotion_authorized'])
        self.assertLess(len(h.resources.encode(r['summary'])),1024)
        return r

    def test_positive_only_simulates(self):
        r=self.run_case();self.assertEqual(r['summary']['state'],'SIMULATED_ELIGIBLE')
        self.assertEqual(r['summary']['candidate_count'],1)

    def test_determinism_and_no_input_mutation(self):
        d=setup();before=copy.deepcopy(d['heads']);a=h.evaluate(**d);b=h.evaluate(**d)
        self.assertEqual(a,b);self.assertEqual(d['heads'],before)

    def test_incompatible_rank_architecture_runtime_targets(self):
        for key,value in [('max_rank',4),('architecture','other'),('runtime_ref','9'*64),('targets',[])]:
            with self.subTest(key=key):
                r=self.run_case(lambda d:d['checks'][0].update({key:value}))
                self.assertEqual(r['details'][0]['cause'],'HEAD_RUNTIME_INCOMPATIBLE')

    def test_impostor_base(self):
        def edit(d):
            a=d['heads'][0];a['base_ref']='9'*64;a.pop('head_ref');a['head_ref']=h.resources.sha(a)
        self.assertEqual(self.run_case(edit)['details'][0]['cause'],'BASE_IDENTITY_MISMATCH')

    def test_manifest_tampered(self):
        self.assertEqual(self.run_case(lambda d:d['heads'][0].update(adapter_ref='9'*64))['summary']['cause'],'HEAD_MANIFEST_INVALID')

    def test_stale_and_future(self):
        for offset,cause in [(-121,'HEAD_EVIDENCE_STALE'),(1,'EVIDENCE_FUTURE')]:
            r=self.run_case(lambda d:d['checks'][0].update(observed_at=(fixture.NOW+timedelta(seconds=offset)).isoformat()))
            self.assertEqual(r['summary']['cause'],cause)

    def test_resources_missing(self):
        r=self.run_case(lambda d:d['profiles'].clear())
        self.assertEqual(r['summary']['state'],'ABSTAIN')

    def test_permission_revoked_and_license(self):
        for key,value,cause in [('permission','REVOKED','HEAD_PERMISSION_DENIED'),('license_allowed',False,'LICENSE_NOT_AUTHORIZED')]:
            self.assertEqual(self.run_case(lambda d:d['checks'][0].update({key:value}))['details'][0]['cause'],cause)

    def test_revoked_task_grant(self):
        def edit(d):
            old=d['host'];d['host']=h.resources.Host(old.validate_task,lambda t:None,old.verify_projection,old.witness)
        self.assertEqual(self.run_case(edit)['summary']['cause'],'PERMISSION_DENIED')

    def test_session_change_and_cache_other_head(self):
        for field in ('pin','cache'):
            def edit(d):d[field]={'base_ref':d['task']['model_version'],'adapter_ref':'9'*64,'generation':1}
            self.assertEqual(self.run_case(edit)['details'][0]['cause'],'SESSION_OR_CACHE_HEAD_MISMATCH')

    def test_generation_change(self):
        self.assertEqual(self.run_case(lambda d:d.update(generation=2))['details'][0]['cause'],'PROVENANCE_OR_GENERATION_MISMATCH')

    def test_witness_missing(self):
        self.assertEqual(self.run_case(lambda d:d.update(verify_head=lambda *a:False))['details'][0]['cause'],'HEAD_NOT_WITNESSED')

    def test_measured_claim_never_produces_simulation_or_grant(self):
        self.assertEqual(self.run_case(lambda d:d['checks'][0].update(origin='MEASURED'))['summary']['state'],'ABSTAIN')

    def test_bounds_duplicate_and_bool(self):
        for edit in (lambda d:d['heads'].append(copy.deepcopy(d['heads'][0])),lambda d:d.update(generation=True),lambda d:d.update(heads=d['heads']*33)):
            self.assertEqual(self.run_case(edit)['summary']['state'],'ABSTAIN')

    def test_no_io_dispatch_or_load(self):
        d=setup()
        with patch('builtins.open',side_effect=AssertionError('no files')),patch('socket.socket',side_effect=AssertionError('no network')),patch('subprocess.Popen',side_effect=AssertionError('no process')):
            r=h.evaluate(**d)
        self.assertEqual(r['summary']['state'],'SIMULATED_ELIGIBLE')
