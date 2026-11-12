"""Full composition with a synthetic chooser; no model or network is invoked."""
import copy
import unittest

from meta_harness.brain import cycle, projections, verify_cycle, verify_projections
from meta_harness.cli import demo_gate, task
from meta_harness.delegation import Session, TokenBudget, sha
from meta_harness.workers import NativeSort
from meta_harness.hexelion import public_prompt
from tests.test_meta_context import fixture, QUERY, STAMP


class BrainTests(unittest.TestCase):
    def test_snapshot_digest_rechecked_before_existing_adapter_dispatch(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from meta_harness.hexelion import ExistingHexelion
        from meta_harness.delegation import Failure
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'hexelion_proxy.py').write_text('# synthetic trusted module')
            adapter = ExistingHexelion(directory, 'http://127.0.0.1:1', context_ref='a' * 64)
            request = task('bound-plan', 'hexelion', 'b' * 64, 'private-model',
                           adapter.input_sha256, 'ollama_loopback', 512)
            adapter._context_ref = 'c' * 64
            with patch('meta_harness.hexelion.run_worker') as dispatch:
                with self.assertRaises(Failure):
                    adapter(request, lambda: False)
                dispatch.assert_not_called()

    def test_existing_planner_optional_context_is_closed_and_input_bound(self):
        from meta_harness.context import digest_text
        from meta_harness.delegation import Failure
        original = public_prompt(None)
        bound = public_prompt(None, context_ref='a' * 64)
        self.assertTrue(bound.startswith(original))
        self.assertNotEqual(digest_text(original), digest_text(bound))
        for value in ('sk-FAKE_PRIVATE_CANARY', {}, True, 'A' * 64):
            with self.assertRaises(Failure):
                public_prompt(None, context_ref=value)

    def prepare(self, *, decision='DELEGATE_LOCAL', grant=True, cancelled=lambda: False,
                writer=True, mutate=None):
        context, rows, _, _ = fixture()
        snapshot = context.read(QUERY, STAMP)
        worker = NativeSort()
        tasks = [task('brain-' + n, 'serion-sort', worker.version,
                    'local-tool' if n == 'dispatch' else 'baseline-tool',
                    worker.input_sha256, 'local_function', 0) for n in ('one', 'two', 'dispatch')]
        for t in tasks:
            t['task_id'] = 'public-sort-native'
        planned_task = task('brain-plan', 'hexelion', 'b' * 64, 'private-model', 'c' * 64,
                            'ollama_loopback', 512)
        calls = []
        class Planner:
            input_sha256 = 'c' * 64
            context_ref = snapshot.record()['context_ref']
            def __call__(self, t, cancelled):
                calls.append('planner')
                self.decision = decision
                if mutate:
                    mutate(rows, self)
                return {'model_version': t['model_version'], 'tokens': 1,
                    'output_sha256': sha({'action': decision}), 'grade': 'PASS', 'basis': 'synthetic'}
        session = Session(demo_gate(tasks + [planned_task] if grant else [], 'd' * 64), TokenBudget(512))
        def draft(receipt, task, *, cancelled):
            calls.append('memory')
            self.assertTrue(session.attests(receipt, task))
            return {'schema': 'preceptoros.meta-memory-draft/1', 'state': 'PENDING',
                    'cause': 'exact_draft_present', 'receipt_ref': receipt['receipt_ref']}
        kwargs = dict(context=context, session=session, worker=worker, baseline_tasks=tasks[:2],
            delegated_task=tasks[2], planner_factory=lambda capability: (Planner(), planned_task),
            now=lambda: STAMP, write_draft=draft if writer else None, cancelled=cancelled)
        return (QUERY, snapshot), kwargs, calls

    def test_full_public_cycle_same_state_for_text_speech_and_machine(self):
        args, kw, calls = self.prepare()
        result = cycle(*args, **kw)
        self.assertEqual((result['record']['state'], result['record']['stage']), ('MEASURED', 'complete'))
        self.assertEqual(calls, ['planner', 'memory'])
        self.assertEqual([e['stage'] for e in result['events']],
                         ['context', 'baseline', 'selection', 'execution', 'memory'])
        self.assertTrue(verify_projections(result['views'], result['record']))
        self.assertEqual(result['record']['promotion'], 'NOT_AUTHORIZED')
        self.assertEqual(sum(r['measurement']['tokens'] for r in result['receipts']), 1)
        self.assertEqual(result['views']['text'], result['views']['speech'])
        tasks = kw['baseline_tasks'] + [kw['delegated_task']]
        # The planner task was bound by its Session witness, but is not in this list.
        self.assertFalse(verify_cycle(result, tasks, witness=kw['session'].attests))
        tasks.append(task('brain-plan', 'hexelion', 'b' * 64, 'private-model', 'c' * 64,
                          'ollama_loopback', 512))
        self.assertTrue(verify_cycle(result, tasks, witness=kw['session'].attests))
        result['events'][0]['ref'] = 'e' * 64
        self.assertFalse(verify_cycle(result, tasks, witness=kw['session'].attests))

    def test_deterministic_repetition_and_existing_session_replay(self):
        args, kw, calls = self.prepare()
        a = cycle(*args, **kw)
        b = cycle(*args, **kw)
        self.assertEqual(a, b)
        self.assertEqual(calls, ['planner', 'memory', 'memory'])
        args2, kw2, _ = self.prepare()
        self.assertEqual(a, cycle(*args2, **kw2))

    def test_abstention_and_denied_permission_never_escalate_or_write(self):
        for changes, cause in [({'decision': 'NO_DATA'}, 'planner_abstained'),
                                ({'grant': False}, 'baseline_not_witnessed')]:
            args, kw, calls = self.prepare(**changes)
            result = cycle(*args, **kw)
            self.assertEqual(result['record']['cause'], cause)
            self.assertNotIn('memory', calls)
            self.assertIsNone(result['memory'])

    def test_stop_before_execution_does_not_even_invoke_chooser(self):
        args, kw, calls = self.prepare(cancelled=lambda: True)
        result = cycle(*args, **kw)
        self.assertEqual(result['record']['cause'], 'cancelled')
        self.assertEqual(calls, [])
        self.assertEqual(result['receipts'], [])

    def test_source_race_between_selection_and_execution_is_detected(self):
        from meta_harness.context import digest_text
        def mutate(rows, planner):
            rows[0]['texto'] = 'Changed after the chooser started.'
            rows[0]['sha256'] = digest_text(rows[0]['texto'])
        args, kw, calls = self.prepare(mutate=mutate)
        result = cycle(*args, **kw)
        self.assertEqual((result['record']['stage'], result['record']['cause']),
                         ('execution', 'context_hash_changed'))
        self.assertEqual(len(result['receipts']), 3)
        self.assertNotIn('memory', calls)

    def test_authorized_but_unrelated_task_cannot_replace_measured_worker(self):
        args, kw, calls = self.prepare()
        kw['delegated_task']['input_sha256'] = 'e' * 64
        result = cycle(*args, **kw)
        self.assertEqual(result['record']['cause'], 'context_contract_invalid')
        self.assertEqual(len(result['receipts']), 3)
        self.assertNotIn('memory', calls)

    def test_no_draft_adapter_and_unconfirmed_write_never_claim_complete(self):
        args, kw, _ = self.prepare(writer=False)
        self.assertEqual(cycle(*args, **kw)['record']['cause'], 'memory_adapter_absent')
        kw['write_draft'] = lambda *a, **k: {'state': 'DRAFT', 'promoted': True}
        self.assertEqual(cycle(*args, **kw)['record']['cause'], 'memory_not_confirmed')

    def test_projection_sabotage_and_credential_exception_do_not_leak(self):
        args, kw, _ = self.prepare()
        result = cycle(*args, **kw)
        altered = copy.deepcopy(result['views'])
        altered['speech']['summary'] = 'all systems LIVE'
        self.assertFalse(verify_projections(altered, result['record']))
        def fail(*a, **k):
            raise RuntimeError('sk-FAKE_PRIVATE_CANARY')
        kw['write_draft'] = fail
        result = cycle(*args, **kw)
        self.assertEqual(result['record']['cause'], 'host_adapter_failed')
        self.assertNotIn('sk-FAKE', str(result))

    def test_resealed_live_or_wrong_summary_cannot_launder_a_projection(self):
        args, kw, _ = self.prepare()
        result = cycle(*args, **kw)
        for changes in ({'state': 'LIVE'}, {'summary': 'Secret fake credential'},
                        {'cause': 'unknown_private_cause'}, {'extra': 'surprise'}):
            altered = dict(result['record'], **changes)
            altered['cycle_ref'] = sha({k: v for k, v in altered.items() if k != 'cycle_ref'})
            with self.assertRaises(ValueError):
                projections(altered)
