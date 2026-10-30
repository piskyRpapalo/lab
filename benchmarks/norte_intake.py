"""Offline B4 preflight for a future NORTE Lab intake.

This validates a B3 record and its declared content hashes. It does not read,
write, transmit, or authenticate source revisions; those remain human review.
"""

import hashlib
import re

from benchmarks.norte_record import RecordError, canonical_bytes, validate

SCHEMA = "preceptoros.norte-intake/1"
HEX256 = re.compile(r"[0-9a-f]{64}\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
ENVELOPE_KEYS = {"schema", "record", "provenance"}
PROVENANCE_KEYS = {"web_commit", "record_sha256", "frame_sha256"}
MAX_INTAKE_BYTES = 16_384


def _error(where, why):
    raise RecordError(f"{where}: {why}")


def validate_intake(envelope, canonical_devices=()):
    """Check the closed B4 envelope without performing an intake side effect.

    Hashes establish byte consistency only. A human must still verify the web
    commit and approve the transfer path before this envelope can be accepted.
    """
    if not isinstance(envelope, dict) or set(envelope) != ENVELOPE_KEYS:
        _error("intake", "field set must match preceptoros.norte-intake/1")
    if envelope["schema"] != SCHEMA:
        _error("intake.schema", "unsupported schema")
    provenance = envelope["provenance"]
    if not isinstance(provenance, dict) or set(provenance) != PROVENANCE_KEYS:
        _error("intake.provenance", "web commit and both content hashes are required")
    if not isinstance(provenance["web_commit"], str) or not HEX40.fullmatch(provenance["web_commit"]):
        _error("intake.provenance.web_commit", "must be a full lowercase Git commit hash")
    for key in ("record_sha256", "frame_sha256"):
        value = provenance[key]
        if not isinstance(value, str) or not HEX256.fullmatch(value):
            _error(f"intake.provenance.{key}", "must be a lowercase SHA-256")

    record = envelope["record"]
    validate(record, canonical_devices=canonical_devices)
    expected_record = hashlib.sha256(canonical_bytes(record)).hexdigest()
    expected_frame = hashlib.sha256(canonical_bytes(record["round"]["frame"])).hexdigest()
    if provenance["record_sha256"] != expected_record:
        _error("intake.provenance.record_sha256", "does not match canonical record bytes")
    if provenance["frame_sha256"] != expected_frame:
        _error("intake.provenance.frame_sha256", "does not match canonical Bubble bytes")
    if len(canonical_bytes(envelope)) >= MAX_INTAKE_BYTES:
        _error("intake", "reaches the 16 KiB envelope ceiling")
    return envelope


def prepare_intake(record, web_commit, canonical_devices=()):
    """Build and validate an in-memory envelope; no source authenticity implied."""
    validate(record, canonical_devices=canonical_devices)
    record_bytes = canonical_bytes(record)
    frame_bytes = canonical_bytes(record["round"]["frame"])
    envelope = {
        "schema": SCHEMA,
        "record": record,
        "provenance": {
            "web_commit": web_commit,
            "record_sha256": hashlib.sha256(record_bytes).hexdigest(),
            "frame_sha256": hashlib.sha256(frame_bytes).hexdigest(),
        },
    }
    return validate_intake(envelope, canonical_devices=canonical_devices)


def serialize_intake(envelope, canonical_devices=()):
    """Return stable UTF-8 JSON only after offline validation."""
    validate_intake(envelope, canonical_devices=canonical_devices)
    return canonical_bytes(envelope)
