#!/usr/bin/env python3
"""Measure the shared lexical projection contract across web and app trees."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


SCHEMA_ID = "preceptoros.lexical-projection/1"
PIECE_LIMIT = 16384
CHANNEL_LIMIT = 1024
WEB_FILES = ("public/lexical_state_schema.json", "public/game/lexical_projector.js")
APP_FILES = ("lexicon_state.py", "lexical_projector.py")
FRAME = {
    "id": "radio-building", "t": "Radio Building", "sound": "four soft notes",
    "motion": "steady", "atoms": [{"k": "channel", "i": [{"o": "channel", "tx": "local"}]}],
}


def _schema(path: Path) -> dict:
    if not path.is_file():
        raise ValueError("NO_DATA: web schema is absent")
    if path.stat().st_size > PIECE_LIMIT:
        raise ValueError("ERROR: web schema exceeds piece ceiling")
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("ERROR: web schema is unreadable") from exc
    properties = schema.get("properties", {})
    live_rule = (schema.get("allOf") or [{}])[0].get("then", {}).get("properties", {})
    if (schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
            or properties.get("v", {}).get("const") != SCHEMA_ID
            or live_rule.get("bytes", {}).get("maximum") != 1023
            or not {"id", "t", "sound", "motion", "n", "a"}.issubset(
                properties.get("p", {}).get("required", []))):
        raise ValueError("ERROR: schema does not declare the measured projection contract")
    return schema


def validate_envelope(value: object, schema: dict) -> int:
    if not isinstance(value, dict) or value.get("v") != SCHEMA_ID:
        raise ValueError("projection version mismatch")
    status = value.get("st")
    size = value.get("bytes")
    if type(size) is not int or size < 0:
        raise ValueError("byte count is not a non-negative integer")
    if status == "LIVE":
        if size >= CHANNEL_LIMIT or "causa" in value or not isinstance(value.get("p"), dict):
            raise ValueError("LIVE projection violates size or payload contract")
        required = {"id", "t", "sound", "motion", "n", "a"}
        if not required.issubset(value["p"]):
            raise ValueError("LIVE payload is incomplete")
        body = json.dumps(value["p"], ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(body) != size:
            raise ValueError("payload byte count does not match UTF-8 serialization")
    elif status in {"NO_DATA", "ERROR"}:
        if "p" in value or not isinstance(value.get("causa"), str) or not value["causa"].strip():
            raise ValueError("unavailable projection requires a cause and no payload")
    else:
        raise ValueError("unsupported projection status")
    return size


def _run_app(app_root: Path, status: str) -> dict:
    code = (
        "import json,sys; from lexical_projector import project; "
        "frame=json.load(sys.stdin); "
        "status=frame.pop('_status'); cause=frame.pop('_cause',None); "
        "print(json.dumps(project(frame,status=status,cause=cause).as_dict(),"
        "ensure_ascii=False,separators=(',',':')))"
    )
    frame = dict(FRAME, _status=status)
    if status != "LIVE":
        frame["_cause"] = "source unavailable in yardstick fixture"
    env = dict(os.environ, PYTHONPATH=str(app_root))
    result = subprocess.run([sys.executable, "-c", code], input=json.dumps(frame),
                            capture_output=True, text=True, cwd=app_root, env=env,
                            timeout=10)
    if result.returncode:
        raise ValueError("ERROR: app projector failed")
    return json.loads(result.stdout)


def verify(web_root: Path, app_root: Path) -> tuple[int, list[tuple[str, str, int]]]:
    schema_path = web_root / WEB_FILES[0]
    schema = _schema(schema_path)
    measurements = []
    for root, names in ((web_root, WEB_FILES), (app_root, APP_FILES)):
        for relative in names:
            path = root / relative
            if not path.is_file():
                raise ValueError("NO_DATA: required artifact is absent: " + relative)
            size = path.stat().st_size
            if size > PIECE_LIMIT:
                raise ValueError("ERROR: piece exceeds ceiling: " + relative)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            measurements.append((relative, digest, size))
    checked = 0
    for status in ("LIVE", "NO_DATA"):
        envelope = _run_app(app_root, status)
        validate_envelope(envelope, schema)
        checked += 1
    return checked, measurements


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web-root", type=Path, required=True)
    parser.add_argument("--app-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        checked, files = verify(args.web_root.resolve(), args.app_root.resolve())
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"LIVE · {checked}/2 states · {len(files)} source hashes · every piece <= {PIECE_LIMIT} B")
    for path, digest, size in files:
        print(f"{path} · {size} B · sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
