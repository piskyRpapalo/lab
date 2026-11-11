import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/'benchmarks/receipts/20261111-qwen3-two-endpoints.json'


class TestMatchedModelEndpointReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads(FILE.read_text(encoding='utf-8'))

    def test_one_model_digest_both_routes(self):
        self.assertEqual(self.r['model'],'qwen3:1.7b')
        self.assertRegex(self.r['digest'],r'^[0-9a-f]{64}$')
        self.assertTrue(all(x['actual_model_digest']==self.r['digest'] for x in self.r['runs']))

    def test_two_runs_per_route(self):
        self.assertEqual([x['endpoint_role'] for x in self.r['runs']],
                         ['rack_local','station_tunnel','station_tunnel','rack_local'])
        self.assertTrue(all(x['generated_tokens']==48 for x in self.r['runs']))
        self.assertTrue(all(x['generated_tokens_per_sec']>0 for x in self.r['runs']))

    def test_station_host_attestation_remains_unknown(self):
        v=self.r['endpoints']['station_tunnel']
        self.assertFalse(v['host_os_measured'])
        self.assertTrue(v['identity'].startswith('NO_DATA'))
        self.assertTrue(self.r['energy'].startswith('NO_DATA'))

    def test_source_inputs_not_published(self):
        s=FILE.read_text(encoding='utf-8')
        for forbidden in ('/home/','127.0.0.1','21434','11434','raw_prompt','model_response'):
            self.assertNotIn(forbidden,s)

    def test_explicit_scope(self):
        self.assertEqual(self.r['scope'],'SMALL_SYNTHETIC_COLD_START_MATCHED_MODEL')
        self.assertEqual(self.r['source_truth'],'NO_DATA: no_quality_evaluation')


if __name__=='__main__':
    unittest.main()
