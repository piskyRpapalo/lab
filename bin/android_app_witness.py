#!/usr/bin/env python3
"""Android personal APP / local-model witness: read-only ADB, no node enrollment.

Does not inspect application-private files, activate VPN, run inference, or copy APKs.
Outputs a scrubbed inventory. 'Packaged' is NEVER a claim that inference works.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess

SCHEMA = "preceptoros.lab.android-app-witness/1"
CANONICAL = "org.preceptoros.app"
LEGACY = "org.preceptoros.mvp"
OWNER_CERT_SHA256 = "16761a1e61376506acf4abdadfdddeb96ff18b4cc80a3d98205c91648e4c010f"
INTERESTING = (
    "assets/offline-mini.gguf", "lib/arm64-v8a/libmini_llama.so",
)
TAIL_LIMIT = 262144
PATH_PATTERN = re.compile(r"^/data/app/[a-zA-Z0-9_~=+./-]+/base\.apk$")
NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,24}$")
HEX = re.compile(r"^[0-9a-f]{64}$")


class EvidenceError(Exception):
    """Fail closed on malformed or inaccessible evidence."""


def u16(blob: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(blob):
        raise EvidenceError("zip_truncated")
    return struct.unpack_from("<H", blob, offset)[0]


def u32(blob: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(blob):
        raise EvidenceError("zip_truncated")
    return struct.unpack_from("<I", blob, offset)[0]


def u64(blob: bytes, offset: int) -> int:
    if offset < 0 or offset + 8 > len(blob):
        raise EvidenceError("zip_truncated")
    return struct.unpack_from("<Q", blob, offset)[0]


def sized(blob: bytes, offset: int) -> tuple[bytes, int]:
    count = u32(blob, offset)
    if count > len(blob) - offset - 4:
        raise EvidenceError("signature_length_invalid")
    return blob[offset + 4:offset + 4 + count], offset + 4 + count


def apk_tail_evidence(tail: bytes, file_size: int) -> dict:
    if not (0 < file_size <= 2**34) or len(tail) > TAIL_LIMIT:
        raise EvidenceError("apk_size_invalid")
    eocd = tail.rfind(b"PK\x05\x06")
    if eocd < 0:
        raise EvidenceError("zip_eocd_missing")
    count = u16(tail, eocd + 10)
    central_size = u32(tail, eocd + 12)
    central_offset = u32(tail, eocd + 16)
    if count > 10000 or central_offset + central_size > file_size:
        raise EvidenceError("zip_central_invalid")
    central = len(tail) - (file_size - central_offset)
    if central < 0 or central + central_size > len(tail):
        raise EvidenceError("zip_central_not_in_tail")
    pos = central
    selected = {}
    for _ in range(count):
        if tail[pos:pos+4] != b"PK\x01\x02":
            raise EvidenceError("zip_central_entry_invalid")
        length = u16(tail, pos + 28)
        extra = u16(tail, pos + 30)
        comment = u16(tail, pos + 32)
        if pos + 46 + length + extra + comment > len(tail):
            raise EvidenceError("zip_name_truncated")
        filename = tail[pos + 46:pos + 46 + length].decode("utf-8", "replace")
        if filename in INTERESTING:
            if filename in selected:
                raise EvidenceError("duplicate_critical_apk_asset")
            selected[filename] = {
                "bytes_uncompressed": u32(tail, pos + 24),
                "zip_method": u16(tail, pos + 10),
            }
        pos += 46 + length + extra + comment
    if pos != central + central_size:
        raise EvidenceError("zip_central_size_mismatch")

    # APK signature scheme v2 block immediately precedes the ZIP central directory.
    if tail[central - 16:central] != b"APK Sig Block 42":
        raise EvidenceError("signer_v2_block_missing")
    full_size = u64(tail, central - 24)
    start = central - full_size - 8
    if start < 0 or u64(tail, start) != full_size:
        raise EvidenceError("signer_v2_block_incomplete")
    certificates = []
    idx = start + 8
    while idx < central - 24:
        length = u64(tail, idx)
        if length < 4 or idx + 8 + length > central - 24:
            raise EvidenceError("signer_v2_pair_invalid")
        kind = u32(tail, idx + 8)
        value = tail[idx + 12:idx + 8 + length]
        idx += 8 + length
        if kind != 0x7109871A:
            continue
        signers, _ = sized(value, 0)
        signer, _ = sized(signers, 0)
        signed, _ = sized(signer, 0)
        _, next_pos = sized(signed, 0)
        certblob, _ = sized(signed, next_pos)
        cert, _ = sized(certblob, 0)
        certificates.append(hashlib.sha256(cert).hexdigest())
    if not certificates:
        raise EvidenceError("certificate_unavailable")
    return {
        "zip_entries": count,
        "cert_sha256": certificates[0],
        "packaged_assets": selected,
        "apk_size_bytes": file_size,
    }


def package_set(raw: bytes) -> set[str]:
    lines = raw.decode("utf-8", "replace").splitlines()
    return {line[len("package:"):].strip() for line in lines
            if line.startswith("package:") and line[len("package:"):].strip()}


def assess(enabled: set[str], disabled: set[str], package: str | None,
           info: dict | None, app_version: dict | None) -> dict:
    active = sorted(enabled.intersection((CANONICAL, LEGACY)))
    preserved = sorted(disabled.intersection((CANONICAL, LEGACY)))
    canonical = active == [CANONICAL]
    signer = info.get("cert_sha256") if info else None
    if signer is not None and not HEX.fullmatch(signer):
        raise EvidenceError("invalid_certificate_digest")
    assets = info.get("packaged_assets", {}) if info else {}
    packaged = all(assets.get(key, {}).get("bytes_uncompressed", 0) > 0
                   for key in INTERESTING)
    # An installation has one enabled front door only if its package ID matches
    # the canonical release and its certificate is the owner's.
    single = canonical and signer == OWNER_CERT_SHA256 and packaged
    return {
        "enabled_app_packages": active,
        "disabled_legacy_preserved": preserved,
        "canonical_install": {"state": "PASS" if single else "FAIL",
                              "cause": None if single else (
                                  "legacy_and_canonical_both_enabled" if len(active) > 1 else
                                  "canonical_not_enabled" if not canonical else
                                  "certificate_or_native_asset_unverified")},
        "inspected_package": package or "NO_DATA(package_absent)",
        "installed_version": app_version or {"state": "NO_DATA", "cause": "package_version_unavailable"},
        "package_certificate": {"state": "VERIFIED_INSTALLED_BLOCK" if signer else "NO_DATA",
                                "source": "android_installed_apk_v2_block_not_independent_crypto_verify",
                                "owner_matches": signer == OWNER_CERT_SHA256 if signer else None},
        "models_in_apk": {
            "state": "VERIFIED_PACKAGED" if packaged else "NO_DATA",
            "cause": None if packaged else "gguf_or_jni_missing_or_unreadable",
            "model_asset_size_bytes": assets.get(INTERESTING[0], {}).get("bytes_uncompressed"),
            "jni_library_size_bytes": assets.get(INTERESTING[1], {}).get("bytes_uncompressed"),
        },
        "inference": {"state": "NO_DATA", "cause": "no_physical_JNI_generation_witness"},
        "tailscale_and_remote_hexelion": {
            "state": "NO_DATA", "cause": "signed_private_model_turn_not_measured"},
        "beelink_node_admission": "NOT_REQUESTED",
        "migration": {"state": "HOLD" if not canonical else "NOT_REQUIRED",
                      "cause": "cross_package_user_data_export_needed" if not canonical else None},
    }


def adb(serial: str, *args: str, deadline: int = 12) -> bytes:
    try:
        run = subprocess.run(["adb", "-s", serial, *args], capture_output=True,
                             timeout=deadline, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise EvidenceError("adb_unavailable_or_timeout") from exc
    if run.returncode != 0:
        raise EvidenceError("adb_command_rejected")
    return run.stdout


def witness(serial: str, alias: str) -> dict:
    enabled = package_set(adb(serial, "shell", "pm", "list", "packages", "-e", "--user", "0"))
    disabled = package_set(adb(serial, "shell", "pm", "list", "packages", "-d", "--user", "0"))
    target = CANONICAL if CANONICAL in enabled else LEGACY if LEGACY in enabled else None
    result = {"schema": SCHEMA, "device_alias": alias, "read_only": True}
    if target is None:
        result["assessment"] = assess(enabled, disabled, None, None, None)
        return result
    paths = adb(serial, "shell", "pm", "path", target).decode("utf-8", "replace").splitlines()
    paths = [x[len("package:"):].strip() for x in paths if x.startswith("package:")]
    if (len(paths) != 1 or not PATH_PATTERN.fullmatch(paths[0])
            or ".." in paths[0].split("/")):
        raise EvidenceError("apk_path_unexpected")
    apk_path = paths[0]
    raw_size = adb(serial, "shell", "stat", "-c", "%s", apk_path).decode("ascii", "replace").strip()
    if not raw_size.isdigit():
        raise EvidenceError("apk_size_missing")
    size = int(raw_size)
    tail = adb(serial, "exec-out", "tail", "-c", str(TAIL_LIMIT), apk_path, deadline=25)
    info = apk_tail_evidence(tail, size)
    # Dumpsys contains no private application data; only extract version fields.
    rows = adb(serial, "shell", "dumpsys", "package", target, deadline=18).decode("utf-8", "replace")
    code = re.search(r"\bversionCode=(\d+)\b", rows)
    name = re.search(r"\bversionName=([a-zA-Z0-9._-]{1,60})\b", rows)
    version = ({"version_code": int(code.group(1)), "version_name": name.group(1)}
               if code and name else None)
    result["assessment"] = assess(enabled, disabled, target, info, version)
    result["witness"] = {"archive_entries": info["zip_entries"],
                         "certificate_sha256": info["cert_sha256"]}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True, help="ADB serial; excluded from receipt")
    parser.add_argument("--alias", required=True, help="Public device alias, no private serial")
    options = parser.parse_args(argv)
    if not NAME_PATTERN.fullmatch(options.alias):
        parser.error("alias must be short and machine-safe")
    try:
        result = witness(options.serial, options.alias)
    except EvidenceError as exc:
        result = {"schema": SCHEMA, "device_alias": options.alias, "read_only": True,
                  "state": "NO_DATA", "cause": str(exc)}
    result["receipt_sha256"] = hashlib.sha256(json.dumps(
        result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return 0 if result.get("state") != "NO_DATA" else 2


if __name__ == "__main__":
    raise SystemExit(main())
