"""Preserve device preflight uncertainty; do not infer phone or station identity."""
import json
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / "benchmarks/receipts/20261111-swarmi-hardware-preflight.json"

class TestSwarm01DevicePreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FILE.read_text(encoding="utf-8"))

    def test_no_android_claim(self):
        mobile = self.data["devices"]["android"]
        self.assertEqual(mobile["authorized_adb_devices"], 0)
        self.assertTrue(mobile["device_identity"].startswith("NO_DATA"))
        self.assertTrue(mobile["physical_app_test"].startswith("NO_DATA"))

    def test_station_is_tunnel_not_host(self):
        station = self.data["devices"]["station_tunnel"]
        self.assertFalse(station["host_inspected_directly"])
        self.assertTrue(station["os_and_gpu"].startswith("NO_DATA"))
        self.assertTrue(station["other_process_state"].startswith("NO_DATA"))

    def test_model_installed_does_not_mean_running(self):
        rack = self.data["devices"]["rack"]
        self.assertGreater(rack["ollama_models_installed"], 0)
        self.assertEqual(rack["ollama_models_loaded"], 0)
        self.assertTrue(self.data["model_quality"].startswith("NO_DATA"))

    def test_not_signed_or_physical(self):
        self.assertTrue(self.data["signature"].startswith("NO_DATA"))
        self.assertTrue(self.data["assistive_e2e"].startswith("NO_DATA"))
        self.assertEqual(self.data["scope"], "SNAPSHOT_NOT_CONTINUOUS")

    def test_no_sensitive_paths_or_hosts(self):
        raw = FILE.read_text(encoding="utf-8")
        for marker in ("/home/", "127.0.0.1", "192.168.", "token=", "private_key", "david", "pisky"):
            self.assertNotIn(marker, raw)

if __name__ == "__main__":
    unittest.main()
