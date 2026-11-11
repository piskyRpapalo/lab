import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/'benchmarks/receipts/20261111-gemma2-cpu-gpu.json'


class TestLocalGemmaDevicePilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads(RECEIPT.read_text(encoding='utf-8'))

    def test_two_per_backend_with_actual_backend(self):
        self.assertEqual([x['backend_observed'] for x in self.r['runs']],
                         ['GPU','CPU','CPU','GPU'])
        self.assertEqual([x['backend_requested'] for x in self.r['runs']],
                         ['gpu','cpu','cpu','gpu'])

    def test_honest_counts(self):
        self.assertEqual(len(self.r['runs']),4)
        self.assertTrue(all(x['eval_count']==48 for x in self.r['runs']))
        self.assertTrue(all(x['wall_s']>0 for x in self.r['runs']))

    def test_no_cpu_gpu_conflation(self):
        gpu=[x for x in self.r['runs'] if x['backend_observed']=='GPU']
        cpu=[x for x in self.r['runs'] if x['backend_observed']=='CPU']
        self.assertEqual(len(gpu),len(cpu))
        self.assertTrue(all(x['size_vram_bytes']>0 for x in gpu))
        self.assertTrue(all(x['size_vram_bytes']==0 for x in cpu))

    def test_declared_limits(self):
        self.assertTrue(self.r['not_a_quality_benchmark'])
        self.assertTrue(self.r['power'].startswith('NO_DATA'))
        self.assertTrue(self.r['thermal_control'].startswith('NO_DATA'))
        self.assertEqual(self.r['scope'],'SMALL_SYNTHETIC_COLD_START')

    def test_scrubbed(self):
        s=RECEIPT.read_text(encoding='utf-8')
        for forbidden in ('/home/','127.0.0.1','prompt_text','model_response','access_token'):
            self.assertNotIn(forbidden,s)


if __name__=='__main__':
    unittest.main()
