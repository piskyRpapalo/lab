"""Deterministic lexical selector. Model output never participates in ranking."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Iterable


_WORD = re.compile(r"[^\W_]+", re.UNICODE)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    source_id: str
    start_byte: int
    end_byte: int
    excluded: bool = False

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    @property
    def byte_count(self) -> int:
        return len(self.text.encode("utf-8"))


@dataclass(frozen=True)
class SelectionPolicy:
    max_chunks: int
    max_chunk_bytes: int
    max_total_bytes: int = 8192
    idf_scale: int = 1024
    version: str = "lexical-v1"
    exclude_source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if min(self.max_chunks, self.max_chunk_bytes, self.max_total_bytes, self.idf_scale) <= 0:
            raise ValueError("policy limits must be positive")
        if not self.version or not self.version.isascii():
            raise ValueError("policy version must be non-empty ASCII")
        if any(len(value) != 64 or any(char not in "0123456789abcdef" for char in value)
               for value in self.exclude_source_ids):
            raise ValueError("excluded source ids must be lowercase SHA-256 values")


@dataclass(frozen=True)
class RankedChunk:
    chunk: Chunk
    priority: int
    cause: str


@dataclass(frozen=True)
class ExcludedChunk:
    chunk_id: str
    cause: str


@dataclass(frozen=True)
class Selection:
    status: str
    cause: str | None
    selected: tuple[RankedChunk, ...]
    exclusions: tuple[ExcludedChunk, ...]


def _terms(text: str) -> tuple[str, ...]:
    return tuple(term.casefold() for term in _WORD.findall(text))


def select_chunks(query: str, chunks: Iterable[Chunk], policy: SelectionPolicy) -> Selection:
    query_terms = tuple(dict.fromkeys(_terms(query)))
    if not query_terms:
        return Selection("NO_DATA", "query has no indexable terms", (), ())

    corpus = tuple(chunks)
    df = {term: sum(term in set(_terms(chunk.text)) for chunk in corpus) for term in query_terms}
    ranked: list[RankedChunk] = []
    excluded: list[ExcludedChunk] = []
    for chunk in corpus:
        if chunk.excluded or chunk.source_id in policy.exclude_source_ids:
            excluded.append(ExcludedChunk(chunk.chunk_id, "excluded by source policy"))
            continue
        size = chunk.byte_count
        if size > policy.max_chunk_bytes:
            excluded.append(ExcludedChunk(chunk.chunk_id, "chunk exceeds declared byte ceiling"))
            continue
        term_counts: dict[str, int] = {}
        for term in _terms(chunk.text):
            if term in query_terms:
                term_counts[term] = term_counts.get(term, 0) + 1
        if not term_counts:
            excluded.append(ExcludedChunk(chunk.chunk_id, "no lexical overlap with query"))
            continue
        score = 0
        for term, count in term_counts.items():
            score += min(count, 8) * (len(corpus) + 1) * policy.idf_scale // (df[term] + 1)
        ranked.append(RankedChunk(chunk, score, "integer lexical overlap with inverse document frequency"))

    ranked.sort(key=lambda item: (-item.priority, item.chunk.chunk_id))
    selected: list[RankedChunk] = []
    used_bytes = 0
    for item in ranked:
        if len(selected) >= policy.max_chunks:
            excluded.append(ExcludedChunk(item.chunk.chunk_id, "declared chunk-count ceiling"))
            continue
        if used_bytes + item.chunk.byte_count > policy.max_total_bytes:
            excluded.append(ExcludedChunk(item.chunk.chunk_id, "declared total-byte ceiling"))
            continue
        selected.append(item)
        used_bytes += item.chunk.byte_count
    if not selected:
        return Selection("NO_DATA", "no eligible chunk matched the query within policy", (), tuple(excluded))
    return Selection("VERBATIM", None, tuple(selected), tuple(excluded))
