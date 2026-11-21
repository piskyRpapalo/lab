"""Pure synthetic fixtures; does NOT impersonate a LAB host attestor.

The integration gate must separately call the real LAB delegation.verify and
Session.attests; these fixtures test the non-authoritative mathematical layer.
"""
import datetime as dt
import hashlib
import json
import unittest

from meta_harness.ho_lab_sonification import canonical, project

AT = dt.datetime(2026, 11, 21, 0, 25, tzinfo=dt.timezone.utc)


def fixture(model, samples):
    blob = canonical({'model_ref': model, 'measure_kind': 'latency', 'unit': 'ms', 'samples': samples})
    receipt = {
        'schema': 'preceptoros.meta-receipt/1', 'phase': 'complete',
        'failure_class': 'NONE', 'outcome': 'KNOWN',
        'confidence_basis': 'synthetic', 'specialist': model,
        'model_version': 'a' * 64, 'receipt_ref': 'b' * 64,
        'observed_at': '2026-11-21T00:24:00Z',
        'measurement': {'grade': 'NOT_EVALUATED',
                        'output_sha256': hashlib.sha256(blob).hexdigest(), 'tokens': 0}
    }
    return receipt, blob


def run_pair(receipt, blob, **kwargs):
    return project(receipt, blob, verify_receipt=lambda r: True,
                   attest_receipt=lambda r: True, host_read_time=AT, **kwargs)


class PureSoundExperiment(unittest.TestCase):
    def test_model_a_fixed_frequencies(self):
        p = run_pair(*fixture('model-a', [40, 80, 120, 160]))
        self.assertEqual([s['hz'] for s in p['record']['series']], [308, 396, 484, 572])
        self.assertEqual(p['state'], 'SIMULATED')
        self.assertFalse(p['playback_authorized'])

    def test_model_b_fixed_frequencies(self):
        p = run_pair(*fixture('model-b', [60, 90, 110, 130]))
        self.assertEqual([s['hz'] for s in p['record']['series']], [352, 418, 462, 506])

    def test_exact_semantic_digest_and_projection_parity(self):
        x = fixture('model-a', [40, 80, 120, 160])
        p, q = run_pair(*x), run_pair(*x)
        self.assertEqual(p, q)
        self.assertEqual(p['semantic_ref'], q['semantic_ref'])
        self.assertEqual({v['state_ref'] for v in p['views'].values()}, {p['semantic_ref']})

    def test_no_verifiers_fails_closed(self):
        r,b = fixture('model-a', [40,80,120,160])
        self.assertEqual(project(r,b,verify_receipt=None,attest_receipt=None,
                                 host_read_time=AT)['cause'], 'independent_lab_verifiers_missing')

    def test_real_host_attestation_is_not_self_hash(self):
        r,b = fixture('model-a', [40,80,120,160])
        got = project(r,b,verify_receipt=lambda r:True,attest_receipt=lambda r:False,
                      host_read_time=AT)
        self.assertEqual(got['cause'], 'lab_host_witness_missing')

    def test_zero_is_a_real_valid_sample_not_missing(self):
        p = run_pair(*fixture('model-a', [0, 0, 40, 80]))
        self.assertEqual([s['hz'] for s in p['record']['series']], [220,220,308,396])

    def test_negative_rejected(self):
        self.assertEqual(run_pair(*fixture('model-a', [40,-1,80,120]))['cause'],
                         'lab_sample_invalid_or_out_of_scale')

    def test_nan_rejected(self):
        r,b = fixture('model-a', [40,80,120,160])
        bad = b'{"model_ref":"model-a","measure_kind":"latency","unit":"ms","samples":[NaN,80,120,160]}'
        r['measurement']['output_sha256'] = hashlib.sha256(bad).hexdigest()
        self.assertEqual(run_pair(r,bad)['cause'],'lab_artifact_or_time_invalid')

    def test_infinite_rejected(self):
        for nonfinite in ('Infinity', '-Infinity'):
            r,b = fixture('model-a', [40,80,120,160])
            bad = ('{"model_ref":"model-a","measure_kind":"latency","unit":"ms","samples":['+nonfinite+',80,120,160]}').encode()
            r['measurement']['output_sha256'] = hashlib.sha256(bad).hexdigest()
            self.assertEqual(run_pair(r,bad)['cause'],'lab_artifact_or_time_invalid')

    def test_missing_sample_rejected_no_sound(self):
        p = run_pair(*fixture('model-a', []))
        self.assertEqual(p['cause'],'lab_samples_missing_or_wrong_count')
        self.assertEqual(p['audio_events'],[])

    def test_missing_artifact_rejected(self):
        r,b=fixture('model-a',[40,80,120,160])
        self.assertEqual(run_pair(r,b'')['cause'],'lab_sample_artifact_sha_mismatch')

    def test_mutation_sha_rejected(self):
        r,b=fixture('model-a',[40,80,120,160])
        altered=b.replace(b'120',b'140')
        self.assertEqual(run_pair(r,altered)['cause'],'lab_sample_artifact_sha_mismatch')

    def test_model_identity_swap_denied(self):
        r,b=fixture('model-a',[40,80,120,160])
        r['specialist']='model-b'
        self.assertEqual(run_pair(r,b)['cause'],'lab_model_identity_mismatch')

    def test_future_timestamp_rejected(self):
        r,b=fixture('model-a',[40,80,120,160])
        r['observed_at']='2027-01-01T00:00:00Z'
        self.assertEqual(run_pair(r,b)['cause'],'lab_observation_from_future')

    def test_fractional_second_past_ttl_is_stale(self):
        r,b=fixture('model-a',[40,80,120,160])
        now=dt.datetime(2026,11,21,0,26,0,1,tzinfo=dt.timezone.utc)
        p=project(r,b,verify_receipt=lambda r:True,attest_receipt=lambda r:True,
                  host_read_time=now)
        self.assertEqual(p['state'],'STALE')
        self.assertEqual(p['record']['age_s'],121)
        self.assertEqual(p['views']['sound_proposal']['notes'],[])

    def test_caller_cannot_widen_source_freshness_ceiling(self):
        r,b=fixture('model-a',[40,80,120,160])
        self.assertEqual(run_pair(r,b,max_age_s=600)['cause'],
                         'host_clock_or_freshness_policy_invalid')

    def test_stale_is_silent(self):
        r,b=fixture('model-a',[40,80,120,160])
        r['observed_at']='2026-11-20T00:00:00Z'
        p=run_pair(r,b)
        self.assertEqual(p['state'],'STALE')
        self.assertEqual(p['views']['sound_proposal']['notes'],[])
        self.assertIn('STALE:',p['views']['speech']['text'])

    def test_out_of_scale_not_silently_clamped(self):
        self.assertEqual(run_pair(*fixture('model-a',[40,220,120,160]))['cause'],
                         'lab_sample_invalid_or_out_of_scale')

    def test_duplicate_json_key_rejected(self):
        r,b=fixture('model-a',[40,80,120,160])
        bad=b'{"model_ref":"model-a","model_ref":"model-b","measure_kind":"latency","unit":"ms","samples":[40,80,120,160]}'
        r['measurement']['output_sha256']=hashlib.sha256(bad).hexdigest()
        self.assertEqual(run_pair(r,bad)['cause'],'lab_artifact_or_time_invalid')

    def test_non_integer_measure_rejected(self):
        self.assertEqual(run_pair(*fixture('model-a',[40.5,80,120,160]))['cause'],
                         'lab_sample_invalid_or_out_of_scale')

    def test_model_supplied_playback_grant_field_rejected(self):
        r,b=fixture('model-a',[40,80,120,160])
        injected=canonical({'model_ref':'model-a','measure_kind':'latency','unit':'ms','samples':[40,80,120,160],
                            'playback_permission':'GRANTED'})
        r['measurement']['output_sha256']=hashlib.sha256(injected).hexdigest()
        self.assertEqual(run_pair(r,injected)['cause'],'lab_measurement_fields_invalid')

    def test_measurement_basis_never_grants_playback(self):
        r,b=fixture('model-a',[40,80,120,160])
        r['confidence_basis']='public_deterministic_reference'
        p=run_pair(r,b)
        self.assertEqual(p['state'],'NO_DATA')
        self.assertEqual(p['cause'],'lab_physical_measurement_witness_missing')
        self.assertFalse(p['playback_authorized'])
        self.assertEqual(p['audio_events'], [])

    def test_unit_swap_rejected(self):
        r,b=fixture('model-a',[40,80,120,160])
        changed=canonical({'model_ref':'model-a','measure_kind':'latency',
                           'unit':'s','samples':[40,80,120,160]})
        r['measurement']['output_sha256']=hashlib.sha256(changed).hexdigest()
        self.assertEqual(run_pair(r,changed)['cause'],'lab_measure_kind_or_unit_invalid')

    def test_measure_kind_swap_rejected(self):
        r,b=fixture('model-a',[40,80,120,160])
        changed=canonical({'model_ref':'model-a','measure_kind':'temperature',
                           'unit':'ms','samples':[40,80,120,160]})
        r['measurement']['output_sha256']=hashlib.sha256(changed).hexdigest()
        self.assertEqual(run_pair(r,changed)['cause'],'lab_measure_kind_or_unit_invalid')

    def test_protocol_roundtrip_basis_not_physical(self):
        r,b=fixture('model-a',[40,80,120,160])
        r['confidence_basis']='protocol_roundtrip'
        p=run_pair(r,b)
        self.assertEqual(p['state'],'NO_DATA')
        self.assertEqual(p['cause'],'lab_physical_measurement_witness_missing')

    def test_playback_never_authorized(self):
        p=run_pair(*fixture('model-a',[40,80,120,160]))
        self.assertFalse(p['views']['sound_proposal']['playback_authorized'])
        self.assertFalse(p['views']['sound_proposal']['actual_audio'])



class LabHarnessIndependentWitness(unittest.TestCase):
    """Real LAB validation/attestation call path; dispatch is strictly synthetic."""
    def _fixture(self, basis='synthetic'):
        import time
        from meta_harness.delegation import Session, TokenBudget, sha, verify
        blob=canonical({'model_ref':'model-a','measure_kind':'latency','unit':'ms',
                        'samples':[40,80,120,160]})
        task={'schema':'preceptoros.meta-task/1','task_id':'ho-sound-a','run_id':'ho-fixture-a',
              'specialist':'model-a','model_version':'a'*64,'source':'local',
              'input_sha256':hashlib.sha256(blob).hexdigest(),'max_tokens':16,
              'timeout_ms':1000,'depth':0,'privacy':'LOCAL_ONLY','transport':'local_function'}
        counts={'dispatch':0}
        def authority(t):
            return {'approved':True,'task_sha256':sha(t),'approval_ref':'b'*64,
                    'expires_ns':time.monotonic_ns()+1000000000,'max_tokens':16,
                    'max_ms':1000,'max_depth':0,'local_only':True}
        def dispatch(t,cancelled):
            counts['dispatch']+=1
            return {'model_version':t['model_version'],
                    'output_sha256':hashlib.sha256(blob).hexdigest(),
                    'tokens':0,'grade':'NOT_EVALUATED','basis':basis}
        session=Session(authority, TokenBudget(64))
        receipt=session.execute(task,dispatch,observed_at='2026-11-21T00:24:00Z')
        return blob,task,session,receipt,counts,verify

    def test_real_lab_receipt_synthetic_projection_inert(self):
        blob,task,session,receipt,counts,verify=self._fixture()
        self.assertTrue(verify(receipt))
        self.assertTrue(session.attests(receipt,task))
        p=project(receipt,blob,verify_receipt=verify,
                  attest_receipt=lambda r:session.attests(r,task),host_read_time=AT)
        self.assertEqual(p['state'],'SIMULATED')
        self.assertEqual(counts['dispatch'],1)
        self.assertFalse(p['execution_authorized'])
        self.assertFalse(p['playback_authorized'])
        self.assertEqual(p['record']['receipt_ref'],receipt['receipt_ref'])

    def test_foreign_lab_session_is_not_witness(self):
        from meta_harness.delegation import Session,TokenBudget
        blob,task,session,receipt,counts,verify=self._fixture()
        foreign=Session(lambda t:None,TokenBudget(64))
        self.assertFalse(foreign.attests(receipt,task))
        p=project(receipt,blob,verify_receipt=verify,
                  attest_receipt=lambda r:foreign.attests(r,task),host_read_time=AT)
        self.assertEqual(p['cause'],'lab_host_witness_missing')
        self.assertEqual(p['audio_events'],[])

    def test_real_lab_signed_receipt_does_not_cover_mutated_artifact(self):
        blob,task,session,receipt,counts,verify=self._fixture()
        p=project(receipt,blob.replace(b'120',b'140'),verify_receipt=verify,
                  attest_receipt=lambda r:session.attests(r,task),host_read_time=AT)
        self.assertEqual(p['cause'],'lab_sample_artifact_sha_mismatch')

    def test_real_lab_roundtrip_basis_does_not_become_physical(self):
        blob,task,session,receipt,counts,verify=self._fixture('protocol_roundtrip')
        p=project(receipt,blob,verify_receipt=verify,
                  attest_receipt=lambda r:session.attests(r,task),host_read_time=AT)
        self.assertEqual(p['state'],'NO_DATA')
        self.assertEqual(p['cause'],'lab_physical_measurement_witness_missing')

if __name__ == '__main__':
    unittest.main()
