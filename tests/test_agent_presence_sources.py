"""Independent host fixture sources, never a real cross-CLI E2E assertion."""
from dataclasses import replace,asdict
from datetime import timedelta
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from meta_harness import agent_presence_sources as s
from meta_harness import agent_presence as p
from meta_harness.readonly_mirror import ReadOnlyJournal
from meta_harness.execution_journal import ExecutionJournal
from meta_harness.delegation import Session,TokenBudget
from tests.test_agent_presence import setup as projection_fixture,NOW
from tests.test_meta_delegation import grant,result


def setup():
    d=projection_fixture();values=[d['declarations'],d['observation'],d['claim']]
    refs=['1'*64,d['observation'].source_ref,d['claim'].source_ref]
    reads=[[],[],[]]
    sources=[]
    for index in range(3):
        def read(i=index):reads[i].append(1);return values[i]
        def attest(value,selection,i=index):return value==values[i] and selection==d['selection']
        sources.append(s.Source(refs[index],read,attest))
    adapter=s.PresenceSources(d['selection'],*sources,independent=lambda *_:True,
                allow_publication=d['allow_publication'],verify_capability=d['verify_capability'],now=lambda:NOW)
    return adapter,values,reads,d


class SourceTests(unittest.TestCase):
    def check(self,a,state='CAPTURED',cause=None):
        out=a.capture();r=out['capture']
        self.assertEqual(r['state'],state);self.assertEqual(r['authority'],'none');self.assertIs(r['ownerReply'],False)
        self.assertLess(len(s.encode(r)),1024)
        self.assertIn('authenticated_agent_source_binding',r['unknowns'])
        self.assertEqual(r['capture_ref'],s.sha({k:v for k,v in r.items() if k!='capture_ref'}))
        if cause:self.assertEqual(r['cause'],cause)
        if state=='NO_DATA':self.assertIsNone(out['snapshot'])
        else:
            self.assertEqual(out['snapshot']['authority'],'none')
            self.assertEqual(r['projection_state'],out['snapshot']['state'])
            self.assertEqual(out['snapshot']['liveness'],'NO_DATA(process_liveness_not_proven)')
        return out

    def test_three_sources_deterministic_no_authority(self):
        a,v,reads,d=setup();first=self.check(a);second=self.check(a)
        self.assertEqual(first,second);self.assertEqual([len(x) for x in reads],[6,6,6])
        self.assertEqual(first['snapshot']['state'],'OBSERVED')

    def test_missing_independent_provenance_never_reads(self):
        a,v,reads,d=setup();a.independent=lambda *_:False
        self.check(a,'NO_DATA','INDEPENDENT_SOURCE_PROVENANCE_MISSING');self.assertEqual(reads,[[],[],[]])

    def test_duplicate_reader_or_source_ref_rejected(self):
        a,v,r,d=setup();cli,journal,mesa=a.sources
        for wrong in (replace(journal,ref=cli.ref),replace(journal,read=cli.read)):
            with self.assertRaises(ValueError):s.PresenceSources(d['selection'],cli,wrong,mesa,
                    independent=lambda *_:True,allow_publication=lambda _:True,verify_capability=lambda *_:True,now=lambda:NOW)

    def test_change_during_capture_is_rejected_without_mutating_input(self):
        a,v,r,d=setup();before=copy.deepcopy(v)
        old=a.sources[2];calls=[]
        def changed():
            calls.append(1)
            return replace(v[2],generation=2) if len(calls)==2 else v[2]
        a.sources=(a.sources[0],a.sources[1],replace(old,read=changed,attest=lambda *_:True))
        self.check(a,'NO_DATA','SOURCE_CHANGED_DURING_CAPTURE');self.assertEqual(v,before)

    def test_shared_mutable_source_cannot_rewrite_first_capture(self):
        a,v,r,d=setup();old=a.sources[0]
        def read():
            if r[0]:v[0][0]=replace(v[0][0],branch='other-branch')
            r[0].append(1);return v[0]
        a.sources=(replace(old,read=read),*a.sources[1:])
        self.check(a,'NO_DATA','SOURCE_CHANGED_DURING_CAPTURE')

    def test_source_ref_mismatch_and_revocation(self):
        a,v,r,d=setup();v[1]=replace(v[1],source_ref='0'*64)
        self.check(a,'NO_DATA','SOURCE_IDENTITY_MISMATCH')
        a,v,r,d=setup();seen=[]
        def independent(*_):seen.append(1);return len(seen)==1
        a.independent=independent;self.check(a,'NO_DATA','INDEPENDENT_SOURCE_PROVENANCE_REVOKED')
        a,v,r,d=setup();a.sources=(a.sources[0],replace(a.sources[1],attest=lambda *_:False),a.sources[2])
        self.check(a,'NO_DATA','SOURCE_NOT_WITNESSED')

    def test_claim_owner_or_head_disagreement_never_authorizes(self):
        a,v,r,d=setup();v[2]=replace(v[2],instance_ref='0'*64)
        self.assertEqual(self.check(a)['snapshot']['cause'],'CLAIM_OWNER_CHANGED')
        a,v,r,d=setup();v[1]=replace(v[1],selection=replace(v[1].selection,head='0'*40))
        self.assertEqual(self.check(a)['snapshot']['cause'],'EVIDENCE_SELECTION_OR_HEAD_MISMATCH')

    def test_clock_deadline_future_and_old_evidence(self):
        a,v,r,d=setup();times=iter([NOW,NOW+timedelta(seconds=16)])
        a.now=lambda:next(times,NOW+timedelta(seconds=16))
        self.check(a,'NO_DATA','CAPTURE_DEADLINE_EXCEEDED')
        a,v,r,d=setup();times=iter([NOW,NOW-timedelta(seconds=1)])
        a.now=lambda:next(times,NOW-timedelta(seconds=1))
        self.check(a,'NO_DATA','CAPTURE_CLOCK_INVALID_OR_FUTURE')
        a,v,r,d=setup();a.now=lambda:NOW+timedelta(seconds=16)
        out=self.check(a);self.assertEqual(out['snapshot']['state'],'STALE')

    def test_omissions_and_private_exceptions(self):
        a,v,r,d=setup();v[0][0]=replace(v[0][0],branch='PRIVATE_BRANCH',omissions=('branch',))
        self.assertNotIn('PRIVATE_BRANCH',str(self.check(a)))
        a,v,r,d=setup()
        def fail():raise OSError('PRIVATE_ERROR')
        a.sources=(replace(a.sources[0],read=fail),*a.sources[1:])
        self.assertNotIn('PRIVATE_ERROR',str(self.check(a,'NO_DATA','SOURCE_UNAVAILABLE_OR_HOST_ERROR')))

    def test_real_readonly_journal_io_with_synthetic_original_binding(self):
        # Native SQLite read in an isolated private fixture; no new journal schema,
        # no receipt relabelling, no actual CLI/session-source authentication claim.
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'journal.sqlite';j=ExecutionJournal.create(path)
            d=projection_fixture();t=d['observation'].task
            session=Session(grant,TokenBudget(128),journal=j,clock=lambda:1)
            receipt=session.execute(t,result,observed_at=NOW.strftime('%Y-%m-%dT%H:%M:%SZ'))
            original=replace(d['observation'],receipt=receipt)
            ro=ReadOnlyJournal(path);fingerprint=hashlib.sha256(path.read_bytes()).hexdigest()
            def read_journal():
                native=ro.lookup(t['run_id'],s.sha(t))
                if native!=original.receipt:raise ValueError('original_binding_missing')
                return replace(original,receipt=native)
            a,v,r,d=setup();v[1]=original
            a.sources=(a.sources[0],s.Source(original.source_ref,read_journal,
                        lambda o,sel:o==original and sel==original.selection and ro.attests(o.receipt,s.sha(o.task),o.task['run_id'])),a.sources[2])
            self.assertEqual(self.check(a)['snapshot']['state'],'OBSERVED')
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),fingerprint)
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()),['journal.sqlite'])
            # Without the original context capability the same native bytes do not qualify.
            a.sources=(a.sources[0],replace(a.sources[1],attest=lambda *_:False),a.sources[2])
            self.check(a,'NO_DATA','SOURCE_NOT_WITNESSED')

    def test_late_source_change_and_cross_source_alias_race(self):
        a,v,r,d=setup();old=a.sources[2];calls=[]
        def late():
            calls.append(1);return replace(v[2],generation=2) if len(calls)>=3 else v[2]
        a.sources=(a.sources[0],a.sources[1],replace(old,read=late,attest=lambda *_:True))
        self.check(a,'NO_DATA','SOURCE_CHANGED_DURING_CAPTURE')
        a,v,r,d=setup();old=a.sources[1];calls=[]
        def mutate_other():
            calls.append(1)
            if len(calls)==1:v[0][0]=replace(v[0][0],branch='changed-after-cli-attestation')
            return v[1]
        a.sources=(a.sources[0],replace(old,read=mutate_other),a.sources[2])
        self.check(a,'NO_DATA','SOURCE_CHANGED_DURING_CAPTURE')
