#!/usr/bin/env python3
import argparse
import datetime
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA = "preceptoros.reporte-mantenimiento/1"
LIMIT = 1024
SUMMARY = re.compile(r"Ran (\d+) tests? in [0-9.]+s")
APP_SUMMARY = re.compile(r"VERDE · (\d+)/(\d+)")


def _no_data(cause):
    return {"estado": "NO_DATA", "tests": None, "causa": cause}


def _run(root, command, timeout=1800, app=False):
    if root is None:
        return _no_data("repo path was not supplied")
    cwd = Path(root)
    if not cwd.is_dir():
        return _no_data("repo path is unavailable")
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return _no_data("gate timed out")
    except OSError as error:
        return _no_data(f"gate runner unavailable ({type(error).__name__})")
    output = result.stdout + "\n" + result.stderr
    digest = hashlib.sha256(output.encode("utf-8", errors="replace")).hexdigest()
    if app:
        match = APP_SUMMARY.search(output)
        if not match:
            return {"estado": "NO_DATA", "tests": None, "causa": "app gate summary missing", "sha256": digest}
        passed, total = map(int, match.groups())
    else:
        match = SUMMARY.search(output)
        if not match:
            return {"estado": "NO_DATA", "tests": None, "causa": "unittest summary missing", "sha256": digest}
        total = int(match.group(1))
        skipped = re.search(r"skipped=(\d+)", output)
        failed = re.search(r"failures=(\d+)", output)
        errors = re.search(r"errors=(\d+)", output)
        skipped_count = int(skipped.group(1) if skipped else 0)
        failed_count = int(failed.group(1) if failed else 0)
        error_count = int(errors.group(1) if errors else 0)
        passed = total - skipped_count - failed_count - error_count
    if app:
        skipped_count = None
        failed_count = 0 if result.returncode == 0 else 1
        error_count = 0
    state = "VERDE" if result.returncode == 0 and failed_count == 0 and error_count == 0 else "ROJO"
    return {"estado": state, "tests": f"{passed}/{total}", "omitidas": skipped_count,
            "causa": None if state == "VERDE" else "gate returned red", "sha256": digest}


def correr_gates_web(root=None):
    return _run(root, [sys.executable, "test_web.py"])


def correr_gates_app(root=None):
    return _run(root, ["./bin/pruebas"], app=True)


def correr_gates_lab(root=None):
    return _run(root, [sys.executable, "-m", "unittest", "discover", "-s", "tests"])


def verificar_umbrales(reporte):
    gates = reporte.get("gates") if isinstance(reporte, dict) else None
    if not isinstance(gates, dict):
        return {"estado": "NO_DATA", "causa": "gate receipts are missing"}
    states = [gates.get(name, {}).get("estado", "NO_DATA") for name in ("web", "app", "lab")]
    if "ROJO" in states:
        return {"estado": "ROJO", "causa": "at least one gate is red"}
    if any(state != "VERDE" for state in states):
        return {"estado": "NO_DATA", "causa": "one or more gate receipts are unavailable"}
    return {"estado": "VERDE", "causa": None}


def consolidar(recibos):
    by_name = {name: value for name, value in zip(("web", "app", "lab"), recibos) if isinstance(value, dict)}
    for name in ("web", "app", "lab"):
        by_name.setdefault(name, _no_data("gate receipt was not supplied"))
    total = 0
    for value in by_name.values():
        match = re.fullmatch(r"(\d+)/(\d+)", str(value.get("tests")))
        if match:
            total += int(match.group(1))
    report = {"gates": by_name, "total_tests": total}
    verdict = verificar_umbrales(report)
    return {"schema": SCHEMA, "state": verdict["estado"], "cause": verdict["causa"],
            "observed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "machine": platform.machine() or "NO_DATA", "gates": by_name, "total_tests": total}


def emitir_reporte(reporte, signing_key=None):
    base = dict(reporte)
    base.pop("sha256", None)
    base.pop("signature", None)
    digest = hashlib.sha256(json.dumps(base, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    body = dict(base, sha256=digest)
    signature = {"estado": "NO_DATA", "causa": "no signing key is configured"}
    if signing_key:
        if not shutil.which("ssh-keygen") or not Path(signing_key).is_file():
            signature = {"estado": "NO_DATA", "causa": "ssh-keygen or signing key is unavailable"}
        else:
            with tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / "receipt"
                source.write_text(json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
                result = subprocess.run(["ssh-keygen", "-q", "-Y", "sign", "-n", "preceptoros-maintenance", "-f", signing_key, str(source)], capture_output=True, timeout=20)
                signed = source.with_name("receipt.sig")
                if result.returncode == 0 and signed.is_file():
                    signature = {"estado": "FIRMADO_POR_AGENTE", "valor": signed.read_text(encoding="utf-8")}
                else:
                    signature = {"estado": "NO_DATA", "causa": "signing command failed"}
    body["signature"] = signature
    text = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(text.encode("utf-8")) >= LIMIT:
        return json.dumps({"schema": SCHEMA, "state": "NO_DATA", "cause": "report reaches the 1024-byte ceiling"}, separators=(",", ":"))
    return text


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--web", type=Path)
    parser.add_argument("--app", type=Path)
    parser.add_argument("--lab", type=Path)
    parser.add_argument("--signing-key", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check and not any((args.web, args.app, args.lab)):
        receipts = [_no_data("repo path was not supplied") for _ in range(3)]
    else:
        receipts = [correr_gates_web(args.web), correr_gates_app(args.app), correr_gates_lab(args.lab)]
    text = emitir_reporte(consolidar(receipts), args.signing_key)
    print(text)
    return 0 if len(text.encode("utf-8")) < LIMIT else 1


if __name__ == "__main__":
    raise SystemExit(main())
