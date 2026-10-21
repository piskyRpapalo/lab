#!/usr/bin/env python3
import argparse
import datetime
import hashlib
import json
import platform
import re
import sys
from pathlib import Path

LIMIT = 1024
SCHEMA = "lab.study-spec/1"
VARIABLES = ("TREND_VECTOR", "BASE_MODELS", "RAG_CORPUS", "LORA_ADAPTER", "HARDWARE_MATRIX")
RINGS = ("FORGE", "EDGE", "SANCTUARY")
HASH = re.compile(r"^[a-f0-9]{64}$")


def cargar_spec(ruta):
    try:
        raw = Path(ruta).read_bytes()
    except OSError as error:
        return {"estado": "NO_DATA", "causa": type(error).__name__}
    if len(raw) >= LIMIT:
        return {"estado": "RECHAZADA", "causa": "study spec reaches the 1024-byte ceiling"}
    try:
        spec = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return {"estado": "RECHAZADA", "causa": "study spec is not UTF-8 JSON"}
    result = validar_variables(spec)
    return {"estado": "VALIDA", "spec": spec} if result["estado"] == "VALIDA" else result


def validar_variables(spec):
    if not isinstance(spec, dict) or set(spec) != {"schema", "variables"} or spec.get("schema") != SCHEMA:
        return {"estado": "RECHAZADA", "causa": "study spec schema is invalid"}
    values = spec.get("variables")
    if not isinstance(values, dict) or set(values) != set(VARIABLES):
        return {"estado": "RECHAZADA", "causa": "study spec must contain exactly five variables"}
    for name in VARIABLES:
        value = values[name]
        if not isinstance(value, dict):
            return {"estado": "RECHAZADA", "causa": f"{name} must be an object"}
        if name == "HARDWARE_MATRIX":
            if value.get("state") == "NO_DATA":
                if set(value) != {"state", "cause", "rings"} or not value.get("cause"):
                    return {"estado": "RECHAZADA", "causa": "hardware absence needs a cause and rings"}
                rings = value["rings"]
                if not isinstance(rings, dict) or set(rings) != set(RINGS) or any(rings[r] for r in RINGS):
                    return {"estado": "RECHAZADA", "causa": "NO_DATA hardware rings must be empty"}
            elif value.get("state") == "DECLARED":
                rings = value.get("rings")
                if set(value) != {"state", "rings"} or not isinstance(rings, dict) or set(rings) != set(RINGS):
                    return {"estado": "RECHAZADA", "causa": "declared hardware matrix is malformed"}
                if any(not isinstance(rings[r], list) or any(not isinstance(x, str) or not HASH.fullmatch(x) for x in rings[r]) for r in RINGS):
                    return {"estado": "RECHAZADA", "causa": "ring members must be SHA-256 references"}
            else:
                return {"estado": "RECHAZADA", "causa": "hardware matrix state is invalid"}
            continue
        if value.get("state") == "NO_DATA":
            if set(value) != {"state", "cause"} or not value.get("cause"):
                return {"estado": "RECHAZADA", "causa": f"{name} absence needs a cause"}
            continue
        hashes = value.get("sha256")
        expected = {"state", "sha256"}
        if value.get("state") != "DECLARED" or set(value) != expected:
            return {"estado": "RECHAZADA", "causa": f"{name} declaration is malformed"}
        multiple = name in ("BASE_MODELS", "RAG_CORPUS")
        if multiple and (not isinstance(hashes, list) or not hashes or len(hashes) != len(set(hashes))):
            return {"estado": "RECHAZADA", "causa": f"{name} requires unique hashes"}
        if not multiple and not isinstance(hashes, str):
            return {"estado": "RECHAZADA", "causa": f"{name} requires one hash"}
        items = hashes if multiple else [hashes]
        if any(not isinstance(item, str) or not HASH.fullmatch(item) for item in items):
            return {"estado": "RECHAZADA", "causa": f"{name} contains an invalid hash"}
    return {"estado": "VALIDA"}


def despachar_a_anillos(spec):
    valid = validar_variables(spec)
    if valid["estado"] != "VALIDA":
        return valid
    matrix = spec["variables"]["HARDWARE_MATRIX"]
    rings = matrix.get("rings", {})
    return {"estado": "PLAN", "anillos": {name: {"asignaciones": list(rings.get(name, [])),
        "estado": "NO_DATA" if not rings.get(name) else "DECLARADO",
        "causa": "no approved machine assignment" if not rings.get(name) else None} for name in RINGS}}


def ejecutar_en_anillo(spec, anillo):
    plan = despachar_a_anillos(spec)
    if anillo not in RINGS or plan.get("estado") != "PLAN":
        return {"estado": "RECHAZADA", "causa": "ring or study spec is invalid"}
    assignment = plan["anillos"][anillo]
    if not assignment["asignaciones"]:
        return {"estado": "NO_DATA", "causa": "ring_offline: no approved machine assignment"}
    return {"estado": "NO_DATA", "causa": "ring_offline: no signed local dispatch adapter"}


def consolidar_resultados(resultados):
    items = list(resultados) if isinstance(resultados, (list, tuple)) else []
    states = [item.get("estado", "NO_DATA") for item in items if isinstance(item, dict)]
    state = "ROJO" if "ROJO" in states or "RECHAZADA" in states else "NO_DATA" if not states or "NO_DATA" in states else "SIMULATED"
    return {"estado": state, "anillos": items, "no_data": sum(value == "NO_DATA" for value in states)}


def emitir_recibo(resultado, maquina=None, fecha=None):
    ring_results = resultado.get("anillos", [])
    rings = {}
    if isinstance(ring_results, (list, tuple)):
        for index, value in enumerate(ring_results[:len(RINGS)]):
            if isinstance(value, dict):
                rings[RINGS[index]] = {"state": value.get("estado", "NO_DATA"),
                                       "cause": value.get("causa")}
    body = {"schema": "lab.study-runner-receipt/1", "state": resultado.get("estado", "NO_DATA"),
            "machine": maquina or platform.machine() or "NO_DATA",
            "date": fecha or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rings": rings,
            "cause": resultado.get("causa") or ("one or more ring results are NO_DATA" if resultado.get("estado") == "NO_DATA" else None),
            "sha256": hashlib.sha256(json.dumps(resultado, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "signature": {"state": "NO_DATA", "cause": "no signing key is configured"}}
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) >= LIMIT:
        return json.dumps({"schema": body["schema"], "state": "NO_DATA", "cause": "receipt reaches the 1024-byte ceiling"}, separators=(",", ":"))
    return encoded


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--spec", type=Path, default=Path(__file__).resolve().parents[1] / "study_spec.json")
    args = parser.parse_args(argv)
    loaded = cargar_spec(args.spec)
    if loaded["estado"] != "VALIDA":
        result = {"estado": loaded["estado"], "anillos": [], "causa": loaded["causa"]}
    else:
        plan = despachar_a_anillos(loaded["spec"])
        rings = [ejecutar_en_anillo(loaded["spec"], ring) for ring in RINGS] if not args.dry_run else list(plan["anillos"].values())
        result = consolidar_resultados(rings)
    text = emitir_recibo(result)
    if len(text.encode("utf-8")) >= LIMIT:
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
