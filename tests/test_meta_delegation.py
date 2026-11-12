"""Pure injected-host tests, no model, service, credential or network dependency."""
import copy
import threading
import unittest
from unittest.mock import patch

from meta_harness.delegation import Failure, Session, TokenBudget, encode, seal, sha, verify

STAMP = '2026-11-12T00:00:00Z'


def task(**changes):
    return dict({'schema': 'preceptoros.meta-task/1', 'task_id': 'sort', 'run_id': 'run-one',
        'specialist': 'serion-sort', 'source': 'local-model', 'model_version': 'a' * 64,
        'input_sha256': 'b' * 64, 'max_tokens': 64, 'timeout_ms': 30000,
        'depth': 1, 'privacy': 'LOCAL_ONLY', 'transport': 'ollama_loopback'}, **changes)


def grant(t):
    return {'approved': True, 'task_sha256': sha(t), 'approval_ref': 'c' * 64,
            'expires_ns': 10**30, 'max_tokens': 64, 'max_ms': 30000, 'max_depth': 1, 'local_only': True}


def result(t, cancelled):
    return {'model_version': t['model_version'], 'tokens': 64, 'output_sha256': 'd' * 64,
            'grade': 'PASS', 'basis': 'synthetic'}


class DelegationTests(unittest.TestCase):
    def run_one(self, *, request=None, authority=grant, dispatch=result, cancel=lambda: False, budget=64):
        clock = iter(range(0, 100000, 1000))
        session = Session(authority, TokenBudget(budget), clock=lambda: next(clock))
        return session.execute(request or task(), dispatch, observed_at=STAMP, cancelled=cancel)

    def test_authorized_attributed_bounded_sealed_receipt(self):
        receipt = self.run_one()
        self.assertEqual(receipt['phase'], 'complete')
        self.assertEqual(receipt['failure_class'], 'NONE')
        self.assertEqual(receipt['approval_state'], 'EXTERNAL_GATE')
        self.assertEqual(receipt['approval_ref'], 'c' * 64)
        self.assertEqual(receipt['specialist'], 'serion-sort')
        self.assertTrue(verify(receipt))
        self.assertLess(len(encode(receipt)), 1024)
        self.assertEqual(self.run_one(), self.run_one())

    def test_unknown_or_denied_permission_never_dispatches(self):
        for decision in (None, True, {}, dict(grant(task()), approved=False), dict(grant(task()), approved=1)):
            with self.subTest(decision=type(decision).__name__):
                def forbidden(*args):
                    self.fail('denied dispatch executed')
                receipt = self.run_one(authority=lambda _: decision, dispatch=forbidden)
                self.assertEqual(receipt['failure_class'], 'PERMISSION')
                self.assertEqual(receipt['outcome'], 'NOT_STARTED')

    def test_grant_is_bound_to_exact_input_and_budget(self):
        for change, category in [({'task_sha256': 'f' * 64}, 'PERMISSION'),
                ({'expires_ns': 0}, 'PERMISSION'), ({'local_only': False}, 'PERMISSION'),
                ({'max_tokens': 1}, 'BUDGET'), ({'max_ms': True}, 'BUDGET'), ({'max_depth': 0}, 'BUDGET')]:
            receipt = self.run_one(authority=lambda t: dict(grant(t), **change))
            self.assertEqual(receipt['failure_class'], category)
            self.assertEqual(receipt['outcome'], 'NOT_STARTED')

    def test_exact_replay_is_cached_and_different_payload_rejected(self):
        calls = []
        def dispatch(t, c):
            calls.append(t['run_id'])
            return result(t, c)
        session = Session(grant, TokenBudget(64))
        first = session.execute(task(), dispatch, observed_at=STAMP)
        second = session.execute(task(), dispatch, observed_at=STAMP)
        self.assertEqual(first, second)
        second['phase'] = 'tampered'
        self.assertEqual(len(calls), 1)
        self.assertEqual(session.execute(task(), dispatch, observed_at=STAMP)['phase'], 'complete')
        with self.assertRaises(Failure) as caught:
            session.execute(task(input_sha256='e' * 64), dispatch, observed_at=STAMP)
        self.assertEqual(caught.exception.category, 'REPLAY')

    def test_concurrent_run_id_never_dispatches_twice(self):
        started, release, values = threading.Event(), threading.Event(), []
        session = Session(grant, TokenBudget(128))
        def dispatch(t, c):
            started.set()
            release.wait(2)
            return result(t, c)
        thread = threading.Thread(target=lambda: values.append(session.execute(task(), dispatch, observed_at=STAMP)))
        thread.start()
        try:
            self.assertTrue(started.wait(1))
            with self.assertRaises(Failure) as caught:
                session.execute(task(), dispatch, observed_at=STAMP)
            self.assertEqual(caught.exception.category, 'REPLAY')
        finally:
            release.set()
            thread.join()
        self.assertEqual(len(values), 1)

    def test_two_clients_share_one_conservative_budget(self):
        budget = TokenBudget(128)
        first, second = Session(grant, budget), Session(grant, budget)
        self.assertEqual(first.execute(task(), result, observed_at=STAMP)['phase'], 'complete')
        self.assertEqual(second.execute(task(run_id='run-two'), result, observed_at=STAMP)['phase'], 'complete')
        denied = first.execute(task(run_id='run-three'), result, observed_at=STAMP)
        self.assertEqual(denied['failure_class'], 'BUDGET')
        self.assertEqual(budget.remaining, 0)

    def test_cancel_before_dispatch_and_after_grant(self):
        for signals in ([True], [False, True]):
            checks = iter(signals)
            def forbidden(*args):
                self.fail('cancelled dispatch executed')
            receipt = self.run_one(cancel=lambda: next(checks), dispatch=forbidden)
            self.assertEqual(receipt['phase'], 'cancelled')
            self.assertEqual(receipt['outcome'], 'NOT_STARTED')

    def test_inflight_cancel_is_unknown_and_cannot_retry(self):
        flag, calls = [False], []
        def dispatch(t, c):
            calls.append(1)
            flag[0] = True
            return result(t, c)
        budget = TokenBudget(64)
        session = Session(grant, budget)
        receipt = session.execute(task(), dispatch, observed_at=STAMP, cancelled=lambda: flag[0])
        self.assertEqual((receipt['phase'], receipt['outcome']), ('cancelled', 'UNKNOWN'))
        self.assertEqual(budget.remaining, 0)
        session.execute(task(), dispatch, observed_at=STAMP)
        self.assertEqual(len(calls), 1)

    def test_uncertain_transport_failure_is_scrubbed_reserved_and_not_retried(self):
        calls = []
        def fails(*args):
            calls.append(1)
            raise OSError('fake-key-SECRET /private/location')
        budget = TokenBudget(64)
        session = Session(grant, budget)
        receipt = session.execute(task(), fails, observed_at=STAMP)
        self.assertEqual(receipt['failure_class'], 'UNKNOWN')
        self.assertEqual(receipt['outcome'], 'UNKNOWN')
        self.assertNotIn(b'SECRET', encode(receipt))
        self.assertNotIn(b'/private', encode(receipt))
        self.assertEqual(session.execute(task(), fails, observed_at=STAMP), receipt)
        self.assertEqual((len(calls), budget.remaining), (1, 0))

    def test_provider_failure_cannot_fallback_to_paid_adapter(self):
        def fails(*args):
            raise Failure('TRANSPORT')
        receipt = self.run_one(dispatch=fails)
        self.assertEqual(receipt['failure_class'], 'TRANSPORT')
        self.assertEqual(receipt['next_action'], 'repair_transport')

    def test_web_manual_is_not_api_callable(self):
        receipt = self.run_one(request=task(transport='web_manual'))
        self.assertEqual(receipt['failure_class'], 'TRANSPORT')
        self.assertEqual(receipt['outcome'], 'NOT_STARTED')

    def test_local_only_and_depth_are_enforced_before_grant(self):
        for request in [task(privacy='REMOTE_OK'), task(depth=2), task(max_tokens=True),
                        task(source='secret\nvalue'), dict(task(), prompt='private')]:
            with self.assertRaises(Failure):
                self.run_one(request=request)

    def test_bad_result_schema_model_or_token_count_cannot_pass(self):
        for change, category in [({'model_version': 'e' * 64}, 'MODEL_IDENTITY'),
                ({'tokens': 65}, 'BUDGET'), ({'tokens': True}, 'BUDGET'),
                ({'output_sha256': 'private-answer'}, 'PROTOCOL'),
                ({'raw_answer': 'fake-secret'}, 'PROTOCOL')]:
            receipt = self.run_one(dispatch=lambda t, c: dict(result(t, c), **change))
            self.assertEqual(receipt['failure_class'], category)
            self.assertNotIn(b'fake-secret', encode(receipt))

    def test_task_skill_and_format_failures_are_distinct(self):
        for category in ('TASK_SKILL', 'OUTPUT_SCHEMA'):
            receipt = self.run_one(dispatch=lambda t, c: dict(result(t, c), grade=category))
            self.assertEqual(receipt['failure_class'], category)
            self.assertEqual(receipt['phase'], 'failed')
            self.assertTrue(verify(receipt))

    def test_receipt_mutation_unknown_fields_and_false_live_are_rejected(self):
        original = self.run_one()
        for change in ({'specialist': 'different'}, {'phase': 'LIVE'}, {'raw_answer': 'fake-secret'}):
            broken = dict(copy.deepcopy(original), **change)
            self.assertFalse(verify(broken))
            # A recomputed hash cannot legalize unknown fields or LIVE.
            if 'specialist' not in change:
                broken['receipt_ref'] = sha({k: v for k, v in broken.items() if k != 'receipt_ref'})
                self.assertFalse(verify(broken))

    def test_same_state_for_text_speech_and_json_and_sabotage(self):
        from meta_harness.cli import projections, verify_projections
        receipt = self.run_one()
        views = projections([receipt], STAMP)
        self.assertEqual(views['text'], views['speech'])
        self.assertEqual(views['text']['summary'], views['machine']['record']['summary'])
        self.assertEqual(len({v['state_ref'] for v in views.values()}), 1)
        self.assertLessEqual(len(views['text']['summary']), 100)
        self.assertLess(len(encode(views['machine'])), 1024)
        self.assertTrue(verify_projections(views, [receipt], STAMP))
        views['speech']['summary'] = 'Everything is LIVE.'
        self.assertFalse(verify_projections(views, [receipt], STAMP))
        self.assertEqual(projections([], STAMP)['machine']['record']['state'], 'NO_DATA')

    def test_demo_gate_is_closed_to_exact_host_prepared_tasks(self):
        from meta_harness.cli import demo_gate
        session = Session(demo_gate([task()], 'c' * 64), TokenBudget(128))
        changed = task(run_id='not-approved')
        denied = session.execute(changed, result, observed_at=STAMP)
        self.assertEqual(denied['failure_class'], 'PERMISSION')
        granted = session.execute(task(), result, observed_at=STAMP)
        self.assertEqual(granted['phase'], 'complete')
        with self.assertRaises(Failure):
            demo_gate([task()], 'raw-key-not-a-reference')

    def test_metadata_catalog_is_never_inference_verification(self):
        from meta_harness.cli import model_catalog
        with patch('meta_harness.cli.throughput.request', return_value={
                'models': [{'name': 'public:tiny', 'digest': 'a' * 64}]}):
            row = model_catalog('http://127.0.0.1:1', 'public:tiny', 'local-model')
        self.assertEqual(row['state'], 'DECLARED')
        self.assertEqual(row['transport_state'], 'CONNECTED')
        self.assertEqual(row['generation']['state'], 'NO_DATA')

    def test_success_without_measurement_cannot_be_resigned_into_validity(self):
        receipt = self.run_one()
        receipt.update(measurement=None, confidence_basis='NO_DATA', outcome='NOT_STARTED')
        receipt['receipt_ref'] = sha({k: v for k, v in receipt.items() if k != 'receipt_ref'})
        self.assertFalse(verify(receipt))

    def test_expired_while_waiting_budget_never_dispatches_and_refunds(self):
        clock = iter([0, 0, 31_000_000_000])
        budget = TokenBudget(64)
        def forbidden(*args):
            self.fail('expired task dispatched')
        receipt = Session(grant, budget, clock=lambda: next(clock)).execute(task(), forbidden, observed_at=STAMP)
        self.assertEqual(receipt['failure_class'], 'TRANSPORT')
        self.assertEqual(receipt['outcome'], 'NOT_STARTED')
        self.assertEqual(budget.remaining, 64)

    def test_cancelled_during_reservation_wait_never_dispatches(self):
        waiting, stop, results = threading.Event(), [False], []
        class WaitingBudget(TokenBudget):
            def reserve(self, cap):
                waiting.set()
                super().reserve(cap)
        budget = WaitingBudget(64)
        budget.lock.acquire()
        session = Session(grant, budget)
        def forbidden(*args):
            self.fail('cancelled waiter dispatched')
        thread = threading.Thread(target=lambda: results.append(session.execute(
            task(), forbidden, observed_at=STAMP, cancelled=lambda: stop[0])))
        thread.start()
        try:
            self.assertTrue(waiting.wait(1))
            stop[0] = True
        finally:
            budget.lock.release()
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(results[0]['failure_class'], 'CANCELLED')
        self.assertEqual(results[0]['outcome'], 'NOT_STARTED')
        self.assertEqual(budget.remaining, 64)


if __name__ == '__main__':
    unittest.main()
