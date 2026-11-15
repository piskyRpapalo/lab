"""Opaque synthetic identities, Mesa claims and existing native Session receipts."""
from dataclasses import asdict,replace
from datetime import datetime,timedelta,timezone
import unittest
from unittest.mock import patch
from meta_harness import agent_presence as p
from meta_harness.delegation import Session,TokenBudget
from tests.test_meta_delegation import task,grant,result

NOW=datetime(2026,11,14,20,tzinfo=timezone.utc)

def setup(index=1,label='codex'):
    session=p.sha({'fixture_session':index});instance=p.sha({'fixture_instance':index})
    select=p.Selection(session,instance,1,'a'*64,'b'*64,p.sha({'fixture_tree':index}),'c'*40)
    claim=p.Claim('d'*64,session,instance,select.repo_ref,select.worktree_ref,'multiagent-p0','e'*64,1,NOW.isoformat(),True)
    declaration=p.Declaration(select,label,'lab','codex/presence-p0','multiagent-p0',p.sha(asdict(claim)),claim.scope_ref,NOW.isoformat(),NOW.isoformat())
    t=task();s=Session(grant,TokenBudget(128),clock=lambda:1)
    r=s.execute(t,result,observed_at=NOW.strftime('%Y-%m-%dT%H:%M:%SZ'))
    obs=p.Observation(select,declaration.claim_ref,'f'*64,t,r)
    cap=p.Capability('synthetic-task',p.sha(r),p.sha(t),claim.scope_ref)
    return dict(selection=select,declarations=[declaration],claim=claim,observation=obs,capabilities=[cap],now=NOW,
                allow_publication=lambda _:True,verify_claim=lambda c:c==claim,
                verify_observation=lambda o,d,c:s.attests(o.receipt,o.task) and o.selection==select and o.claim_ref==declaration.claim_ref and o.source_ref=='f'*64,verify_capability=lambda c,o:c==cap)


class PresenceTests(unittest.TestCase):
    def check(self,d,state,cause=None):
        out=p.project(**d);self.assertEqual(out['state'],state)
        self.assertEqual(out['authority'],'none');self.assertIs(out['ownerReply'],False)
        self.assertEqual(out['liveness'],'NO_DATA(process_liveness_not_proven)')
        self.assertIn('exclusive-writer-ownership',out['unknowns'])
        self.assertEqual(out['snapshot_ref'],p.sha({k:v for k,v in out.items() if k!='snapshot_ref'}))
        self.assertLess(len(p.encode(out)),16384)
        short=p.receipt(out);self.assertLess(len(p.encode(short)),1024)
        self.assertEqual(short['authority'],'none');self.assertIs(short['ownerReply'],False)
        if cause:self.assertEqual(out['cause'],cause)
        return out

    def test_01_two_agents_claiming_same_worktree(self):
        d=setup();peer=setup(2)['declarations'][0]
        peer=replace(peer,selection=replace(peer.selection,worktree_ref=d['selection'].worktree_ref))
        d['declarations'].append(peer)
        self.check(d,'NO_DATA','WORKTREE_CLAIM_CONFLICT')

    def test_02_disappearance_expires_without_inventing_offline(self):
        d=setup();d['now']=NOW+timedelta(seconds=16)
        self.check(d,'STALE','DECLARATION_STALE')
        d['declarations']=[];self.check(d,'NO_DATA','SELECTED_ACTIVATION_MISSING')

    def test_03_restart_does_not_inherit_old_activation(self):
        d=setup();d['declarations'][0]=replace(d['declarations'][0],selection=replace(d['selection'],instance_ref='0'*64))
        self.check(d,'NO_DATA','SELECTED_ACTIVATION_MISSING')
        d=setup();d['observation']=replace(d['observation'],selection=replace(d['selection'],instance_ref='0'*64))
        self.check(d,'NO_DATA','EVIDENCE_SELECTION_OR_HEAD_MISMATCH')

    def test_04_same_name_is_not_identity(self):
        a=setup(1,label='hexelion');b=setup(2,label='hexelion')
        a['declarations']+=b['declarations'];b['declarations']=list(a['declarations'])
        first=self.check(a,'OBSERVED');second=self.check(b,'OBSERVED')
        self.assertEqual(first['publication']['label'],second['publication']['label'])
        self.assertNotEqual(first['identity'],second['identity'])

    def test_05_mission_owner_change_invalidates_old_binding(self):
        d=setup();new=replace(d['claim'],session_ref='0'*64,generation=2)
        d['claim']=new;d['verify_claim']=lambda _:True
        self.check(d,'NO_DATA','CLAIM_OWNER_CHANGED')
        d=setup();d['claim']=replace(d['claim'],generation=2);d['verify_claim']=lambda _:True
        self.check(d,'NO_DATA','CLAIM_BINDING_MISMATCH')

    def test_06_receipt_from_another_head_or_clone_rejected(self):
        for changes in ({'head':'0'*40},{'clone_ref':'0'*64},{'generation':2}):
            d=setup();d['observation']=replace(d['observation'],selection=replace(d['selection'],**changes))
            self.check(d,'NO_DATA','EVIDENCE_SELECTION_OR_HEAD_MISMATCH')

    def test_07_private_source_omissions_never_transport_content(self):
        d=setup();secret='PRIVATE_SYNTHETIC_BRANCH'
        d['declarations'][0]=replace(d['declarations'][0],branch=secret,
                                     omissions=('branch','head','scope','capabilities','review'))
        out=self.check(d,'OBSERVED')
        self.assertNotIn(secret,str(out));self.assertIsNone(out['publication']['branch'])
        self.assertIsNone(out['publication']['head']);self.assertEqual(out['capabilities'],[])
        self.assertEqual(out['human_review'],'NO_DATA(review_status_unwitnessed)')
        d=setup();raw=asdict(d['declarations'][0]);raw['private_prompt']='PRIVATE_SYNTHETIC_PROMPT'
        d['declarations']=[raw];out=self.check(d,'NO_DATA','PUBLICATION_INVALID')
        self.assertNotIn('PRIVATE_SYNTHETIC_PROMPT',str(out))

    def test_08_old_execution_cannot_be_kept_active_by_new_heartbeat(self):
        d=setup();d['now']=NOW+timedelta(seconds=16)
        d['declarations'][0]=replace(d['declarations'][0],declared_at=d['now'].isoformat(),heartbeat_at=d['now'].isoformat())
        out=self.check(d,'STALE','EXECUTION_EVIDENCE_STALE')
        self.assertEqual(out['observed_at'],NOW.strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.assertFalse(out['has_recent_execution_evidence'])

    def test_declared_is_not_observed_or_a_mesa_assignment(self):
        d=setup();d['observation']=None;d['capabilities']=[]
        self.check(d,'DECLARED','EXECUTION_NOT_OBSERVED')
        d['claim']=None;out=self.check(d,'DECLARED','CLAIM_SOURCE_NOT_WITNESSED')
        self.assertIsNone(out['claim_ref']);self.assertFalse(out['has_recent_execution_evidence'])

    def test_unknown_native_result_is_not_capability(self):
        d=setup();s=Session(grant,TokenBudget(128),clock=lambda:1)
        def uncertain(*_):raise OSError('PRIVATE_CANARY')
        t=d['observation'].task;r=s.execute(t,uncertain,observed_at=NOW.strftime('%Y-%m-%dT%H:%M:%SZ'))
        d['observation']=replace(d['observation'],receipt=r);d['verify_observation']=lambda o,*_:s.attests(o.receipt,o.task)
        self.check(d,'NO_DATA','EXECUTION_OUTCOME_NOT_KNOWN')

    def test_source_witnesses_are_not_self_hashes(self):
        d=setup();d['verify_observation']=lambda *_:False
        self.check(d,'NO_DATA','JOURNAL_EVIDENCE_NOT_WITNESSED')
        d=setup();d['verify_capability']=lambda *_:False
        self.check(d,'NO_DATA','CAPABILITY_NOT_WITNESSED')
        d=setup();d['allow_publication']=lambda _:False
        out=self.check(d,'NO_DATA','DISCLOSURE_NOT_WITNESSED');self.assertIsNone(out['publication'])

    def test_capability_evidence_and_scope_are_exact(self):
        for changes in ({'evidence_ref':'0'*64},{'task_ref':'0'*64},{'scope_ref':'0'*64}):
            d=setup();d['capabilities'][0]=replace(d['capabilities'][0],**changes)
            self.check(d,'NO_DATA','CAPABILITY_NOT_WITNESSED')
        out=self.check(setup(),'OBSERVED');self.assertEqual(out['capabilities'][0]['evidence_basis'],'synthetic')

    def test_future_clock_and_bad_times_do_not_leak(self):
        d=setup();d['now']=NOW-timedelta(seconds=1);self.check(d,'NO_DATA','CLOCK_INVALID_OR_FUTURE')
        d=setup();d['declarations'][0]=replace(d['declarations'][0],declared_at='PRIVATE_BAD_DATE')
        out=self.check(d,'NO_DATA');self.assertNotIn('PRIVATE_BAD_DATE',str(out))
        d=setup();d['declarations'][0]=replace(d['declarations'][0],declared_at='P'*20000)
        self.check(d,'NO_DATA','PUBLICATION_TIME_INVALID')

    def test_generation_duplicate_publication_and_bounds(self):
        d=setup();d['selection']=replace(d['selection'],generation=2)
        self.check(d,'NO_DATA','SELECTED_ACTIVATION_MISSING')
        d=setup();d['declarations']*=2;self.check(d,'NO_DATA','AMBIGUOUS_PUBLICATION')
        d=setup();d['declarations']*=33;self.check(d,'NO_DATA','INPUT_OR_HOST_CONTRACT_INVALID')

    def test_deterministic_no_io_and_no_mutation(self):
        d=setup();before=asdict(d['declarations'][0])
        with patch('socket.socket',side_effect=AssertionError('network')),patch('subprocess.Popen',side_effect=AssertionError('process')),patch('builtins.open',side_effect=AssertionError('file')):
            a=self.check(d,'OBSERVED');b=self.check(d,'OBSERVED')
        self.assertEqual(a,b);self.assertEqual(asdict(d['declarations'][0]),before)

    def test_pending_human_review_never_means_approval(self):
        d=setup();self.assertEqual(self.check(d,'OBSERVED')['human_review'],'WAITING_FOR_HUMAN_REVIEW')
        d['claim']=replace(d['claim'],review_pending=False);d['verify_claim']=lambda _:True
        ref=p.sha(asdict(d['claim']));d['declarations'][0]=replace(d['declarations'][0],claim_ref=ref)
        d['observation']=None;d['capabilities']=[]
        self.assertEqual(self.check(d,'DECLARED')['human_review'],'NO_PENDING_REVIEW_REPORTED_NOT_APPROVAL')

    def test_receipt_rejects_authority_and_schema_mutation(self):
        for changes in ({'authority':'execute'},{'state':'AUTHORIZED'},{'schema':'unknown'},{'cause':'PRIVATE_BAD_CAUSE'},{'has_recent_execution_evidence':False}):
            out=self.check(setup(),'OBSERVED');out.update(changes)
            out['snapshot_ref']=p.sha({k:v for k,v in out.items() if k!='snapshot_ref'})
            with self.assertRaises(ValueError):p.receipt(out)

    def test_relabelled_native_receipt_needs_independent_head_binding(self):
        d=setup();new=replace(d['selection'],head='0'*40)
        d['selection']=new;d['declarations'][0]=replace(d['declarations'][0],selection=new)
        d['observation']=replace(d['observation'],selection=new)
        # The self-consistent wrapper lies; the host's journal/context map refuses it.
        self.check(d,'NO_DATA','JOURNAL_EVIDENCE_NOT_WITNESSED')

    def test_stale_mesa_capture_and_duplicate_capability(self):
        d=setup();d['claim']=replace(d['claim'],observed_at=(NOW-timedelta(seconds=121)).isoformat())
        d['verify_claim']=lambda _:True
        self.check(d,'DECLARED','CLAIM_SOURCE_STALE')
        d=setup();d['capabilities']*=2
        self.check(d,'NO_DATA','DUPLICATE_CAPABILITY_EVIDENCE')
