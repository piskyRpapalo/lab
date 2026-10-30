"""Pure, offline contract judge and canonical serializer for NORTE B3.

This module does not run a game, assign a seal, read a clock, or publish a
record. Callers provide measurements with provenance or caused NO_DATA.
"""

import json
import re

SCHEMA = "preceptoros.norte-record/1"
BUBBLE = "preceptoros.bubble/1"
FRAME_LIMIT = 1024
RECORD_LIMIT = 16_384
DOCTRINE_SEALS = {"LIVE", "STALE", "STATIC", "SIMULATED", "NO_DATA", "ERROR"}
MEASURED_KEYS = {"state", "value", "source", "observed_at"}
NO_DATA_KEYS = {"state", "cause", "source", "attempted_at"}
ROUND_KEYS = {"number", "tick", "color", "coordinates", "frame"}
SUMMARY_KEYS = {"seed", "rules_version", "device", "date", "result", "seal"}
FRAME_KEYS = {"v", "id", "t", "cv", "light", "style", "atoms", "bands",
              "change", "sound", "soundCause", "motion", "seal"}
FORBIDDEN_KEYS = {"user", "walker", "identity", "prompt", "answer", "hostname",
                  "host", "path", "device_name", "machine_name"}


class RecordError(ValueError):
    """A B3 artifact failed its closed contract."""


def _fail(where, reason):
    raise RecordError(f"{where}: {reason}")


def canonical_bytes(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        _fail("record", f"not canonical JSON ({type(exc).__name__})")


def _scrub_keys(value, where="record"):
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str) or key.lower() in FORBIDDEN_KEYS:
                _fail(where, "forbidden or non-text key")
            _scrub_keys(nested, where)
    elif isinstance(value, list):
        for nested in value:
            _scrub_keys(nested, where)


def _measurement(value, where):
    if not isinstance(value, dict):
        _fail(where, "must be MEDIDO or NO_DATA object")
    if value.get("state") == "MEASURED" and set(value) == MEASURED_KEYS:
        if not isinstance(value["source"], str) or not value["source"].strip():
            _fail(where, "MEASURED requires a source")
        if not isinstance(value["observed_at"], str) or not value["observed_at"].strip():
            _fail(where, "MEASURED requires observed_at")
        return value["value"]
    if value.get("state") == "NO_DATA" and set(value) == NO_DATA_KEYS:
        for key in ("cause", "source", "attempted_at"):
            if not isinstance(value[key], str) or not value[key].strip():
                _fail(where, f"NO_DATA requires {key}")
        return None
    _fail(where, "field shape invalid; each absence needs its own cause")


def _round(record):
    if not isinstance(record, dict) or set(record) != ROUND_KEYS:
        _fail("round", "field set must match the v1 contract")
    if type(record["number"]) is not int or record["number"] < 1:
        _fail("round.number", "must be a positive integer")
    tick = _measurement(record["tick"], "round.tick")
    if tick is not None and (type(tick) is not int or tick < 0):
        _fail("round.tick", "must be a non-negative simulation tick")
    color = _measurement(record["color"], "round.color")
    coordinates = _measurement(record["coordinates"], "round.coordinates")
    if color is not None and not isinstance(color, str):
        _fail("round.color", "must be a named Bubble band")
    if coordinates is not None:
        if (not isinstance(coordinates, list) or not coordinates or
                any(not isinstance(pair, list) or len(pair) != 2 or
                    any(type(n) is not int for n in pair) for pair in coordinates)):
            _fail("round.coordinates", "must be a list of axial integer pairs")

    frame = record["frame"]
    if not isinstance(frame, dict) or set(frame) - FRAME_KEYS:
        _fail("round.frame", "unknown frame fields")
    if frame.get("v") != BUBBLE:
        _fail("round.frame.v", "must be preceptoros.bubble/1")
    if frame.get("seal") not in DOCTRINE_SEALS:
        _fail("round.frame.seal", "missing or invalid data seal")
    atoms = frame.get("atoms")
    if not isinstance(atoms, list) or not atoms:
        _fail("round.frame.atoms", "at least one visible atom is required")
    phrases = []
    for atom in atoms:
        if not isinstance(atom, dict) or not isinstance(atom.get("r"), str) or not atom["r"].strip():
            _fail("round.frame.atoms", "each visible atom needs its own phrase")
        if "\n" in atom["r"] or len(atom["r"].encode("utf-8")) > 240:
            _fail("round.frame.atoms", "phrase must be one bounded line")
        phrases.append(atom["r"])
    if len(set(phrases)) != len(phrases):
        _fail("round.frame.atoms", "visible atoms need distinct phrases")
    bands = frame.get("bands")
    if not isinstance(bands, list) or not bands or any(not isinstance(b, str) for b in bands):
        _fail("round.frame.bands", "named color bands are required")
    if color is not None and color not in bands:
        _fail("round.color", "primary color must occur in the Bubble frame")
    sound = frame.get("sound")
    if sound == "NO_DATA":
        if not isinstance(frame.get("soundCause"), str) or not frame["soundCause"].strip():
            _fail("round.frame.sound", "NO_DATA sound requires soundCause")
    elif not isinstance(sound, str) or not sound.strip():
        _fail("round.frame.sound", "must be declared or NO_DATA with cause")
    frame_size = len(canonical_bytes(frame))
    if frame_size >= FRAME_LIMIT:
        _fail("round.frame", f"{frame_size} UTF-8 bytes reaches the 1 KiB ceiling")
    if len(canonical_bytes(record)) >= FRAME_LIMIT:
        _fail("round", "round envelope reaches the 1 KiB ceiling")


def validate(record, canonical_devices=()):
    """Validate one round record and summary; return the original value.

    A MEDIDO device must be one of the supplied canonical fleet pseudonyms.
    Empty or unknown fleet identity therefore remains NO_DATA or is rejected.
    """
    if not isinstance(record, dict) or set(record) != {"schema", "round", "summary"}:
        _fail("record", "field set must match the v1 contract")
    if record["schema"] != SCHEMA:
        _fail("record.schema", "unsupported schema")
    _scrub_keys(record)
    _round(record["round"])
    summary = record["summary"]
    if not isinstance(summary, dict) or set(summary) != SUMMARY_KEYS:
        _fail("summary", "seed, rules_version, device, date, result and seal are required")
    values = {key: _measurement(summary[key], f"summary.{key}") for key in SUMMARY_KEYS}
    for key in ("seed", "rules_version", "date", "result", "seal"):
        value = values[key]
        if value is not None and (not isinstance(value, str) or not value.strip()):
            _fail(f"summary.{key}", "measured value must be non-empty text")
    date_value = values["date"]
    if date_value is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
        _fail("summary.date", "must be supplied as YYYY-MM-DD")
    device = values["device"]
    if device is not None and (not isinstance(device, str) or device not in set(canonical_devices)):
        _fail("summary.device", "pseudonym is absent from the measured fleet census")
    if len(canonical_bytes(record)) >= RECORD_LIMIT:
        _fail("record", "reaches the 16 KiB artifact ceiling")
    return record


def serialize(record, canonical_devices=()):
    """Return canonical UTF-8 bytes only after the pure judge accepts the record."""
    validate(record, canonical_devices)
    return canonical_bytes(record)
