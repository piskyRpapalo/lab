import copy
import hashlib
import json
import unittest

from bin.verify_cold_install import PHASES, verify


def digest(data):
    return hashlib.sha256(data).hexdigest()


def receipt():
    allowed = digest(b"same origin")
    surfaces = ["chat", "joystick", "basic", "atlantis", "zombie", "voice",
                "no-sound", "reduced-motion", "navigation", "import", "errors"]
    phases = {}
    for phase in PHASES:
        requests = []
        phases[phase] = {"capture_complete": True, "request_count": 0,
                         "request_log_sha256": digest(b"[]"), "requests": requests}
    return {"schema": "lab.cold-install-receipt/1", "evidence_kind": "synthetic-test",
            "fresh_install": {"profile_cleared": True, "service_worker_cleared": True,
                              "browser_cache_cleared": True},
            "allowed_origin_sha256": [allowed],
            "artifacts": {c: {"expected_sha256": digest(c.encode()),
                              "installed_sha256": digest(c.encode()), "size_bytes": 10}
                          for c in ("web", "app")},
            "required_surface_ids": surfaces,
            "surfaces": {c: [{"id": s, "visible": True, "message_complete": True}
                             for s in surfaces] for c in ("web", "app")},
            "phases": phases}


class ColdInstallTests(unittest.TestCase):
    def test_complete_synthetic_contract_is_green(self):
        result = verify(receipt())
        self.assertEqual(result["verdict"], "GREEN")
        self.assertEqual(result["checks"]["phases"], 6)

    def test_missing_surface_is_no_data(self):
        doc = receipt()
        doc["surfaces"]["app"].pop()
        self.assertEqual(verify(doc)["verdict"], "NO_DATA")

    def test_changed_installed_artifact_is_red(self):
        doc = receipt()
        doc["artifacts"]["web"]["installed_sha256"] = "0" * 64
        self.assertEqual(verify(doc)["verdict"], "RED")

    def test_external_origin_is_red(self):
        doc = receipt()
        row = {"transport": "network", "origin_sha256": "f" * 64}
        doc["phases"]["first_launch"]["requests"] = [row]
        doc["phases"]["first_launch"]["request_count"] = 1
        doc["phases"]["first_launch"]["request_log_sha256"] = digest(
            json.dumps([row], sort_keys=True, separators=(",", ":")).encode())
        self.assertEqual(verify(doc)["verdict"], "RED")

    def test_offline_network_is_red_even_same_origin(self):
        doc = receipt()
        row = {"transport": "network", "origin_sha256": doc["allowed_origin_sha256"][0]}
        doc["phases"]["offline_launch"]["requests"] = [row]
        doc["phases"]["offline_launch"]["request_count"] = 1
        doc["phases"]["offline_launch"]["request_log_sha256"] = digest(
            json.dumps([row], sort_keys=True, separators=(",", ":")).encode())
        self.assertEqual(verify(doc)["verdict"], "RED")

    def test_truncated_capture_is_no_data(self):
        doc = receipt()
        doc["phases"]["offline_restart"]["capture_complete"] = False
        self.assertEqual(verify(doc)["verdict"], "NO_DATA")

    def test_forged_request_hash_is_red(self):
        doc = receipt()
        doc["phases"]["task_flow"]["request_log_sha256"] = "0" * 64
        self.assertEqual(verify(doc)["verdict"], "RED")


if __name__ == "__main__":
    unittest.main()
