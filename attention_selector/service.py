"""Hexagonal application service with injected data, model, and receipt ports."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import sys
from typing import Protocol

from .core import Chunk, Selection, SelectionPolicy, select_chunks
from .package import TwoPassPackage, build_two_pass_package
from .store import ChunkStore


class CorpusReader(Protocol):
    def read_chunks(self) -> tuple[Chunk, ...]: ...


class ModelCaller(Protocol):
    def explain(self, equation: str, cause: str) -> str: ...


class ReceiptWriter(Protocol):
    def write(self, value: dict) -> None: ...


class LocalStoreReader:
    def __init__(self, store: ChunkStore):
        self.store = store

    def read_chunks(self) -> tuple[Chunk, ...]:
        return tuple(Chunk(row.chunk_id, row.text, row.source_id, row.start_byte, row.end_byte)
                     for row in self.store.read_all())


class JsonReceiptWriter:
    def __init__(self, stream=None):
        self.stream = stream if stream is not None else sys.stdout

    def write(self, value: dict) -> None:
        self.stream.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


class AttentionSelectorService:
    def __init__(self, reader: CorpusReader, writer: ReceiptWriter,
                 policy: SelectionPolicy, model_caller: ModelCaller | None = None):
        self.reader = reader
        self.writer = writer
        self.policy = policy
        self.model_caller = model_caller

    def rank(self, query: str) -> Selection:
        result = select_chunks(query, self.reader.read_chunks(), self.policy)
        self.writer.write({"status": result.status, "cause": result.cause,
                           "selected_count": len(result.selected), "excluded_count": len(result.exclusions),
                           "ceilings": {"chunk_count": self.policy.max_chunks,
                                        "chunk_bytes_each": self.policy.max_chunk_bytes,
                                        "total_text_bytes": self.policy.max_total_bytes},
                           "ranked": [{"chunk_id": row.chunk.chunk_id, "priority": row.priority,
                                       "bytes": row.chunk.byte_count, "seal": "VERBATIM", "cause": row.cause}
                                      for row in result.selected],
                           "excluded": [{"chunk_id": row.chunk_id, "priority": None,
                                         "seal": "NO_DATA", "cause": row.cause}
                                        for row in result.exclusions]})
        return result

    def package(self, query: str, *, index_budget_bytes: int,
                chunk_budget_bytes: int) -> TwoPassPackage:
        result = build_two_pass_package(query, self.reader.read_chunks(), self.policy,
                                        index_budget_bytes=index_budget_bytes,
                                        chunk_budget_bytes=chunk_budget_bytes)
        self.writer.write({"status": result.status, "cause": result.cause,
                           "index_bytes": len(result.pass1_bytes), "chunks_bytes": len(result.pass2_bytes),
                           "ceilings": {"index_bytes": index_budget_bytes,
                                        "chunk_package_bytes": chunk_budget_bytes,
                                        "chunk_count": self.policy.max_chunks,
                                        "chunk_bytes_each": self.policy.max_chunk_bytes,
                                        "total_text_bytes": self.policy.max_total_bytes},
                           "selected_count": len(result.pass2),
                           "sha256": {"index": hashlib.sha256(result.pass1_bytes).hexdigest(),
                                      "chunks": hashlib.sha256(result.pass2_bytes).hexdigest()}})
        return result

    def explain(self, equation: str, cause: str) -> str:
        if self.model_caller is None:
            self.writer.write({"status": "NO_DATA", "cause": "model caller is not configured"})
            raise RuntimeError("model caller is not configured")
        answer = self.model_caller.explain(equation, cause)
        self.writer.write({"status": "RESPONSE_RECEIVED", "response_bytes": len(answer.encode("utf-8")),
                           "semantic_quality": "NO_DATA",
                           "cause": "no labeled explanation-correctness set is available",
                           "authority": False})
        return answer
