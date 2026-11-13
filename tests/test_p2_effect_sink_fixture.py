"""Test-only effect owner; no real issuer, worker fence or production dispatch."""
from concurrent.futures import ThreadPoolExecutor
import tempfile
import threading
from pathlib import Path
import unittest

from meta_harness.delegation import Failure, Session, sha
from meta_harness.execution_journal import DurableTokenBudget, ExecutionJournal
from tests.test_meta_delegation import STAMP, grant, result, task


class FixtureSink:
    """In-process synthetic fence, not a durable or cryptographic authority.

    The same lock orders fixture revocation with fixture effect; this cannot
    fence another process, a service, or a real external side-effect owner.
    """
    def __init__(self, request, *, token_changes=None, interrupt_after_effect=False):
        self.lock = threading.Lock()
        self.live = {'active': True, 'generation': 1, 'host': 'fixture-host',
                     'target': 'fixture-target', 'operation': 'a' * 64, 'now': 10}
        self.token = dict(self.live, task_ref=sha(request), expires=20)
        self.token.update(token_changes or {})
        self.effects, self.rejections = [], 0
        self.interrupt_after_effect = interrupt_after_effect

    def revoke(self):
        with self.lock:
            self.live['active'] = False

    def __call__(self, request, cancelled):
        with self.lock:
            token, live = self.token, self.live
            if (live['active'] is not True or token['active'] is not True
                    or any(token[k] != live[k] for k in ('generation', 'host', 'target', 'operation'))
                    or token['task_ref'] != sha(request) or token['expires'] <= live['now']):
                self.rejections += 1
                raise Failure('PERMISSION')
            if token['operation'] in self.effects:
                self.rejections += 1
                raise Failure('REPLAY')
            self.effects.append(token['operation'])
            if self.interrupt_after_effect:
                raise OSError('synthetic lost confirmation')
        return result(request, cancelled)


def make_session(temp, *, admission=None):
    journal = ExecutionJournal.create(Path(temp) / 'journal.sqlite3')
    journal.initialize_budget(128)
    return Session(grant, DurableTokenBudget(journal), journal=journal, admission=admission)


class SinkTests(unittest.TestCase):
    def test_revocation_after_grant_never_reaches_effect(self):
        # Revocation follows the last authority callback in both Session paths.
        for admission, trigger in ((None, 2), (lambda *_: True, 5)):
            with self.subTest(admission=admission is not None), tempfile.TemporaryDirectory() as temp:
                sink = FixtureSink(task())
                checks = []
                def cancelled():
                    checks.append(1)
                    if len(checks) == trigger:
                        sink.revoke()
                    return False
                session = make_session(temp, admission=admission)
                receipt = session.execute(task(), sink, observed_at=STAMP, cancelled=cancelled)
                self.assertFalse(sink.live['active'])
                self.assertEqual(len(sink.effects), 0)
                self.assertEqual(sink.rejections, 1)
                # Session cannot know the sink refused before the effect and stays conservative.
                self.assertEqual(receipt['outcome'], 'UNKNOWN')
                self.assertEqual(session.budget.remaining, 64)
                self.assertEqual(session.execute(task(), sink, observed_at=STAMP)['outcome'], 'UNKNOWN')
                with self.assertRaises(Failure):
                    session.execute(task(run_id='next'), sink, observed_at=STAMP)
                self.assertEqual(len(sink.effects), 0)
                self.assertEqual(session.budget.remaining, 64)

    def test_unprotected_destination_still_has_gap(self):
        with tempfile.TemporaryDirectory() as temp:
            state = {'revoked': False, 'effects': 0, 'checks': 0}
            def cancelled():
                state['checks'] += 1
                if state['checks'] == 2:
                    state['revoked'] = True
                return False
            def unprotected(request, stop):
                self.assertTrue(state['revoked'])
                state['effects'] += 1
                return result(request, stop)
            session = make_session(temp)
            receipt = session.execute(task(), unprotected, observed_at=STAMP, cancelled=cancelled)
            self.assertEqual((state['effects'], receipt['outcome']), (1, 'KNOWN'))

    def test_bounded_adversarial_matrix_and_false_blocks(self):
        rows = [('valid', {}, False), ('valid-two', {}, False), ('revoked', {}, True),
                ('stale_generation', {'generation': 0}, False),
                ('wrong_operation', {'operation': 'b'*64}, False),
                ('wrong_host', {'host': 'other-host'}, False),
                ('wrong_target', {'target': 'other-target'}, False),
                ('wrong_task', {'task_ref': '0'*64}, False),
                ('expired', {'expires': 10}, False)]
        totals = {'authorized_effects': 0, 'unauthorized_effects': 0, 'revoked_effects': 0,
                  'false_blocks': 0, 'unknown_retained': 0}
        for name, changes, revoke in rows:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temp:
                request = task(run_id='valid-two') if name == 'valid-two' else task()
                sink = FixtureSink(request, token_changes=changes)
                if revoke:
                    sink.revoke()
                session = make_session(temp)
                receipt = session.execute(request, sink, observed_at=STAMP)
                effects = len(sink.effects)
                if name.startswith('valid'):
                    totals['authorized_effects'] += effects
                    totals['false_blocks'] += effects != 1
                    self.assertEqual(receipt['outcome'], 'KNOWN')
                else:
                    totals['unauthorized_effects'] += effects
                    if name == 'revoked':
                        totals['revoked_effects'] += effects
                    totals['unknown_retained'] += (receipt['outcome'] == 'UNKNOWN' and session.budget.remaining == 64)
                    self.assertEqual(receipt['outcome'], 'UNKNOWN')
        self.assertEqual(totals, {'authorized_effects': 2, 'unauthorized_effects': 0,
                                  'revoked_effects': 0, 'false_blocks': 0, 'unknown_retained': 7})

    def test_valid_request_replay_has_exactly_one_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            session = make_session(temp)
            sink = FixtureSink(task())
            first = session.execute(task(), sink, observed_at=STAMP)
            replayed = session.execute(task(), sink, observed_at=STAMP)
            self.assertEqual(first, replayed)
            self.assertEqual(first['outcome'], 'KNOWN')
            self.assertEqual(len(sink.effects), 1)

    def test_interruption_after_effect_stays_unknown_and_retains_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            session = make_session(temp)
            sink = FixtureSink(task(), interrupt_after_effect=True)
            first = session.execute(task(), sink, observed_at=STAMP)
            self.assertEqual(first['outcome'], 'UNKNOWN')
            self.assertEqual((len(sink.effects), session.budget.remaining), (1, 64))
            self.assertEqual(session.execute(task(), sink, observed_at=STAMP), first)
            with self.assertRaises(Failure):
                session.execute(task(run_id='next'), sink, observed_at=STAMP)
            self.assertEqual((len(sink.effects), session.budget.remaining), (1, 64))

    def test_unknown_after_journal_reopen_stays_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            session = make_session(temp)
            sink = FixtureSink(task(), interrupt_after_effect=True)
            first = session.execute(task(), sink, observed_at=STAMP)
            self.assertEqual(first['outcome'], 'UNKNOWN')
            reopened = ExecutionJournal(Path(temp) / 'journal.sqlite3', resolution_witness=None)
            restarted = Session(grant, DurableTokenBudget(reopened), journal=reopened)
            self.assertEqual(restarted.execute(task(), sink, observed_at=STAMP), first)
            with self.assertRaises(Failure):
                restarted.execute(task(run_id='next'), sink, observed_at=STAMP)
            self.assertEqual((len(sink.effects), restarted.budget.remaining), (1, 64))

    def test_fixture_owner_rejects_duplicate_effect_directly(self):
        sink = FixtureSink(task())
        sink(task(), lambda: False)
        with self.assertRaises(Failure):
            sink(task(), lambda: False)
        self.assertEqual(len(sink.effects), 1)

    def test_fixture_effect_owner_serializes_duplicate_claimants(self):
        sink = FixtureSink(task())
        barrier = threading.Barrier(2)
        def contender():
            barrier.wait(timeout=3)
            try:
                sink(task(), lambda: False)
                return 'effect'
            except Failure:
                return 'rejected'
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: contender(), range(2)))
        self.assertEqual(sorted(results), ['effect', 'rejected'])
        self.assertEqual((len(sink.effects), sink.rejections), (1, 1))
