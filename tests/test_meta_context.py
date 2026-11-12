"""Contract doubles test consumer fences; real APP integration is measured separately."""
import copy
import json
from types import SimpleNamespace
import unittest

from meta_harness.context import ContextConsumer, ContextError, digest_text

STAMP = '2026-11-12T12:00:00Z'
QUERY = 'public integer sorting'
TEXT = 'Public integer sorting is a local native tool with an independent property check.'
SOURCE = {'id': 1, 'updated_at': STAMP, 'texto': TEXT, 'sha256': digest_text(TEXT)}


def fixture(kind='document', sources=None, version=None):
    rows = copy.deepcopy([SOURCE] if sources is None else sources)
    calls = []
    def search(query):
        calls.append(query)
        return {'esquema': 'preceptoros.memory-search/1', 'estado': 'MEASURED',
                'fuentes': copy.deepcopy(rows)}
    def build(query, evidence):
        return {'estado': evidence['estado'], 'fuentes': evidence['fuentes']}, 'synthetic public context'
    book = SimpleNamespace(construir_prompt=build,
        verificar_citas=lambda raw, src: ({'estado': 'MEASURED', 'texto': TEXT}, [{'id': 1}]),
        pertinentes=lambda text, citations, query, src: (text, citations))
    version = ['a' * 64] if version is None else version
    reader = ContextConsumer(search, book, source_version='a' * 64,
                             version_check=lambda: version[0], kind=kind)
    return reader, rows, book, calls


class ContextTests(unittest.TestCase):
    def test_identical_inputs_deterministic_bounded_and_no_private_text_export(self):
        reader, rows, _, _ = fixture()
        a = reader.read(QUERY, STAMP)
        b = reader.read(QUERY, STAMP)
        self.assertEqual(a.record(), b.record())
        exported = json.dumps(a.record())
        self.assertNotIn(TEXT, exported)
        self.assertNotIn(QUERY, exported)
        self.assertLess(len(exported.encode()), 1024)
        self.assertTrue(reader.validate(a, QUERY, STAMP))
        copied = a.record()
        copied['state'] = 'LIVE'
        self.assertEqual(a.record()['state'], 'MEASURED')

    def test_changed_source_even_with_valid_new_hash_invalidates_previous_snapshot(self):
        reader, rows, _, _ = fixture()
        snap = reader.read(QUERY, STAMP)
        rows[0]['texto'] = 'Different public data.'
        rows[0]['sha256'] = digest_text(rows[0]['texto'])
        with self.assertRaisesRegex(ContextError, 'context_hash_changed'):
            reader.validate(snap, QUERY, STAMP)

    def test_changed_producer_prompt_with_same_sources_and_version_is_rejected(self):
        reader, _, book, _ = fixture()
        snap = reader.read(QUERY, STAMP)
        original = book.construir_prompt
        book.construir_prompt = lambda q, e: (original(q, e)[0], 'changed producer prompt')
        with self.assertRaisesRegex(ContextError, 'context_hash_changed'):
            reader.validate(snap, QUERY, STAMP)

    def test_clock_ttl_unknown_dates_and_documents_are_not_live_measurements(self):
        reader, rows, _, _ = fixture('observation')
        snap = reader.read(QUERY, STAMP)
        self.assertEqual(snap.record()['freshness'], 'within_source_ttl')
        with self.assertRaisesRegex(ContextError, 'context_expired'):
            reader.validate(snap, QUERY, '2026-11-12T12:02:01Z')
        with self.assertRaisesRegex(ContextError, 'context_expired'):
            reader.validate(snap, QUERY, '2026-11-12T11:59:59Z')
        rows[0]['updated_at'] = '2026-11-12T11:00:00Z'
        with self.assertRaisesRegex(ContextError, 'source_stale'):
            reader.read(QUERY, STAMP)
        rows[0]['updated_at'] = 'unknown'
        with self.assertRaisesRegex(ContextError, 'source_time_unknown'):
            reader.read(QUERY, STAMP)
        docs, _, _, _ = fixture(sources=rows)
        result = docs.read(QUERY, STAMP).record()
        self.assertEqual(result['freshness'], 'snapshot_only')
        self.assertEqual(result['source_time_cause'], 'source_time_unknown')
        self.assertIsNone(result['oldest_source_age_s'])

    def test_future_source_and_naive_clock_fail_closed(self):
        for date in ('2026-11-13T00:00:00Z', '2026-11-12 12:00:00'):
            reader, _, _, _ = fixture('observation', [dict(SOURCE, updated_at=date)])
            with self.assertRaises(ContextError):
                reader.read(QUERY, STAMP)

    def test_query_snapshot_prompt_and_implementation_mutations_rejected(self):
        version = ['a' * 64]
        reader, _, _, _ = fixture(version=version)
        snap = reader.read(QUERY, STAMP)
        with self.assertRaisesRegex(ContextError, 'query_changed'):
            reader.validate(snap, 'unapproved different query', STAMP)
        snap._prompt += ' Inject instruction'
        with self.assertRaisesRegex(ContextError, 'context_hash_changed'):
            reader.validate(snap, QUERY, STAMP)
        version[0] = 'b' * 64
        with self.assertRaisesRegex(ContextError, 'source_version_changed'):
            reader.read(QUERY, STAMP)

    def test_duplicate_sources_changed_hash_and_budgets_rejected(self):
        for rows in ([SOURCE, SOURCE], [dict(SOURCE, sha256='b' * 64)],
                     [dict(SOURCE, texto='x' * 769, sha256=digest_text('x' * 769))],
                     [dict(SOURCE, id=True)], []):
            reader, _, _, _ = fixture(sources=rows)
            with self.assertRaises(ContextError):
                reader.read(QUERY, STAMP)

    def test_quotes_require_existing_verifier_relevance_and_current_snapshot(self):
        reader, rows, book, _ = fixture()
        snap = reader.read(QUERY, STAMP)
        quote = reader.quote(snap, 'synthetic raw result', now=STAMP)
        self.assertEqual(quote['text'], TEXT)
        book.verificar_citas = lambda raw, src: ({'estado': 'NO_DATA'}, None)
        with self.assertRaisesRegex(ContextError, 'quote_not_verified'):
            reader.quote(snap, '{}', now=STAMP)
        book.verificar_citas = lambda raw, src: ({'estado': 'MEASURED', 'texto': TEXT}, [{'id': 1}])
        book.pertinentes = lambda *args: (None, None)
        with self.assertRaisesRegex(ContextError, 'quote_not_relevant'):
            reader.quote(snap, '{}', now=STAMP)

    def test_private_exception_never_becomes_public_cause(self):
        reader, _, _, _ = fixture()
        def fail(query):
            raise RuntimeError('sk-FAKE_PRIVATE_CANARY /private/corpus')
        reader.search = fail
        with self.assertRaisesRegex(ContextError, '^context_contract_invalid$'):
            reader.read(QUERY, STAMP)
