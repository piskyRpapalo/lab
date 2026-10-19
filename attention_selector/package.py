"""Stable two-pass context package. Pass one is an index; pass two is verbatim."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .core import Chunk, SelectionPolicy, select_chunks


@dataclass(frozen=True)
class PackagedChunk:
    chunk_id: str
    source_id: str
    start_byte: int
    end_byte: int
    sha256: str
    seal: str
    text: str


@dataclass(frozen=True)
class TwoPassPackage:
    status: str
    cause: str | None
    pass1: tuple[dict, ...]
    pass2: tuple[PackagedChunk, ...]
    pass1_bytes: bytes
    pass2_bytes: bytes
    prefix: str


def _json_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_two_pass_package(
    query: str,
    chunks: tuple[Chunk, ...] | list[Chunk],
    policy: SelectionPolicy,
    *,
    index_budget_bytes: int,
    chunk_budget_bytes: int,
) -> TwoPassPackage:
    if min(index_budget_bytes, chunk_budget_bytes) <= 0:
        raise ValueError("both pass budgets must be positive")
    policy_doc = {"max_chunks": policy.max_chunks, "max_chunk_bytes": policy.max_chunk_bytes,
                  "max_total_bytes": policy.max_total_bytes, "idf_scale": policy.idf_scale,
                  "version": policy.version, "exclude_source_ids": sorted(policy.exclude_source_ids)}
    policy_hash = hashlib.sha256(_json_bytes(policy_doc)).hexdigest()
    prefix = f"attention-package/1|policy={policy_hash}|"
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    ceilings = {"index_bytes": index_budget_bytes, "chunk_package_bytes": chunk_budget_bytes,
                "chunk_count": policy.max_chunks, "chunk_bytes_each": policy.max_chunk_bytes,
                "total_text_bytes": policy.max_total_bytes}
    selection = select_chunks(query, chunks, policy)
    pass2_rows: list[PackagedChunk] = []
    index_rows: list[dict] = []
    for ranked in selection.selected:
        chunk = ranked.chunk
        packaged = PackagedChunk(chunk.chunk_id, chunk.source_id, chunk.start_byte, chunk.end_byte,
                                 chunk.sha256, "VERBATIM", chunk.text)
        existing = [{"schema": "attention-selector.chunk/1", **item.__dict__} for item in pass2_rows]
        candidate_doc = {"schema": "attention-selector.chunks/1", "policy_sha256": policy_hash,
                         "query_sha256": query_hash, "ceilings": ceilings,
                         "status": "VERBATIM", "cause": None,
                         "items": [*existing, {"schema": "attention-selector.chunk/1", **packaged.__dict__}]}
        candidate = prefix.encode("ascii") + _json_bytes(candidate_doc)
        if len(candidate) > chunk_budget_bytes:
            index_rows.append({"chunk_id": chunk.chunk_id, "priority": ranked.priority,
                               "bytes": chunk.byte_count, "seal": "NO_DATA",
                               "cause": "complete chunk exceeds pass-two byte ceiling"})
            continue
        pass2_rows.append(packaged)
        index_rows.append({"chunk_id": chunk.chunk_id, "priority": ranked.priority,
                           "bytes": chunk.byte_count, "seal": "VERBATIM", "cause": ranked.cause})
    for item in selection.exclusions:
        index_rows.append({"chunk_id": item.chunk_id, "priority": None, "bytes": None,
                           "seal": "NO_DATA", "cause": item.cause})
    index_rows.sort(key=lambda item: (item["seal"] != "VERBATIM",
                                      -(item["priority"] or 0), item["chunk_id"]))
    index_doc = {"schema": "attention-selector.index/1", "policy_sha256": policy_hash,
                 "query_sha256": query_hash, "ceilings": ceilings,
                 "status": "VERBATIM" if pass2_rows else "NO_DATA",
                 "cause": None if pass2_rows else selection.cause or "declared package budget admits no complete chunk",
                 "unlisted_count": 0, "unlisted_cause": None, "items": []}
    for row in index_rows:
        candidate = {**index_doc, "items": [*index_doc["items"], row]}
        if len(prefix.encode("ascii") + _json_bytes(candidate)) <= index_budget_bytes:
            index_doc = candidate
    omitted = len(index_rows) - len(index_doc["items"])
    index_doc["unlisted_count"] = omitted
    index_doc["unlisted_cause"] = "index byte ceiling" if omitted else None
    while len(prefix.encode("ascii") + _json_bytes(index_doc)) > index_budget_bytes and index_doc["items"]:
        index_doc["items"].pop()
        omitted = len(index_rows) - len(index_doc["items"])
        index_doc["unlisted_count"] = omitted
        index_doc["unlisted_cause"] = "index byte ceiling" if omitted else None
    allowed = {row["chunk_id"] for row in index_doc["items"] if row["seal"] == "VERBATIM"}
    pass2_rows = [row for row in pass2_rows if row.chunk_id in allowed]
    if not pass2_rows:
        index_doc["status"] = "NO_DATA"
        index_doc["cause"] = selection.cause or "declared package budget admits no complete chunk"
        for row in index_doc["items"]:
            if row["seal"] == "VERBATIM":
                row["seal"] = "NO_DATA"
                row["cause"] = "index byte ceiling omitted the corresponding pass-two chunk"
    pass1 = tuple(index_doc["items"])
    pass1_bytes = prefix.encode("ascii") + _json_bytes(index_doc)
    if len(pass1_bytes) > index_budget_bytes:
        pass1_bytes = b""
        pass1 = ()
    pass2_doc = {"schema": "attention-selector.chunks/1", "policy_sha256": policy_hash,
                 "query_sha256": query_hash, "ceilings": ceilings,
                 "status": "VERBATIM" if pass2_rows else "NO_DATA",
                 "cause": None if pass2_rows else "declared package budget admits no complete chunk",
                 "items": [{"schema": "attention-selector.chunk/1", **item.__dict__} for item in pass2_rows]}
    pass2_bytes = prefix.encode("ascii") + _json_bytes(pass2_doc)
    if len(pass2_bytes) > chunk_budget_bytes:
        pass2_bytes = b""
        pass2_rows = []
    if not pass1 or not pass2_rows:
        return TwoPassPackage("NO_DATA", selection.cause or "declared package budget admits no complete chunk",
                              pass1, tuple(pass2_rows), pass1_bytes, pass2_bytes, prefix)
    return TwoPassPackage("VERBATIM", None, pass1, tuple(pass2_rows), pass1_bytes, pass2_bytes, prefix)
