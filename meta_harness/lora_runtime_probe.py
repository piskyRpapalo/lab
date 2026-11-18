"""Read-only llama.cpp LoRA readback witness for an operator-selected local runtime.

This is an observation adapter for the existing armory/head-eligibility contracts,
not a second registry, loader, dispatcher, cache authority or execution grant.
No source prompts or model responses are transmitted or recorded.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import urllib.error
import urllib.request

from .delegation import sha

SCHEMA = "preceptoros.lora-runtime-witness/1"
HEX = re.compile(r"^[0-9a-f]{64}$")
LOCAL = re.compile(r"^http://127[.]0[.]0[.]1:([0-9]{2,5})/?$")
NODES = frozenset({"rack", "station", "tower", "forge", "sentinel"})
MAX_RESPONSE = 16384
MAX_ARTIFACT_BYTES = 64 * 1024**3  # upper safety bound, not a hardware claim


class WitnessError(Exception):
    """Named, scrub-safe failure; do not pass untrusted details to receipts."""


def _digest_file(path: str, expected: str) -> None:
    if type(path) is not str or not path.startswith("/") or type(expected) is not str or not HEX.fullmatch(expected):
        raise WitnessError("ARTIFACT_INPUT_INVALID")
    try:
        flags = (os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) |
                 getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0))
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as stream:
            first = os.fstat(stream.fileno())
            if not stat.S_ISREG(first.st_mode) or not 0 < first.st_size <= MAX_ARTIFACT_BYTES:
                raise WitnessError("ARTIFACT_NOT_REGULAR")
            digest = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
            last = os.fstat(stream.fileno())
            if (first.st_ino, first.st_dev, first.st_size, first.st_mtime_ns) != (
                last.st_ino, last.st_dev, last.st_size, last.st_mtime_ns
            ):
                raise WitnessError("ARTIFACT_CHANGED_DURING_READ")
    except WitnessError:
        raise
    except OSError:
        raise WitnessError("ARTIFACT_UNAVAILABLE") from None
    if digest.hexdigest() != expected:
        raise WitnessError("ARTIFACT_DIGEST_MISMATCH")


def _unique(pairs):
    record = {}
    for key, value in pairs:
        if key in record:
            raise WitnessError("JSON_DUPLICATE_KEY")
        record[key] = value
    return record


def _parse(data: bytes):
    if type(data) is not bytes or not 0 < len(data) <= MAX_RESPONSE:
        raise WitnessError("RESPONSE_SIZE_OR_TYPE")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_unique,
                          parse_constant=lambda _value: (_ for _ in ()).throw(
                              WitnessError("NONFINITE_JSON")))
    except WitnessError:
        raise
    except (UnicodeError, ValueError, TypeError):
        raise WitnessError("RESPONSE_JSON_INVALID") from None


def local_endpoint(value: str) -> str:
    if type(value) is not str:
        raise WitnessError("ENDPOINT_NOT_LOOPBACK")
    match = LOCAL.fullmatch(value)
    if match is None or not 1024 <= int(match.group(1)) <= 65535:
        raise WitnessError("ENDPOINT_NOT_LOOPBACK")
    return "http://127.0.0.1:" + str(int(match.group(1)))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise WitnessError("REDIRECT_REFUSED")


def get_local(endpoint: str, route: str) -> bytes:
    base = local_endpoint(endpoint)
    if route not in ("/props", "/lora-adapters"):
        raise WitnessError("ROUTE_NOT_ALLOWED")
    request = urllib.request.Request(base + route, method="GET",
                                     headers={"Accept": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)
    try:
        with opener.open(request, timeout=2) as response:
            if response.geturl() != request.full_url or response.status != 200:
                raise WitnessError("HTTP_STATUS_OR_ORIGIN")
            result = response.read(MAX_RESPONSE + 1)
    except WitnessError:
        raise
    except (OSError, urllib.error.URLError, ValueError):
        raise WitnessError("RUNTIME_UNREACHABLE") from None
    if len(result) > MAX_RESPONSE:
        raise WitnessError("RESPONSE_SIZE_OR_TYPE")
    return result


def _reported(props, adapters, base_path: str, adapter_path: str):
    if type(props) is not dict or type(adapters) is not list or len(adapters) > 128:
        raise WitnessError("RUNTIME_SCHEMA_INVALID")
    # The runtime's self-report is not cryptographic attestation of loaded weights.
    if props.get("model_path") != base_path:
        raise WitnessError("RUNTIME_BASE_PATH_UNVERIFIED")
    seen, match, canonical = set(), None, []
    for item in adapters:
        required = {"id", "path", "scale"}
        # Current llama.cpp also returns task_name and prompt_prefix. These
        # are operator-untrusted strings and never leave this witness.
        if type(item) is not dict or not required <= set(item) <= (required | {"task_name", "prompt_prefix"}):
            raise WitnessError("RUNTIME_SCHEMA_INVALID")
        if any(type(item[k]) is not str or len(item[k]) > 4096
               for k in ("task_name", "prompt_prefix") if k in item):
            raise WitnessError("RUNTIME_SCHEMA_INVALID")
        identifier, path, scale = item["id"], item["path"], item["scale"]
        if (type(identifier) is not int or identifier < 0 or identifier in seen
                or type(path) is not str or len(path) > 4096
                or type(scale) not in (int, float) or not math.isfinite(scale)
                or not -16 <= scale <= 16):
            raise WitnessError("RUNTIME_SCHEMA_INVALID")
        seen.add(identifier)
        canonical.append([identifier, hashlib.sha256(path.encode()).hexdigest(), float(scale),
                          hashlib.sha256(item.get("task_name", "").encode()).hexdigest(),
                          hashlib.sha256(item.get("prompt_prefix", "").encode()).hexdigest()])
        if path == adapter_path:
            if match is not None:
                raise WitnessError("RUNTIME_DUPLICATE_ADAPTER")
            match = (identifier, scale)
    if match is None:
        raise WitnessError("RUNTIME_ADAPTER_NOT_LOADED")
    return match, canonical


def snapshot(*, endpoint: str, node: str, base_path: str, base_sha256: str,
             adapter_path: str, adapter_sha256: str, fetch=None, now=None) -> dict:
    """Read two stable live snapshots and hash local operator-pinned artifact bytes.

    Success means only host files and runtime paths correspond to the claimed
    snapshot; it DOES NOT attest loaded tensor bytes or an actual LoRA inference.
    Callers must not use this result as permission to dispatch or reuse KV.
    """
    record = dict(schema=SCHEMA, state="NO_DATA", cause="UNVERIFIED",
                  node=node if type(node) is str and node in NODES else "NO_DATA", base_ref=None,
                  adapter_ref=None, adapter_id=None, scale=None,
                  snapshot_ref=None, observed_at=None, origin="LOCAL_READBACK",
                  dispatch_authorized=False, cache_reuse_authorized=False,
                  promotion="NOT_AUTHORIZED")
    def finish(cause: str):
        record["cause"] = cause
        record["receipt_ref"] = sha(record)
        if len(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()) >= 1024:
            raise ValueError("receipt_budget")
        return record
    try:
        local_endpoint(endpoint)  # reject remote endpoint even with injected fetcher
        if type(node) is not str or node not in NODES or any(type(v) is not str for v in (
                base_path, base_sha256, adapter_path, adapter_sha256)):
            raise WitnessError("INPUT_INVALID")
        if base_path == adapter_path:
            raise WitnessError("BASE_ADAPTER_COLLISION")
        reader = fetch if fetch is not None else lambda route: get_local(endpoint, route)
        if not callable(reader):
            raise WitnessError("READER_INVALID")
        first_props, first_adapters = _parse(reader("/props")), _parse(reader("/lora-adapters"))
        first_match, first_rows = _reported(first_props, first_adapters, base_path, adapter_path)
        _digest_file(base_path, base_sha256)
        _digest_file(adapter_path, adapter_sha256)
        second_props, second_adapters = _parse(reader("/props")), _parse(reader("/lora-adapters"))
        second_match, second_rows = _reported(second_props, second_adapters, base_path, adapter_path)
        if (first_match, first_rows, first_props) != (second_match, second_rows, second_props):
            raise WitnessError("RUNTIME_SNAPSHOT_CHANGED")
        instant = datetime.now(timezone.utc) if now is None else now
        if not isinstance(instant, datetime) or instant.tzinfo is None:
            raise WitnessError("CLOCK_INVALID")
        record.update(state="SNAPSHOT_OBSERVED", cause="PATHS_AND_FILES_ONLY_NOT_INFERENCE",
                      base_ref=base_sha256, adapter_ref=adapter_sha256,
                      adapter_id=first_match[0], scale=float(first_match[1]),
                      snapshot_ref=sha(first_rows), observed_at=instant.astimezone(
                          timezone.utc).isoformat())
        return finish(record["cause"])
    except WitnessError as error:
        return finish(str(error))
    except Exception:
        return finish("HOST_OR_RUNTIME_ERROR")


def prepare_request_head(*, witness: dict, base_ref: str, adapter_ref: str,
                         session_ref: str, context_ref: str, tool_scope_ref: str,
                         permission_ref: str, verify_witness, now: datetime,
                         mode: str = "adapter") -> dict:
    """Bind an operator-chosen adapter SHA to a catalog ID, never choose by model text.

    The engine can silently accept a request referring to a nonexistent adapter
    and return HTTP 200 with the base output. This guard maps only a witnessed
    adapter digest to an ID, and still does NOT authorize the request, attest
    that the engine applied it, or permit any KV reuse.
    """
    row = dict(schema="preceptoros.lora-request-binding/1", state="NO_DATA",
               cause="UNVERIFIED", selection_ref=None, lora=[],
               cache_prompt=False, dispatch_authorized=False, cache_reuse_authorized=False,
               promotion="NOT_AUTHORIZED")
    def finish(cause: str):
        row["cause"] = cause
        row["receipt_ref"] = sha(row)
        if len(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()) >= 1024:
            raise ValueError("receipt_budget")
        return row
    try:
        if type(mode) is not str or mode not in ("base", "adapter"):
            return finish("REQUEST_MODE_INVALID")
        refs = (base_ref, adapter_ref, session_ref, context_ref,
                tool_scope_ref, permission_ref)
        if not all(type(v) is str and HEX.fullmatch(v) for v in refs):
            return finish("SCOPE_OR_DIGEST_INVALID")
        if (type(witness) is not dict or witness.get("schema") != SCHEMA
                or witness.get("state") != "SNAPSHOT_OBSERVED"
                or witness.get("origin") != "LOCAL_READBACK"
                or witness.get("dispatch_authorized") is not False
                or witness.get("cache_reuse_authorized") is not False
                or witness.get("promotion") != "NOT_AUTHORIZED"
                or len(json.dumps(witness, default=str).encode()) >= 1024):
            return finish("WITNESS_CONTRACT_INVALID")
        ref = witness.get("receipt_ref")
        if (type(ref) is not str or not HEX.fullmatch(ref)
                or ref != sha({k: v for k, v in witness.items() if k != "receipt_ref"})):
            return finish("WITNESS_SEAL_INVALID")
        if witness.get("base_ref") != base_ref or witness.get("adapter_ref") != adapter_ref:
            return finish("WITNESS_MODEL_OR_HEAD_MISMATCH")
        identifier = witness.get("adapter_id")
        if type(identifier) is not int or identifier < 0:
            return finish("WITNESS_HEAD_ID_INVALID")
        if not isinstance(now, datetime) or now.tzinfo is None:
            return finish("CLOCK_INVALID")
        try:
            observed = datetime.fromisoformat(witness["observed_at"])
            if observed.tzinfo is None:
                return finish("WITNESS_TIME_INVALID")
            age = (now.astimezone(timezone.utc) -
                   observed.astimezone(timezone.utc)).total_seconds()
            if not 0 <= age <= 120:
                return finish("WITNESS_STALE_OR_FUTURE")
        except (TypeError, ValueError, KeyError):
            return finish("WITNESS_TIME_INVALID")
        if not callable(verify_witness):
            return finish("HOST_WITNESS_REQUIRED")
        # A self-hash does not prove host origin or that current permissions hold.
        # The callback must independently recheck source/grants/current server.
        if verify_witness(dict(witness), dict(
                session_ref=session_ref, context_ref=context_ref,
                tool_scope_ref=tool_scope_ref, permission_ref=permission_ref)) is not True:
            return finish("HOST_WITNESS_NOT_CURRENT")
        binding = dict(base_ref=base_ref, adapter_ref=adapter_ref,
                       session_ref=session_ref, context_ref=context_ref,
                       tool_scope_ref=tool_scope_ref, permission_ref=permission_ref,
                       snapshot_ref=witness["snapshot_ref"], adapter_id=identifier,
                       mode=mode)
        if type(binding["snapshot_ref"]) is not str or not HEX.fullmatch(binding["snapshot_ref"]):
            return finish("WITNESS_SNAPSHOT_INVALID")
        # A per-request list names the head, never the global server state.
        # Cache remains OFF for adapter and base requests until switching/KV
        # invalidation is independently proven on this exact runtime.
        selected = [{"id": identifier, "scale": 1.0}] if mode == "adapter" else []
        row.update(state="PREPARED_ONLY", cause="NOT_AN_EXECUTION_OR_CACHE_GRANT",
                   selection_ref=sha(binding), lora=selected, cache_prompt=False)
        return finish(row["cause"])
    except Exception:
        return finish("HOST_OR_WITNESS_ERROR")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read-only local llama.cpp LoRA witness")
    parser.add_argument("--endpoint", required=True, help="numeric 127.0.0.1:<port> only")
    parser.add_argument("--node", required=True, choices=sorted(NODES))
    parser.add_argument("--base-path", required=True)
    parser.add_argument("--base-sha256", required=True)
    parser.add_argument("--adapter-path", required=True)
    parser.add_argument("--adapter-sha256", required=True)
    options = parser.parse_args(argv)
    result = snapshot(endpoint=options.endpoint, node=options.node,
                      base_path=options.base_path, base_sha256=options.base_sha256,
                      adapter_path=options.adapter_path, adapter_sha256=options.adapter_sha256)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["state"] == "SNAPSHOT_OBSERVED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
