"""Consumer of APP retrieval/quote contracts; source data never grants authority.

Search, book and version_check are injected by the trusted host. No index, model,
memory service, networking or permission mechanism is implemented here.
"""
import copy
import datetime as dt
import hashlib

from .delegation import HEX, encode, sha

CAUSES = frozenset({'context_unavailable', 'context_contract_invalid', 'context_hash_changed',
    'context_expired', 'source_time_unknown', 'source_time_future', 'source_stale',
    'source_version_changed', 'query_changed', 'quote_not_verified', 'quote_not_relevant'})


class ContextError(Exception):
    def __init__(self, cause):
        self.cause = cause if cause in CAUSES else 'context_contract_invalid'
        super().__init__(self.cause)


def instant(text):
    if type(text) is not str or len(text) > 64:
        raise ContextError('source_time_unknown')
    try:
        value = dt.datetime.fromisoformat(text.replace('Z', '+00:00'))
        if value.tzinfo is None or value.utcoffset() != dt.timedelta(0):
            raise ValueError()
        return value
    except ValueError:
        raise ContextError('source_time_unknown') from None


def digest_text(text):
    return hashlib.sha256(text.encode('utf-8', 'strict')).hexdigest()


class Snapshot:
    """Private prompt/sources stay in process; only record() is exportable."""
    def __init__(self, query, sources, prompt, record):
        self._query = query
        self._sources = copy.deepcopy(sources)
        self._prompt = prompt
        self._record = copy.deepcopy(record)

    def record(self):
        return copy.deepcopy(self._record)


class ContextConsumer:
    def __init__(self, search, book, *, source_version, version_check,
                 kind='document', max_age_seconds=120):
        if (kind not in ('document', 'observation') or type(max_age_seconds) is not int
                or not 1 <= max_age_seconds <= 86400 or not callable(search)
                or not callable(version_check) or type(source_version) is not str
                or not HEX.fullmatch(source_version)):
            raise ContextError('context_contract_invalid')
        self.search, self.book = search, book
        self.version = source_version
        self.version_check = version_check
        self.kind, self.max_age = kind, max_age_seconds

    def read(self, query, now):
        try:
            current = instant(now)
            if self.version_check() != self.version:
                raise ContextError('source_version_changed')
            evidence = self.search(query)
            checked, prompt = self.book.construir_prompt(query, evidence)
            if checked.get('estado') != 'MEASURED' or type(prompt) is not str:
                raise ContextError('context_unavailable')
            sources = checked['fuentes']
            # Independently enforce the consumer's boundary even if a producer drifts.
            if (not 1 <= len(sources) <= 3 or len(prompt.encode()) > 4096
                    or sum(len(s['texto'].encode()) for s in sources) > 768):
                raise ContextError('context_contract_invalid')
            ids = set()
            ages, missing_time = [], False
            for source in sources:
                if (type(source) is not dict or set(source) != {'id', 'updated_at', 'sha256', 'texto'}
                        or type(source['id']) is not int or source['id'] <= 0 or source['id'] in ids
                        or type(source['texto']) is not str or not source['texto']
                        or source['sha256'] != digest_text(source['texto'])):
                    raise ContextError('context_contract_invalid')
                ids.add(source['id'])
                try:
                    age = (current - instant(source['updated_at'])).total_seconds()
                except ContextError:
                    if self.kind == 'observation':
                        raise
                    missing_time = True
                    continue
                if age < 0:
                    raise ContextError('source_time_future')
                ages.append(age)
                if self.kind == 'observation' and age > self.max_age:
                    raise ContextError('source_stale')
            if self.version_check() != self.version:
                raise ContextError('source_version_changed')
            record = {'schema': 'preceptoros.context-consumption/1', 'state': 'MEASURED',
                'cause': None, 'observed_at': now, 'query_sha256': digest_text(query),
                'source_version': self.version, 'sources_sha256': sha(sources),
                'sources': len(sources), 'kind': self.kind,
                'freshness': 'snapshot_only' if self.kind == 'document' else 'within_source_ttl',
                'max_age_seconds': self.max_age,
                'oldest_source_age_s': None if missing_time else max(ages),
                'source_time_cause': 'source_time_unknown' if missing_time else None,
                'prompt_sha256': digest_text(prompt)}
            record['context_ref'] = sha(record)
            if len(encode(record)) >= 1024:
                raise ContextError('context_contract_invalid')
            return Snapshot(query, sources, prompt, record)
        except ContextError:
            raise
        except Exception:
            # No producer exception, source text, query or local path crosses this boundary.
            raise ContextError('context_contract_invalid') from None

    def validate(self, snapshot, query, now):
        try:
            if type(snapshot) is not Snapshot or query != snapshot._query:
                raise ContextError('query_changed')
            record = snapshot.record()
            if sha({k: v for k, v in record.items() if k != 'context_ref'}) != record['context_ref']:
                raise ContextError('context_hash_changed')
            if (record['query_sha256'] != digest_text(query) or record['source_version'] != self.version
                    or record['kind'] != self.kind or record['max_age_seconds'] != self.max_age):
                raise ContextError('context_hash_changed')
            age = (instant(now) - instant(record['observed_at'])).total_seconds()
            if not 0 <= age <= self.max_age:
                raise ContextError('context_expired')
            fresh = self.read(query, now)
            if (sha(snapshot._sources) != record['sources_sha256']
                    or digest_text(snapshot._prompt) != record['prompt_sha256']
                    or fresh.record()['sources_sha256'] != record['sources_sha256']):
                raise ContextError('context_hash_changed')
            return True
        except ContextError:
            raise
        except Exception:
            raise ContextError('context_contract_invalid') from None

    def quote(self, snapshot, raw_answer, *, now):
        """Private extractive result, verified by the original APP implementation.

        Caller must keep text local; its hash/count can be exported, not the quote.
        Lexical relevance is not semantic accuracy or an execution instruction.
        """
        self.validate(snapshot, snapshot._query, now)
        checked, citations = self.book.verificar_citas(raw_answer, snapshot._sources)
        if checked.get('estado') != 'MEASURED':
            raise ContextError('quote_not_verified')
        text, citations = self.book.pertinentes(checked['texto'], citations,
                                                snapshot._query, snapshot._sources)
        if not text or not citations:
            raise ContextError('quote_not_relevant')
        return {'state': 'MEASURED', 'text': text, 'citations': citations,
                'context_ref': snapshot.record()['context_ref']}
