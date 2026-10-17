"""Append-only, private local storage for verbatim chunks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Iterable
from datetime import date


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    sha256: str
    source_id: str
    start_byte: int
    end_byte: int
    captured_at: str
    text: str


@dataclass(frozen=True)
class IngestReceipt:
    appended: tuple[str, ...]
    duplicates: int
    rejected: tuple[tuple[str, str], ...]


class ChunkStore:
    def __init__(self, root: Path):
        self.root = Path(root).expanduser()
        if self.root.is_symlink():
            raise ValueError("store root must not be a symlink")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.is_symlink() or not self.root.is_dir():
            raise ValueError("store root must be a local directory")
        self.root = self.root.resolve()
        os.chmod(self.root, 0o700)

    def append(self, record: ChunkRecord) -> bool:
        path = self.root / f"{record.chunk_id}.json"
        payload = (json.dumps(asdict(record), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            existing = self.read_one(path)
            same_content = (existing.chunk_id == record.chunk_id and existing.sha256 == record.sha256 and
                            existing.source_id == record.source_id and existing.start_byte == record.start_byte and
                            existing.end_byte == record.end_byte and existing.text == record.text)
            if not same_content:
                raise ValueError("append-only store id collision")
            return False
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        except Exception:
            path.unlink(missing_ok=True)
            raise
        os.chmod(path, 0o600)
        return True

    @staticmethod
    def read_one(path: Path) -> ChunkRecord:
        if path.is_symlink() or not path.is_file():
            raise ValueError("store contains a non-regular entry")
        raw = json.loads(path.read_text(encoding="utf-8"))
        record = ChunkRecord(**raw)
        try:
            if date.fromisoformat(record.captured_at).isoformat() != record.captured_at:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError("stored capture date is invalid") from None
        if path.stem != record.chunk_id:
            raise ValueError("stored chunk id mismatch")
        text_bytes = record.text.encode("utf-8")
        if hashlib.sha256(text_bytes).hexdigest() != record.sha256:
            raise ValueError("stored chunk hash mismatch")
        if record.start_byte < 0 or record.end_byte - record.start_byte != len(text_bytes):
            raise ValueError("stored chunk offsets mismatch")
        expected_id = hashlib.sha256(f"{record.source_id}:{record.start_byte}:{record.sha256}".encode("ascii")).hexdigest()
        if expected_id != record.chunk_id:
            raise ValueError("stored chunk identity mismatch")
        return record

    def read_all(self) -> tuple[ChunkRecord, ...]:
        rows = []
        for path in sorted(self.root.glob("*.json")):
            if path.is_symlink() or not stat.S_ISREG(path.stat(follow_symlinks=False).st_mode):
                raise ValueError("store contains a non-regular entry")
            rows.append(self.read_one(path))
        return tuple(rows)


def _split_utf8(text: str, max_bytes: int) -> Iterable[tuple[int, int, str]]:
    if max_bytes <= 0:
        raise ValueError("max_chunk_bytes must be positive")
    start = 0
    offset = 0
    piece: list[str] = []
    used = 0
    for char in text:
        size = len(char.encode("utf-8"))
        if used and used + size > max_bytes:
            value = "".join(piece)
            yield start, offset, value
            start = offset
            piece = []
            used = 0
        piece.append(char)
        used += size
        offset += size
    if piece:
        yield start, offset, "".join(piece)


def ingest_files(root: Path, store: ChunkStore, *, max_chunk_bytes: int, captured_at: str) -> IngestReceipt:
    root = Path(root).resolve(strict=True)
    if max_chunk_bytes <= 0:
        raise ValueError("max_chunk_bytes must be positive")
    if root == store.root or root in store.root.parents or store.root in root.parents:
        raise ValueError("source and chunk store must be separate trees")
    try:
        if date.fromisoformat(captured_at).isoformat() != captured_at:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("captured_at must be a valid ISO date supplied by the caller") from None
    appended: list[str] = []
    duplicates = 0
    rejected: list[tuple[str, str]] = []
    for source in sorted(root.rglob("*")):
        if source.is_symlink():
            rejected.append((hashlib.sha256(str(source).encode()).hexdigest(), "symlink source excluded"))
            continue
        if source.is_dir():
            continue
        if not source.is_file():
            rejected.append((hashlib.sha256(str(source).encode()).hexdigest(), "non-regular source excluded"))
            continue
        try:
            relative = source.relative_to(root).as_posix()
            raw = source.read_bytes()
            text = raw.decode("utf-8", errors="strict")
        except (OSError, UnicodeError) as exc:
            rejected.append((hashlib.sha256(str(source).encode()).hexdigest(), type(exc).__name__))
            continue
        source_id = hashlib.sha256(relative.encode("utf-8")).hexdigest()
        for start, end, value in _split_utf8(text, max_chunk_bytes):
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
            chunk_id = hashlib.sha256(f"{source_id}:{start}:{digest}".encode("ascii")).hexdigest()
            record = ChunkRecord(chunk_id, digest, source_id, start, end, captured_at, value)
            if store.append(record):
                appended.append(chunk_id)
            else:
                duplicates += 1
    return IngestReceipt(tuple(appended), duplicates, tuple(rejected))
