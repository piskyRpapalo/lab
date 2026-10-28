#!/usr/bin/env python3
"""Generate the deterministic synthetic four-class int8 proof payload."""
import hashlib
import json
from pathlib import Path

TOTAL_BYTES = 25_000_000
CHUNK_BYTES = 6_250_000
CLASSES = 4
FEATURES = TOTAL_BYTES // CLASSES
VOCAB = {
    "hello": (12, -4, -4, -4),
    "help": (-4, 12, -4, -4),
    "map": (-4, 12, -4, -4),
    "controls": (-4, -4, 12, -4),
    "privacy": (-4, -4, -4, 12),
}


def feature(term):
    value = 2166136261
    for byte in term.encode("ascii"):
        value = ((value ^ byte) * 16777619) & 0xFFFFFFFF
    return value % FEATURES


def main():
    out = Path(__file__).with_name("model")
    out.mkdir(parents=True, exist_ok=True)
    weights = bytearray(TOTAL_BYTES)
    occupied = {}
    for term, vector in VOCAB.items():
        index = feature(term)
        if index in occupied:
            raise SystemExit("synthetic feature hash collision")
        occupied[index] = term
        weights[index * CLASSES:index * CLASSES + CLASSES] = bytes(v & 0xFF for v in vector)

    chunks = []
    for number, offset in enumerate(range(0, TOTAL_BYTES, CHUNK_BYTES)):
        data = weights[offset:offset + CHUNK_BYTES]
        name = f"weights-{number:02d}.bin"
        (out / name).write_bytes(data)
        chunks.append({
            "file": name,
            "byte_offset": offset,
            "byte_length": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    manifest = {
        "schema": "preceptoros.synthetic-choice-model/1",
        "status": "SYNTHETIC_DEMONSTRATION",
        "total_bytes": TOTAL_BYTES,
        "origin": "same-origin ./model/ (served by the local static demo)",
        "algorithm": "sparse fixed-point word weights; signed int8; FNV-1a feature index",
        "class_order": ["greeting", "screen_help", "controls", "privacy"],
        "chunk_size_bytes": CHUNK_BYTES,
        "chunks": chunks,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"payload_bytes={TOTAL_BYTES} chunks={len(chunks)} max_chunk_bytes={max(x['byte_length'] for x in chunks)}")
    print("manifest_sha256=" + hashlib.sha256((out / "manifest.json").read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
