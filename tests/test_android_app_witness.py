"""The Android app witness must fail closed and never confuse model assets with inference."""
import hashlib
import io
import json
import struct
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util
import zipfile


spec = importlib.util.spec_from_file_location(
    "android_witness", Path(__file__).resolve().parents[1] / "bin" / "android_app_witness.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def fake_evidence():
    return {
        "cert_sha256": app.OWNER_CERT_SHA256,
        "packaged_assets": {
            app.INTERESTING[0]: {"bytes_uncompressed": 105454144},
            app.INTERESTING[1]: {"bytes_uncompressed": 52608936},
        },
    }


def lp(blob):
    return struct.pack("<I", len(blob)) + blob


def zip_with_signature():
    # Synthetically place a v2 signing block before the ZIP central directory.
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as z:
        z.writestr(app.INTERESTING[0], b"GGUF"+b"\0"*8)
        z.writestr(app.INTERESTING[1], b"NATIVE"*4)
    original = out.getvalue()
    idx = original.rfind(b"PK\x05\x06")
    central = struct.unpack_from("<I", original, idx+16)[0]
    fake_der = b"\x30\x08FAKECERT"
    signer_data = lp(b"") + lp(lp(fake_der)) + lp(b"")
    signer = lp(signer_data) + lp(b"") + lp(b"")
    payload = lp(lp(signer))
    pair = struct.pack("<QI", len(payload) + 4, 0x7109871A) + payload
    size = len(pair) + 24
    block = struct.pack("<Q", size) + pair + struct.pack("<Q", size) + b"APK Sig Block 42"
    amended = bytearray(original[:central] + block + original[central:])
    end = amended.rfind(b"PK\x05\x06")
    struct.pack_into("<I", amended, end+16, central + len(block))
    return bytes(amended), fake_der


class AndroidAppWitnessCases(unittest.TestCase):
    def test_zip_v2_cert_and_model_assets_without_pulling_whole_apk(self):
        blob, cert = zip_with_signature()
        result = app.apk_tail_evidence(blob[-app.TAIL_LIMIT:], len(blob))
        self.assertEqual(result["zip_entries"], 2)
        self.assertEqual(result["cert_sha256"], hashlib.sha256(cert).hexdigest())
        self.assertEqual(result["packaged_assets"][app.INTERESTING[0]]["bytes_uncompressed"], 12)

    def test_zip_without_signature_never_declares_owner(self):
        blob, _ = zip_with_signature()
        broken = blob.replace(b"APK Sig Block 42", b"APK Sig Block 4X", 1)
        with self.assertRaises(app.EvidenceError):
            app.apk_tail_evidence(broken, len(broken))

    def test_one_canonical_enabled_with_disabled_legacy_is_good(self):
        report = app.assess({app.CANONICAL}, {app.LEGACY}, app.CANONICAL,
                            fake_evidence(), {"version_code": 7, "version_name": "0.3.0-mvp"})
        self.assertEqual(report["canonical_install"]["state"], "PASS")
        self.assertEqual(report["models_in_apk"]["state"], "VERIFIED_PACKAGED")
        self.assertEqual(report["inference"]["state"], "NO_DATA")
        self.assertEqual(report["tailscale_and_remote_hexelion"]["state"], "NO_DATA")

    def test_two_enabled_apps_is_red_even_if_the_canonical_is_signed(self):
        report = app.assess({app.CANONICAL, app.LEGACY}, set(), app.CANONICAL,
                            fake_evidence(), {"version_code": 7})
        self.assertEqual(report["canonical_install"]["state"], "FAIL")
        self.assertEqual(report["canonical_install"]["cause"],
                         "legacy_and_canonical_both_enabled")

    def test_legacy_only_requires_migration_and_cannot_be_called_updated(self):
        report = app.assess({app.LEGACY}, set(), app.LEGACY,
                            fake_evidence(), {"version_code": 6})
        self.assertEqual(report["canonical_install"]["state"], "FAIL")
        self.assertEqual(report["migration"]["state"], "HOLD")
        self.assertEqual(report["migration"]["cause"], "cross_package_user_data_export_needed")

    def test_wrong_signer_fails_even_with_model_and_correct_package(self):
        info = fake_evidence()
        info["cert_sha256"] = "0" * 64
        report = app.assess({app.CANONICAL}, set(), app.CANONICAL, info, {"version_code": 7})
        self.assertEqual(report["canonical_install"]["state"], "FAIL")
        self.assertEqual(report["package_certificate"]["owner_matches"], False)

    def test_missing_native_runtime_never_claims_inference(self):
        info = fake_evidence()
        del info["packaged_assets"][app.INTERESTING[1]]
        report = app.assess({app.CANONICAL}, set(), app.CANONICAL, info, {"version_code": 7})
        self.assertEqual(report["canonical_install"]["state"], "FAIL")
        self.assertEqual(report["models_in_apk"]["state"], "NO_DATA")

    def test_report_does_not_emit_sensitive_serial(self):
        blob, _ = zip_with_signature()
        serial = "PRIVATE-DEVICE-SERIAL"
        def fake_adb(*args, **kw):
            if args[1:5] == ("shell", "pm", "list", "packages"):
                return b"package:org.preceptoros.app\n"
            if "path" in args:
                return b"package:/data/app/~~SYNTHETIC-01/org.preceptoros.app-foo/base.apk\n"
            if "stat" in args:
                return str(len(blob)).encode()
            if "exec-out" in args:
                return blob
            if "dumpsys" in args:
                return b"versionCode=7 minSdk=26\nversionName=0.3.0-mvp\n"
            raise AssertionError(args)
        with patch.object(app, "adb", side_effect=fake_adb):
            result = app.witness(serial, "Sample")
        wire = json.dumps(result)
        self.assertNotIn(serial, wire)
        self.assertIn('"read_only": true', wire.lower())
        self.assertEqual(result["assessment"]["inference"]["state"], "NO_DATA")

    def test_bad_alias_is_not_accepted(self):
        self.assertIsNone(app.NAME_PATTERN.fullmatch("private owner address"))
        self.assertIsNone(app.NAME_PATTERN.fullmatch("../etc/passwd"))


if __name__ == "__main__":
    unittest.main()
