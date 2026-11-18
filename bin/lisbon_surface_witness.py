#!/usr/bin/env python3
"""Independent, read-only Lisbon surface witness. Not an admission authority.

No HTTP writes, remote shell, credentials, private records or arbitrary URLs.
Public presence is not human approval or proof of owner authorization.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import urllib.error
import urllib.request

SCHEMA = "preceptoros.lab.lisbon-surface-witness/1"
WORLD_SCHEMA = "preceptoros.openworld-estado/2"
URLS = {
    "web": "https://preceptoros.org/api/world-state",
    "aduana": "https://api.preceptoros.org/api/v1/latidos",
    "sw": "https://preceptoros.org/sw.js",
}
MAX_JSON_BYTES = 16384
MAX_SW_BYTES = 131072
MAX_RECEIPT_BYTES = 1024
ANCHOR = "primer-ancla"
NODE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z")
SW_VERSION = re.compile(rb"\bconst VERSION\s*=\s*['\"]([A-Za-z0-9._-]{1,64})['\"]")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect_denied")


def fetch_public(kind, *, opener=None):
    """GET a fixed public endpoint. Never use ambient HTTP proxy credentials."""
    if kind not in URLS:
        raise ValueError("route_not_allowlisted")
    opener = opener or urllib.request.build_opener(
        urllib.request.ProxyHandler({}), NoRedirect()
    )
    req = urllib.request.Request(
        URLS[kind],
        method="GET",
        headers={
            "User-Agent": "Hexelion-Lab-Surface-Witness/1",
            "Accept": "application/json" if kind != "sw" else "text/javascript",
        },
    )
    ceiling = MAX_SW_BYTES if kind == "sw" else MAX_JSON_BYTES
    try:
        with opener.open(req, timeout=5) as response:
            if response.geturl() != URLS[kind] or response.status != 200:
                return None, "response_url_or_status"
            data = response.read(ceiling + 1)
            if len(data) > ceiling:
                return None, "response_byte_limit"
            return data, None
    except (OSError, ValueError, urllib.error.URLError):
        return None, "public_get_unavailable"


def _unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate_json_key")
        obj[key] = value
    return obj


def _invalid_number(value):
    raise ValueError("non_finite_json")


def project_world(raw):
    """Strictly project public seals; historical alive:true is NOT LIVE."""
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_JSON_BYTES:
        raise ValueError("world_bytes_missing_or_over_limit")
    try:
        obj = json.loads(
            raw, object_pairs_hook=_unique, parse_constant=_invalid_number
        )
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise ValueError("invalid_world_json") from exc
    if not isinstance(obj, dict) or obj.get("esquema") != WORLD_SCHEMA:
        raise ValueError("wrong_world_schema")
    colonia, cobertura = obj.get("colonia"), obj.get("cobertura")
    if not isinstance(colonia, dict) or not isinstance(cobertura, dict):
        raise ValueError("world_containers_missing")
    nodes = colonia.get("nodes")
    if not isinstance(nodes, list) or len(nodes) > 128:
        raise ValueError("world_node_count_invalid")
    if (cobertura.get("estado") != "MEDIDO"
            or type(cobertura.get("valor")) is not int
            or cobertura["valor"] != len(nodes)):
        raise ValueError("historical_coverage_mismatch")
    found, cells = set(), set()
    projection = []
    for row in nodes:
        if not isinstance(row, dict):
            raise ValueError("node_object_invalid")
        name, seal, alive = row.get("id"), row.get("seal"), row.get("alive")
        q, r = row.get("q"), row.get("r")
        if (not isinstance(name, str) or not NODE_ID.fullmatch(name)
                or seal not in ("LIVE", "STALE")
                or type(alive) is not bool or type(q) is not int
                or type(r) is not int or abs(q) > 4096 or abs(r) > 4096):
            raise ValueError("node_fields_invalid")
        if name in found or (q, r) in cells:
            raise ValueError("duplicate_node_or_cell")
        found.add(name)
        cells.add((q, r))
        projection.append((name, q, r, seal, alive))
    return tuple(sorted(projection))


def _field_state(raw, cause):
    if raw is None:
        return {"state": "NO_DATA", "cause": cause or "missing_public_source"}
    try:
        return {"state": "MEDIDO", "nodes": project_world(raw),
                "digest": hashlib.sha256(raw).hexdigest()}
    except ValueError as exc:
        return {"state": "NO_DATA", "cause": str(exc)}


def parse_sw(raw):
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_SW_BYTES:
        return None
    match = SW_VERSION.search(raw)
    return match.group(1).decode("ascii") if match else None


def parse_adb(raw):
    """Keep only S110 presence. Never return serial, USB path or ADB output."""
    if not isinstance(raw, str) or "List of devices attached" not in raw:
        return "NO_DATA(adb_unavailable)"
    for line in raw.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device" and "model:S110" in parts[2:]:
            return "DEVICE_PRESENT"
    return "NO_DATA(s110_not_in_device_state)"


def probe_adb():
    try:
        output = subprocess.run(
            ["adb", "devices", "-l"], capture_output=True,
            text=True, timeout=5, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return "NO_DATA(adb_unavailable)"
    if output.returncode != 0:
        return "NO_DATA(adb_command_failed)"
    return parse_adb(output.stdout[:8192])


def build_receipt(web, aduana, sw, *, causes=None, expected_sw=None,
                  phone="NO_DATA(adb_not_checked)", now=None):
    causes = causes or {}
    w = _field_state(web, causes.get("web"))
    a = _field_state(aduana, causes.get("aduana"))
    sw_name = parse_sw(sw)
    when = now or datetime.now(timezone.utc)
    if when.utcoffset() != timezone.utc.utcoffset(when):
        raise ValueError("utc_instant_required")
    result = {
        "schema": SCHEMA,
        "utc": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": "beelink",
        "source_web": w["state"],
        "source_aduana": a["state"],
        "source_sw": "MEDIDO" if sw_name else "NO_DATA",
        "web_sha256": w.get("digest", "NO_DATA"),
        "aduana_sha256": a.get("digest", "NO_DATA"),
        "sw_sha256": hashlib.sha256(sw).hexdigest() if sw_name else "NO_DATA",
        "crossfeed": "NO_DATA(missing_or_invalid_feed)",
        "sw_version": sw_name or "NO_DATA(unreadable_sw_version)",
        "sw_gate": "NO_DATA(expected_sw_not_supplied)",
        "s110_adb": phone,
        "join_e2e": "NO_DATA(owner_approval_credential_chain_unobserved)",
        "notification": "NO_DATA(owner_inbox_not_checked)",
    }
    if sw_name is None and sw is not None:
        result["sw_gate"] = "NO_DATA(sw_version_not_extracted)"
    if expected_sw is not None:
        result["sw_gate"] = ("PASS" if sw_name == expected_sw
                             else "FAIL(public_sw_not_expected)" if sw_name
                             else "NO_DATA(public_sw_unavailable)")
    if w["state"] == "MEDIDO" and a["state"] == "MEDIDO":
        if w["nodes"] == a["nodes"]:
            rows = w["nodes"]
            result.update({
                "crossfeed": "MATCH",
                "anchor_live": any(x[0] == ANCHOR and x[3] == "LIVE" for x in rows),
                "live": sum(x[3] == "LIVE" for x in rows),
                "stale": sum(x[3] == "STALE" for x in rows),
                "stale_alive": sum(x[3] == "STALE" and x[4] for x in rows),
                "nonanchor_live": sum(x[3] == "LIVE" and x[0] != ANCHOR for x in rows),
            })
        else:
            result["crossfeed"] = "FAIL(feed_projection_mismatch)"
    else:
        result["crossfeed"] = "NO_DATA({};{})".format(
            w.get("cause", "web_ok"), a.get("cause", "aduana_ok")
        )
    encoded = json.dumps(result, ensure_ascii=True, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode()
    if len(encoded) >= MAX_RECEIPT_BYTES:
        raise ValueError("receipt_exceeds_house_limit")
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true",
                   help="perform 3 bounded read-only public HTTPS GET requests")
    p.add_argument("--adb", action="store_true",
                   help="optionally query adb devices -l (no serial output)")
    p.add_argument("--expected-sw", default=None)
    args = p.parse_args(argv)
    if not args.live:
        p.error("--live is required; tests use the pure build_receipt function")
    if args.expected_sw is not None and not re.fullmatch(
            r"[A-Za-z0-9._-]{1,64}", args.expected_sw):
        p.error("invalid expected SW token")
    samples, causes = {}, {}
    for name in URLS:
        samples[name], causes[name] = fetch_public(name)
    receipt = build_receipt(
        samples["web"], samples["aduana"], samples["sw"], causes=causes,
        expected_sw=args.expected_sw,
        phone=probe_adb() if args.adb else "NO_DATA(adb_not_checked)",
    )
    print(json.dumps(receipt, ensure_ascii=True, sort_keys=True,
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
