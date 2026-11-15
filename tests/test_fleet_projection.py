import copy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from meta_harness.fleet_projection import Observation, project, FIELDS
from meta_harness.resource_admission import resources

NOW = datetime(2026, 11, 15, tzinfo=timezone.utc)
NODES = tuple(resources.sha({'fixture_node': i}) for i in range(6))
SOURCE = resources.sha('synthetic-source')


class FleetTests(unittest.TestCase):
    def obs(self, **changes):
        return replace(Observation(NODES[0], 'reachable', True, SOURCE,
                                   NOW.isoformat(), 'OBSERVED'), **changes)

    def run_projection(self, obs=(), **kw):
        return project(NODES, tuple(obs), now=kw.pop('now', NOW),
                       verify_source=kw.pop('verify_source', lambda _: True), **kw)

    def field(self, result, field='reachable'):
        return next(n for n in result['details'] if n['node_ref'] == NODES[0])['fields'][field]

    def bounds(self, result):
        self.assertEqual(result['summary']['authority'], 'none')
        self.assertFalse(result['summary']['dispatch_authorized'])
        self.assertFalse(result['summary']['physical_presence_verified'])
        self.assertLess(len(resources.encode(result['summary'])), 1024)
        for n in result['details']:
            self.assertEqual(n['admission']['state'], 'NO_DATA')

    def test_six_missing_nodes(self):
        r = self.run_projection()
        self.assertEqual(len(r['details']), 6)
        self.assertTrue(all(f['state'] == 'NO_DATA' for n in r['details'] for f in n['fields'].values()))
        self.bounds(r)

    def test_fresh_observed_and_declared(self):
        for basis in ('OBSERVED', 'DECLARED'):
            r = self.run_projection([self.obs(basis=basis)])
            self.assertEqual(self.field(r)['state'], basis)
            self.bounds(r)

    def test_expiry_boundary(self):
        for seconds, state in ((120, 'OBSERVED'), (121, 'STALE')):
            r = self.run_projection([self.obs(observed_at=(NOW-timedelta(seconds=seconds)).isoformat())])
            self.assertEqual(self.field(r)['state'], state)
            self.bounds(r)

    def test_future_invalid_naive_times(self):
        for time in ((NOW+timedelta(seconds=1)).isoformat(), 'bad', '2026-11-15T00:00:00'):
            r = self.run_projection([self.obs(observed_at=time)])
            self.assertEqual(self.field(r)['cause'], 'clock_invalid_or_future')
            self.bounds(r)

    def test_witness_required_and_fail_closed(self):
        def explode(_):
            raise RuntimeError('private-error')
        for witness in (None, lambda _: False, lambda _: 1, explode):
            r = self.run_projection([self.obs()], verify_source=witness)
            self.assertEqual(self.field(r)['state'], 'NO_DATA')
            self.assertNotIn('private-error', str(r))
            self.bounds(r)

    def test_duplicate_and_conflicting(self):
        for observations in ([self.obs(), self.obs()], [self.obs(), self.obs(value=False)]):
            r = self.run_projection(observations)
            self.assertEqual(self.field(r)['cause'], 'conflicting_observations')

    def test_unreachable_is_evidence_not_authority(self):
        r = self.run_projection([self.obs(value=False)])
        self.assertIs(self.field(r)['value'], False)
        self.bounds(r)

    def test_empty_catalog_not_inference_or_installation(self):
        r = self.run_projection([self.obs(field='catalog_models', value=[])])
        self.assertEqual(self.field(r, 'catalog_models')['value'], [])
        self.assertEqual(self.field(r, 'loaded_models')['state'], 'NO_DATA')
        self.bounds(r)

    def test_unknown_private_and_bad_values_rejected(self):
        for changes in ({'field':'private_path','value':'/private'}, {'node_ref':'x'},
                        {'source_ref':'x'}, {'basis':'MEASURED'}, {'field':'memory_total_bytes','value':True},
                        {'field':'memory_total_bytes','value':-1}, {'field':'os','value':'/private'},
                        {'field':'loaded_models','value':['model-name']}, {'value':1},
                        {'field':'loaded_models','value':[SOURCE,SOURCE]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.run_projection([self.obs(**changes)])

    def test_determinism_and_no_input_mutation(self):
        obs = [self.obs(), self.obs(field='loaded_models', value=[SOURCE, NODES[0]])]
        before = copy.deepcopy(obs)
        def witness(row):
            row['value'] = 'mutated'
            return True
        a = self.run_projection(obs, verify_source=witness)
        b = self.run_projection(list(reversed(obs)), verify_source=witness)
        self.assertEqual(a,b)
        self.assertEqual(before,obs)
        self.bounds(a)

    def test_memory_conflict(self):
        obs = [self.obs(field='memory_total_bytes', value=4), self.obs(field='memory_available_bytes', value=5)]
        self.assertEqual(self.field(self.run_projection(obs),'memory_available_bytes')['cause'],
                         'memory_observations_inconsistent')

    def test_input_bounds(self):
        for nodes in ((), NODES+(SOURCE,), (NODES[0],NODES[0]), ('private',)):
            with self.assertRaises(ValueError):
                project(nodes, (), now=NOW)
        with self.assertRaises(ValueError):
            self.run_projection([self.obs()]*257)
        with self.assertRaises(ValueError):
            self.run_projection(now=NOW.replace(tzinfo=None))

    def test_receipt_integrity(self):
        r = self.run_projection([self.obs()])
        s = r['summary']
        self.assertEqual(s['details_ref'], resources.sha(r['details']))
        self.assertEqual(s['receipt_ref'], resources.sha({k:v for k,v in s.items() if k!='receipt_ref'}))


if __name__ == '__main__':
    unittest.main()
