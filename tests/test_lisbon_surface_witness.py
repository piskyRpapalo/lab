"""Deterministic adversarial gates for the read-only Lisbon surface witness."""
import importlib.util
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "lisbon_surface_witness", ROOT / "bin/lisbon_surface_witness.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def nodes():
    return [
        {"id": "primer-ancla", "q": 0, "r": 0, "alive": True, "seal": "LIVE", "since": "2026-11-18"},
        {"id": "onexstation", "q": 1, "r": 0, "alive": True, "seal": "STALE", "since": "2026-11-04"},
        {"id": "doggee-s110", "q": 2, "r": 0, "alive": True, "seal": "STALE", "since": "2026-11-09"},
    ]


def payload(items=None):
    data = nodes() if items is None else items
    return json.dumps({
        "esquema": m.WORLD_SCHEMA,
        "colonia": {"nodes": data, "buildings": [], "units": []},
        "cobertura": {"estado": "MEDIDO", "valor": len(data), "fuente": "node_heartbeats"},
    }, separators=(",", ":")).encode()


SW = b"const VERSION = 'preceptoros-2026-25-jd';\n"


class SurfaceProjectionTests(unittest.TestCase):
    def test_matching_feeds_derive_live_from_seal_not_alive(self):
        receipt = m.build_receipt(payload(), payload(), SW,
                                  expected_sw="preceptoros-2026-25-ji")
        self.assertEqual(receipt["crossfeed"], "MATCH")
        self.assertEqual((receipt["live"], receipt["stale"],
                          receipt["nonanchor_live"], receipt["stale_alive"]),
                         (1, 2, 0, 2))
        self.assertEqual(receipt["sw_gate"], "FAIL(public_sw_not_expected)")
        self.assertTrue(receipt["anchor_live"])
        self.assertEqual(receipt["web_sha256"], hashlib.sha256(payload()).hexdigest())
        self.assertEqual(receipt["aduana_sha256"], receipt["web_sha256"])

    def test_no_owner_e2e_claim_from_matching_public_feed(self):
        extra = nodes()
        extra[1]["seal"] = "LIVE"
        receipt = m.build_receipt(payload(extra), payload(extra), SW)
        self.assertEqual(receipt["nonanchor_live"], 1)
        self.assertTrue(receipt["join_e2e"].startswith("NO_DATA"))
        self.assertTrue(receipt["notification"].startswith("NO_DATA"))

    def test_divergent_feeds_are_fail_closed(self):
        other = nodes()
        other[1]["seal"] = "LIVE"
        receipt = m.build_receipt(payload(), payload(other), SW)
        self.assertEqual(receipt["crossfeed"], "FAIL(feed_projection_mismatch)")
        self.assertNotIn("live", receipt)

    def test_historical_coverage_mismatch_is_not_accepted(self):
        p = json.loads(payload())
        p["cobertura"]["valor"] = 1
        with self.assertRaisesRegex(ValueError, "historical_coverage"):
            m.project_world(json.dumps(p).encode())

    def test_duplicate_identity_or_coordinates_are_rejected(self):
        duplicate = nodes()
        duplicate[1]["id"] = duplicate[0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate_node"):
            m.project_world(payload(duplicate))
        duplicate = nodes()
        duplicate[1]["q"] = duplicate[0]["q"]
        with self.assertRaisesRegex(ValueError, "duplicate_node"):
            m.project_world(payload(duplicate))

    def test_unknown_seal_and_wrong_types_rejected(self):
        for key, value in (("seal", "LOADING"), ("alive", 1),
                           ("q", True), ("id", "../../rack")):
            with self.subTest(key=key):
                altered = nodes()
                altered[1][key] = value
                with self.assertRaisesRegex(ValueError, "node_fields"):
                    m.project_world(payload(altered))

    def test_json_duplicate_key_and_nan_rejected(self):
        altered = payload().replace(b'"esquema":', b'"esquema":"other","esquema":', 1)
        with self.assertRaisesRegex(ValueError, "invalid_world_json"):
            m.project_world(altered)
        altered = payload().replace(b'"q":0', b'"q":NaN', 1)
        with self.assertRaisesRegex(ValueError, "invalid_world_json"):
            m.project_world(altered)

    def test_empty_and_oversized_rejected(self):
        for raw in (b"", b"x" * (m.MAX_JSON_BYTES + 1), None):
            with self.subTest(kind=type(raw)):
                with self.assertRaisesRegex(ValueError, "world_bytes"):
                    m.project_world(raw)

    def test_no_sources_have_no_invented_counts(self):
        rec = m.build_receipt(None, None, None,
                              causes={"web": "public_get_unavailable",
                                      "aduana": "public_get_unavailable"})
        self.assertTrue(rec["crossfeed"].startswith("NO_DATA"))
        self.assertNotIn("nonanchor_live", rec)
        self.assertEqual(rec["source_web"], "NO_DATA")

    def test_sw_source_must_be_observed(self):
        self.assertIsNone(m.parse_sw(b"self.NO_VERSION = 'fake';"))
        self.assertEqual(m.build_receipt(payload(), payload(), SW,
                                         expected_sw="preceptoros-2026-25-jd")["sw_gate"], "PASS")

    def test_receipt_size_and_no_raw_identifiers(self):
        rec = m.build_receipt(payload(), payload(), SW,
                              phone="DEVICE_PRESENT")
        raw = json.dumps(rec, separators=(",", ":")).encode()
        self.assertLess(len(raw), 1024)
        for forbidden in ("doggee-s110", "onexstation", "S11000", "x-heartbeat-key"):
            self.assertNotIn(forbidden, raw.decode())

    def test_adb_facts_do_not_leak_serials(self):
        serial = "S110001234567890"
        sample = ("List of devices attached\n" + serial +
                  " device usb:5-1 product:M22P_EEA model:S110 device:M22P transport_id:16\n")
        self.assertEqual(m.parse_adb(sample), "DEVICE_PRESENT")
        rec = m.build_receipt(payload(), payload(), SW, phone=m.parse_adb(sample))
        self.assertNotIn(serial, json.dumps(rec))
        self.assertEqual(m.parse_adb(sample.replace(" device ", " offline ", 1)),
                         "NO_DATA(s110_not_in_device_state)")

    def test_adb_is_never_invoked_without_optin(self):
        with patch.object(m, "probe_adb", side_effect=AssertionError("adb called")):
            with patch.object(m, "fetch_public",
                              side_effect=lambda k: (payload(), None) if k != "sw" else (SW, None)):
                with patch("builtins.print"):
                    m.main(["--live"])

    def test_non_allowlisted_public_url_rejected(self):
        with self.assertRaisesRegex(ValueError, "route_not_allowlisted"):
            m.fetch_public("https://any.other.host/")

    def test_unsupported_get_or_redirect_is_not_accepted(self):
        class FakeResponse:
            def __init__(self, url, body=b"{}"):
                self.status = 200
                self.url = url
                self.body = body
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def geturl(self): return self.url
            def read(self, n): return self.body[:n]
        class FakeOpener:
            def __init__(self, url): self.url = url; self.request = None
            def open(self, request, timeout):
                self.request = request
                return FakeResponse(self.url)
        good = FakeOpener(m.URLS["web"])
        data, cause = m.fetch_public("web", opener=good)
        self.assertEqual((data, cause), (b"{}", None))
        self.assertEqual(good.request.get_method(), "GET")
        self.assertEqual(good.request.full_url, m.URLS["web"])
        bad = FakeOpener("https://evil.invalid/steal")
        self.assertEqual(m.fetch_public("web", opener=bad),
                         (None, "response_url_or_status"))
        with self.assertRaisesRegex(ValueError, "redirect_denied"):
            m.NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.invalid/")

    def test_byte_ceiling_from_response(self):
        class Fake:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            status = 200
            def geturl(self): return m.URLS["web"]
            def read(self, n): return b"x" * n
        class Opener:
            def open(self, req, timeout): return Fake()
        self.assertEqual(m.fetch_public("web", opener=Opener()),
                         (None, "response_byte_limit"))


if __name__ == "__main__":
    unittest.main()
