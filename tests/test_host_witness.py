import copy
from datetime import datetime, timedelta, timezone
import unittest

from meta_harness.delegation import sha
from meta_harness.host_witness import HostWitness

NOW = datetime(2026,11,13,12,0,tzinfo=timezone.utc)


def fixture():
    r = {'schema':'preceptoros.lab.uncertainty-ack/1', 'journal_id':'a'*64, 'run_id':'run-one',
         'task_ref':'b'*64, 'prior_ref':'c'*64, 'evidence_ref':'d'*64, 'authority_ref':'e'*64,
         'observed_at':'2026-11-13T12:00:00Z', 'decision':'ACK_UNKNOWN_RETAIN_RESERVATION',
         'no_retry':True, 'reservation_release':False}
    r['resolution_ref'] = sha(r)
    return r


class HostWitnessTests(unittest.TestCase):
    def setUp(self): self.host=HostWitness('a'*64,'b'*64,now=lambda:NOW)
    def test_valid_shape_never_fabricates_authority_or_fence(self):
        r=fixture(); d=self.host.diagnose(r)
        self.assertEqual(d['cause'],'human_authority_and_durable_fence_unavailable')
        for fn in (self.host.human_authorize,self.host.quiescence,self.host.resolution_witness):
            self.assertIs(fn(r),False)
    def test_wrong_identity_and_expired_or_future_evidence(self):
        for key,value,cause in [('journal_id','0'*64,'journal_identity_mismatch'),
                ('task_ref','0'*64,'task_identity_mismatch'),
                ('observed_at','2026-11-13T11:57:59Z','evidence_expired'),
                ('observed_at','2026-11-13T12:00:01Z','evidence_from_future')]:
            r=fixture();r[key]=value;r['resolution_ref']=sha({k:v for k,v in r.items() if k!='resolution_ref'})
            self.assertEqual(self.host.diagnose(r)['cause'],cause)
            self.assertFalse(self.host.resolution_witness(r))
    def test_forged_revoked_pid_or_resealed_claims_never_authorize(self):
        for key,value in [('approved',True),('revoked',False),('pid',123),('process_missing',True)]:
            r=fixture();r[key]=value;r['resolution_ref']=sha({k:v for k,v in r.items() if k!='resolution_ref'})
            self.assertEqual(self.host.diagnose(r)['cause'],'record_invalid')
            self.assertFalse(self.host.quiescence(r))
        r=fixture();r['authority_ref']='0'*64
        self.assertEqual(self.host.diagnose(r)['cause'],'record_invalid')
    def test_restart_recreates_same_fail_closed_verdict(self):
        other=HostWitness('a'*64,'b'*64,now=lambda:NOW)
        self.assertEqual(other.diagnose(fixture()),self.host.diagnose(fixture()))
