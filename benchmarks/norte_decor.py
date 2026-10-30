"""Pure conversion of a supplied scenery movement into a B3/B4 preflight.

No game, clock, repository lookup, storage, transmission, or training occurs.
Missing measurements remain caused NO_DATA values in the B3 contract.
"""

from benchmarks.norte_intake import prepare_intake, serialize_intake
from benchmarks.norte_record import SCHEMA, canonical_bytes, validate


def _measured(value, source, observed_at):
    return {"state": "MEASURED", "value": value,
            "source": source, "observed_at": observed_at}


def _no_data(cause, source, attempted_at):
    return {"state": "NO_DATA", "cause": cause,
            "source": source, "attempted_at": attempted_at}


def movement_record(movement, *, round_number, web_commit, canonical_devices=(),
                    source="supplied DE-1 movement", observed_at="",
                    attempted_at=""):
    """Build a B3 record and B4 hash envelope from supplied movement evidence.

    `observed_at` and `attempted_at` are supplied provenance strings, never
    generated here. Summary fields unavailable to this bridge stay NO_DATA.
    """
    if not isinstance(movement, dict) or set(movement) != {"schema", "seed", "moves", "frames"}:
        raise ValueError("movement: expected the closed DE-1 script")
    if not movement["moves"] or len(movement["moves"]) != len(movement["frames"]):
        raise ValueError("movement: moves and frames must be non-empty and paired")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source: required provenance")
    if not isinstance(web_commit, str) or len(web_commit) != 40:
        raise ValueError("web_commit: full source commit is required")

    frames = movement["frames"]
    if len(frames) != 1:
        raise ValueError("movement: one B3 round represents exactly one scenery frame")
    frame = frames[0]
    move = movement["moves"][0]
    coordinates = [move["from"][key] for key in ("q", "r")] + [move["to"][key] for key in ("q", "r")]
    frame = dict(frame)
    # B3 expects a separate axial-cell list; no color or clock is inferred.
    color = frame.get("bands", [None])[0]
    if not isinstance(color, str) or not color:
        color_field = _no_data("DE-1 frame supplies no measured primary color", source, attempted_at)
    else:
        color_field = _measured(color, source, observed_at)

    tick_field = _no_data("DE-1 relocation has no simulation tick", source, attempted_at)
    coordinate_cells = [move["from"], move["to"]]
    round_data = {
        "number": round_number,
        "tick": tick_field,
        "color": color_field,
        "coordinates": _measured([[cell["q"], cell["r"]] for cell in coordinate_cells], source, observed_at),
        "frame": frame,
    }
    summary = {
        "seed": _measured(str(movement["seed"]), source, observed_at),
        "rules_version": _measured(movement["schema"], source, observed_at),
        "device": _no_data("no canonical fleet pseudonym was supplied", source, attempted_at),
        "date": _no_data("this bridge does not read a clock", source, attempted_at),
        "result": _no_data("no game or combat result was supplied", source, attempted_at),
        "seal": _no_data("no upstream action seal was supplied", source, attempted_at),
    }
    record = {"schema": SCHEMA, "round": round_data, "summary": summary}
    validate(record, canonical_devices=canonical_devices)
    envelope = prepare_intake(record, web_commit, canonical_devices=canonical_devices)
    return {"record": record, "intake": envelope,
            "b3_bytes": canonical_bytes(record),
            "b4_bytes": serialize_intake(envelope, canonical_devices=canonical_devices)}
