#!/usr/bin/env python3
"""Compare Bubble scene geometry across three theme frames, ignoring layouts."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

GREEN, RED, NO_DATA = "GREEN", "RED", "NO_DATA"
THEMES = ("basic", "atlantis", "zombie")
FRAME_LIMIT = 1024
METADATA_KEYS = {"bands", "change", "sound", "soundCause", "style", "light", "id", "t"}
ATOM_TEXT_KEYS = {"r", "tx"}
ITEM_PALETTE_KEYS = {"f", "s"}


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _geometry(frame: dict) -> dict:
    scene = {key: value for key, value in frame.items() if key not in METADATA_KEYS and key != "atoms"}
    atoms = []
    for atom in frame.get("atoms", []):
        if not isinstance(atom, dict):
            atoms.append(atom)
            continue
        item = {key: value for key, value in atom.items() if key not in ATOM_TEXT_KEYS and key != "i"}
        primitives = []
        for primitive in atom.get("i", []):
            if isinstance(primitive, dict):
                primitives.append({key: value for key, value in primitive.items() if key not in ITEM_PALETTE_KEYS})
            else:
                primitives.append(primitive)
        item["i"] = primitives
        atoms.append(item)
    scene["atoms"] = atoms
    return scene


def _palette(frame: dict) -> list[str]:
    values = set()
    bands = frame.get("bands", [])
    if isinstance(bands, list):
        values.update(value for value in bands if isinstance(value, str))
    for atom in frame.get("atoms", []) if isinstance(frame.get("atoms"), list) else []:
        if not isinstance(atom, dict):
            continue
        for primitive in atom.get("i", []) if isinstance(atom.get("i"), list) else []:
            if isinstance(primitive, dict):
                values.update(primitive[key] for key in ITEM_PALETTE_KEYS if isinstance(primitive.get(key), str))
    return sorted(values)


def compare(frames: dict[str, dict], *, layouts: dict | None = None,
            frame_bytes: dict[str, bytes] | None = None) -> dict[str, object]:
    missing = [theme for theme in THEMES if theme not in frames]
    if missing:
        return {"state": NO_DATA, "cause": "missing theme frame: " + ", ".join(missing)}
    geometry_hashes, palette_hashes, sizes = {}, {}, {}
    geometry_values = []
    for theme in THEMES:
        frame = frames[theme]
        if not isinstance(frame, dict):
            return {"state": NO_DATA, "cause": f"{theme} frame is not a JSON object"}
        raw = (frame_bytes or {}).get(theme, _canonical(frame))
        sizes[theme] = len(raw)
        if frame.get("v") != "preceptoros.bubble/1":
            return {"state": RED, "cause": f"{theme} frame has unsupported Bubble version", "frame_bytes": sizes}
        if sizes[theme] > FRAME_LIMIT:
            return {"state": RED, "cause": f"{theme} frame exceeds 1,024 UTF-8 bytes", "frame_bytes": sizes}
        if not isinstance(frame.get("atoms"), list) or not frame["atoms"]:
            return {"state": NO_DATA, "cause": f"{theme} frame has no scene atoms"}
        geometry = _geometry(frame)
        palette = _palette(frame)
        geometry_values.append(_canonical(geometry))
        geometry_hashes[theme] = hashlib.sha256(_canonical(geometry)).hexdigest()
        palette_hashes[theme] = hashlib.sha256(_canonical(palette)).hexdigest()
    geometry_equal = len(set(geometry_values)) == 1
    palette_distinct = len(set(palette_hashes.values())) == len(THEMES)
    causes = []
    if not geometry_equal:
        causes.append("scene geometry differs between themes")
    if not palette_distinct:
        causes.append("theme palette fingerprints are not all distinct")
    return {
        "schema": "preceptoros.lab.bubble-theme-parity/1",
        "state": GREEN if not causes else RED,
        "cause": "; ".join(causes) if causes else None,
        "themes": list(THEMES),
        "frame_bytes": sizes,
        "frame_limit_bytes": FRAME_LIMIT,
        "geometry_sha256": geometry_hashes,
        "geometry_equal": geometry_equal,
        "palette_sha256": palette_hashes,
        "palette_distinct": palette_distinct,
        "layout_ignored": True,
        "layout_inputs_consumed": False,
        "evidence_scope": "Bubble scene data only; rendered visual parity and binding to served examples are not measured",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for theme in THEMES:
        parser.add_argument(f"--{theme}", type=Path, required=True, dest=theme)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    frames, raw = {}, {}
    try:
        for theme in THEMES:
            data = getattr(args, theme).read_bytes()
            raw[theme] = data
            frames[theme] = json.loads(data.decode("utf-8"))
        result = compare(frames, frame_bytes=raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        result = {"state": NO_DATA, "cause": f"frame input unavailable or invalid ({type(exc).__name__})"}
    rendered = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return {GREEN: 0, RED: 1, NO_DATA: 2}[result["state"]]


if __name__ == "__main__":
    raise SystemExit(main())
