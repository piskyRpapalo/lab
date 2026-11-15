from dataclasses import asdict,replace
from datetime import timedelta
import copy
import unittest
from meta_harness import c2c_preflight as c
from tests.test_c2c_preflight import setup


class CacheTests(unittest.TestCase):
    def fixture(self):
        d=setup()
        key=c.CacheKey(c.sha(d['task']),c.sha(asdict(d['pair'])),c.sha(asdict(d['pin'])),
                       '1'*64,'2'*64,'3'*64,'4'*64)
        cache=c.CacheRecord(key,'5'*64,d['now'].isoformat(),'MEASURED')
        return d,key,cache

    def run_cache(self,**changes):
        d,key,cache=self.fixture()
        return c.cache_preflight(cache=changes.pop('cache',cache),expected=changes.pop('expected',key),
               verify_cache=changes.pop('verify_cache',lambda *_:True),**dict(d,**changes))

    def test_synthetic_host_controls_only_no_dispatch(self):
        r=self.run_cache();self.assertEqual(r['state'],'READY_FOR_ISOLATED_BENCH')
        self.assertFalse(r['dispatch_authorized']);self.assertFalse(r['cache_reuse_authorized'])
        self.assertEqual(r['promotion'],'NOT_AUTHORIZED');self.assertLess(len(c.resources.encode(r)),1024)

    def test_all_scope_changes_invalidate_cache(self):
        d,key,cache=self.fixture()
        for field in c.CacheKey.__dataclass_fields__:
            r=self.run_cache(expected=replace(key,**{field:'f'*64}))
            self.assertEqual(r['state'],'ABSTAIN',field)

    def test_cache_permission_tool_RAG_and_session_replay(self):
        d,key,cache=self.fixture()
        for field in ('permission_ref','tool_scope_ref','context_ref','session_ref'):
            old=replace(cache,key=replace(key,**{field:'e'*64}))
            self.assertEqual(self.run_cache(cache=old)['cause'],'CACHE_SCOPE_MISMATCH')

    def test_wrong_head_runtime_generation_rejected_by_original_preflight(self):
        d,key,cache=self.fixture()
        for p in (replace(d['pin'],generation=2),replace(d['pin'],runtime_ref='0'*64)):
            self.assertEqual(self.run_cache(pin=p)['state'],'ABSTAIN')
        pair=replace(d['pair'],receiver=replace(d['pair'].receiver,head_ref='6'*64))
        self.assertEqual(self.run_cache(pair=pair)['cause'],'FUSER_PAIR_OR_HEAD_MISMATCH')

    def test_expired_future_and_bad_timestamp(self):
        d,key,cache=self.fixture()
        for delta,cause in ((-121,'CACHE_STALE'),(1,'CACHE_CLOCK_INVALID_OR_FUTURE')):
            self.assertEqual(self.run_cache(cache=replace(cache,observed_at=(d['now']+timedelta(seconds=delta)).isoformat()))['cause'],cause)
        self.assertEqual(self.run_cache(cache=replace(cache,observed_at='bad'))['cause'],'CACHE_CLOCK_INVALID_OR_FUTURE')

    def test_no_witness_no_invented_authority(self):
        for cb,cause in ((None,'CACHE_LIVE_WITNESS_MISSING'),(lambda *_:False,'CACHE_NOT_CURRENTLY_WITNESSED'),(lambda *_:1,'CACHE_NOT_CURRENTLY_WITNESSED')):
            self.assertEqual(self.run_cache(verify_cache=cb)['cause'],cause)

    def test_revocation_between_checks(self):
        calls=[]
        def witness(*_):calls.append(1);return len(calls)==1
        self.assertEqual(self.run_cache(verify_cache=witness)['cause'],'CACHE_WITNESS_REVOKED')
        d,key,cache=self.fixture();active=[True]
        d['verify']=lambda *_:active[0]
        def revoke(*_):active[0]=False;return True
        self.assertEqual(c.cache_preflight(cache=cache,expected=key,verify_cache=revoke,**d)['cause'],'CACHE_FINAL_PREFLIGHT_CHANGED')

    def test_final_resource_and_origin_changes_are_not_ignored(self):
        from unittest.mock import patch
        d,key,cache=self.fixture();first=c.preflight(**d)
        for field,value in [('resource_ref','e'*64),('origin','SIMULATED')]:
            final=dict(first,**{field:value})
            final['receipt_ref']=c.sha({k:v for k,v in final.items() if k!='receipt_ref'})
            with patch.object(c,'preflight',side_effect=[first,final]):
                r=c.cache_preflight(cache=cache,expected=key,verify_cache=lambda *_:True,**d)
            self.assertEqual(r['cause'],'CACHE_FINAL_PREFLIGHT_CHANGED')

    def test_missing_models_not_rescued_by_cache(self):
        d,key,cache=self.fixture()
        self.assertEqual(self.run_cache(witness=replace(d['witness'],checkpoints_local=False))['cause'],'NO_DATA_LOCAL_CHECKPOINTS')

    def test_forged_origin_manifest_and_host_error(self):
        d,key,cache=self.fixture()
        for bad in (replace(cache,origin='SIMULATED'),replace(cache,cache_ref='tag'),None):
            self.assertEqual(self.run_cache(cache=bad)['state'],'ABSTAIN')
        def fail(*_):raise RuntimeError('private-error')
        r=self.run_cache(verify_cache=fail);self.assertEqual(r['cause'],'CACHE_HOST_OR_EVIDENCE_ERROR')
        self.assertNotIn('private-error',str(r))

    def test_callback_cannot_rewrite_checked_context(self):
        d,key,cache=self.fixture();before=copy.deepcopy(cache)
        def mutate(record,expected):
            object.__setattr__(record.key,'context_ref','f'*64)
            object.__setattr__(expected,'permission_ref','f'*64)
            return True
        r=self.run_cache(verify_cache=mutate)
        self.assertEqual(r['state'],'READY_FOR_ISOLATED_BENCH')
        self.assertEqual(cache,before)

    def test_hostile_reference_not_copied(self):
        class Evil:
            def __deepcopy__(self,m):raise AssertionError('hook')
        d,key,cache=self.fixture()
        self.assertEqual(self.run_cache(expected=replace(key,context_ref=Evil()))['cause'],'CACHE_MANIFEST_INVALID')

    def test_deterministic_receipt(self):
        a=self.run_cache();self.assertEqual(a,self.run_cache())
        self.assertEqual(a['receipt_ref'],c.sha({k:v for k,v in a.items() if k!='receipt_ref'}))


if __name__=='__main__':unittest.main()
