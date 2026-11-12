"""Native control is math, not a model answer or LoRA experiment."""
import unittest
from unittest.mock import patch

from meta_harness.workers import NativeSort, baseline_spec, select_worker, tool_inventory
from meta_harness.delegation import Failure, Session, TokenBudget, sha, verify
from meta_harness.hexelion import capability_evidence
from meta_harness.cli import demo_gate, task
from tests.test_meta_delegation import STAMP


class NativeWorkerTests(unittest.TestCase):
    def prepare(self):
        worker = NativeSort()
        tasks = [task('native-' + n, 'serion-sort', worker.version, 'baseline-tool',
                      worker.input_sha256, 'local_function', 0) for n in ('one', 'two')]
        for request in tasks:
            request['task_id'] = 'public-sort-native'
        return worker, tasks

    def test_real_native_control_is_authorized_witnessed_and_zero_tokens(self):
        worker, tasks = self.prepare()
        session = Session(demo_gate(tasks, 'a' * 64), TokenBudget(0))
        receipts = [session.execute(t, worker, observed_at=STAMP) for t in tasks]
        self.assertTrue(all(verify(r) and r['phase'] == 'complete' for r in receipts))
        self.assertTrue(all(r['measurement']['tokens'] == 0 for r in receipts))
        self.assertEqual(receipts[0]['measurement']['output_sha256'], receipts[1]['measurement']['output_sha256'])
        context = capability_evidence(receipts, tasks, worker.version, STAMP, witness=session.attests)
        self.assertEqual(context['baseline_passed'], 2)

    def test_native_property_judge_detects_bad_order_and_changed_multiset(self):
        worker, tasks = self.prepare()
        for broken in ([1] * 16, list(range(15, -1, -1))):
            with patch('meta_harness.workers.sorted', return_value=broken, create=True):
                self.assertEqual(worker(tasks[0], lambda: False)['grade'], 'TASK_SKILL')

    def test_native_task_cannot_change_data_version_or_transport(self):
        worker, tasks = self.prepare()
        for change in ({'max_tokens': 64}, {'transport': 'ollama_loopback'},
                       {'input_sha256': 'b' * 64}, {'model_version': 'c' * 64}):
            with self.assertRaises(Failure):
                worker(dict(tasks[0], **change), lambda: False)
        with self.assertRaises(Failure):
            worker(tasks[0], lambda: True)

    def test_native_capability_is_independent_of_model_catalog(self):
        selected = select_worker('native-sort', 'http://127.0.0.1:1', 'missing', {'state': 'NO_DATA'})
        self.assertIsInstance(selected[0], NativeSort)
        self.assertEqual(selected[2:], ('local-tool', 'baseline-tool', 'local_function'))
        self.assertEqual(baseline_spec('public-sort-native')[1:], ('baseline-tool', 'local_function', 0))

    def test_cancelled_receipts_never_claim_measured_tool_execution(self):
        worker, tasks = self.prepare()
        session = Session(demo_gate(tasks, 'a' * 64), TokenBudget(0))
        rows = [session.execute(t, worker, observed_at=STAMP, cancelled=lambda: True) for t in tasks]
        self.assertTrue(all(r['outcome'] == 'NOT_STARTED' for r in rows))
        inventory = tool_inventory(worker.version, rows)
        self.assertEqual((inventory['state'], inventory['cause']), ('NO_DATA', 'no_measured_tool_outcome'))
        self.assertEqual(tool_inventory(worker.version, [])['state'], 'NO_DATA')


if __name__ == '__main__':
    unittest.main()
