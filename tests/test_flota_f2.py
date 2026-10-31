import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def is_field(value):
    if not isinstance(value, dict):
        return False
    if value.get("estado") == "MEDIDO":
        return set(value) == {"estado", "valor", "fuente", "hora"} and bool(value["fuente"]) and bool(value["hora"])
    if value.get("estado") == "NO_DATA":
        return set(value) == {"estado", "causa", "fuente", "intento"} and bool(value["causa"].strip()) and bool(value["fuente"]) and bool(value["intento"])
    return False


def walk_fields(value, path="$", failures=None):
    failures = failures if failures is not None else []
    if isinstance(value, dict) and "estado" in value:
        if not is_field(value):
            failures.append(path)
        elif value["estado"] == "MEDIDO":
            walk_fields(value["valor"], path + ".valor", failures)
        return failures
    if isinstance(value, dict):
        for key, child in value.items():
            walk_fields(child, path + "." + key, failures)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_fields(child, f"{path}[{index}]", failures)
    return failures


def snapshot_failures(snapshot):
    failures = []
    nodes = snapshot.get("nodes") if isinstance(snapshot, dict) else None
    if not isinstance(nodes, list) or not nodes:
        return ["nodes"]
    ids = [node.get("id") for node in nodes]
    cells = [(node.get("q"), node.get("r")) for node in nodes]
    if len(ids) != len(set(ids)):
        failures.append("duplicate map node id")
    if len(cells) != len(set(cells)):
        failures.append("duplicate map cell")
    coverage = snapshot.get("coverage", {})
    if coverage.get("estado") != "MEDIDO" or coverage.get("valor") != len(nodes):
        failures.append("coverage does not match map nodes")
    if snapshot.get("measured_at") != coverage.get("hora"):
        failures.append("snapshot measurement times differ")
    return failures


class FleetF2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "flota.json").read_text(encoding="utf-8"))
        cls.schema = json.loads((ROOT / "contracts/preceptoros.flota-2.schema.json").read_text(encoding="utf-8"))

    def test_version_and_schema(self):
        self.assertEqual(self.data["schema"], "preceptoros.flota/2")
        self.assertEqual(self.schema["title"], self.data["schema"])
        self.assertIn("map_heartbeat_snapshot", self.schema["required"])
        self.assertEqual(self.data["nodes"][0]["placement"], "first-row: sovereign inference station")
        self.assertEqual(len(self.data["nodes"]), 1)

    def test_public_map_snapshot_matches_measured_aliases_cells_and_live_state(self):
        snapshot = self.data["map_heartbeat_snapshot"]
        self.assertEqual(snapshot["schema"], "preceptoros.openworld-estado/2")
        self.assertEqual(snapshot["source"], "https://api.preceptoros.org/api/v1/latidos")
        self.assertEqual(snapshot["measured_at"], "2026-10-31T18:41:32Z")
        self.assertEqual(snapshot["coverage"], {
            "estado": "MEDIDO", "valor": 2,
            "fuente": "public D7 response · node_heartbeats",
            "hora": "2026-10-31T18:41:32Z"
        })
        self.assertEqual(snapshot["nodes"], [
            {"id": "primer-ancla", "q": 0, "r": 0, "alive": True, "seal": "LIVE", "since": "2026-10-31"},
            {"id": "onexstation", "q": 1, "r": 0, "alive": True, "seal": "LIVE", "since": "2026-10-31"}
        ])
        self.assertEqual(snapshot_failures(snapshot), [])

    def test_duplicate_alias_cell_and_coverage_mismatch_are_rejected(self):
        snapshot = json.loads(json.dumps(self.data["map_heartbeat_snapshot"]))
        snapshot["nodes"][1]["q"] = snapshot["nodes"][0]["q"]
        snapshot["nodes"][1]["r"] = snapshot["nodes"][0]["r"]
        self.assertIn("duplicate map cell", snapshot_failures(snapshot))
        snapshot["nodes"][1]["q"] = 1
        snapshot["nodes"][1]["r"] = 0
        snapshot["coverage"]["valor"] = 3
        self.assertIn("coverage does not match map nodes", snapshot_failures(snapshot))

    def test_map_presence_does_not_claim_physical_fleet_coverage(self):
        self.assertEqual(self.data["fleet_coverage"]["estado"], "NO_DATA")
        self.assertIn("censo privado", self.data["fleet_coverage"]["causa"].lower())
        self.assertEqual(self.data["nodes"][0]["identity"]["estado"], "NO_DATA")
        self.assertEqual(self.data["nodes"][0]["heartbeat"]["estado"], "NO_DATA")

    def test_all_measurements_are_typed_and_gaps_have_causes(self):
        self.assertEqual(walk_fields(self.data), [])

    def test_ram_and_vram_are_independent(self):
        memory = self.data["nodes"][0]["memory"]
        self.assertNotEqual(memory["ram_total_bytes"]["valor"], memory["vram_total_bytes"]["valor"])
        self.assertNotIn("combined_memory_bytes", memory)
        self.assertNotIn("usable_total_bytes", memory)

    def test_model_size_gap_and_active_state_are_explicit(self):
        models = self.data["nodes"][0]["models"]
        self.assertEqual(len(models["catalog"]), 2)
        self.assertEqual(models["catalog"][1]["tamano_bytes"]["estado"], "NO_DATA")
        self.assertEqual(models["active"]["valor"], [])
        self.assertEqual(models["queue"]["estado"], "NO_DATA")
        digest = models["catalog"][0]["manifest_sha256"]["valor"]
        self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_private_identifiers_are_not_published(self):
        serialized = json.dumps(self.data, ensure_ascii=False)
        self.assertNotRegex(serialized, r"(?i)100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d+\.\d+")
        self.assertNotIn("/home/", serialized)
        self.assertNotRegex(serialized, r"ssh-(ed25519|rsa|ecdsa)\s+AAAA")
        self.assertNotRegex(serialized, r"(?i)(api[_-]?key|heartbeat[_-]?key_hash)")

    def test_sabotage_missing_no_data_cause_is_rejected(self):
        broken = json.loads(json.dumps(self.data))
        del broken["nodes"][0]["memory"]["swap_total_bytes"]["causa"]
        self.assertTrue(walk_fields(broken))

    def test_ram_vram_are_not_added_in_any_output_field(self):
        memory = self.data["nodes"][0]["memory"]
        self.assertEqual(memory["ram_total_bytes"]["valor"], 65963548672)
        self.assertEqual(memory["vram_total_bytes"]["valor"], 68719476736)
        self.assertFalse(any("sum" in key.lower() or "combined" in key.lower() for key in memory))


if __name__ == "__main__":
    unittest.main()
