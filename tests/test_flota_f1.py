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
        else:
            if value["estado"] == "MEDIDO":
                walk_fields(value["valor"], path + ".valor", failures)
        return failures
    if isinstance(value, dict):
        for key, child in value.items():
            walk_fields(child, path + "." + key, failures)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_fields(child, f"{path}[{index}]", failures)
    return failures


class FleetF1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "flota.json").read_text(encoding="utf-8"))
        cls.schema = json.loads((ROOT / "contracts/preceptoros.flota-1.schema.json").read_text(encoding="utf-8"))

    def test_version_and_first_row(self):
        self.assertEqual(self.data["schema"], "preceptoros.flota/1")
        self.assertEqual(self.schema["title"], self.data["schema"])
        self.assertTrue(set(self.schema["required"]).issubset(self.data))
        self.assertEqual(self.data["nodes"][0]["placement"], "first-row: sovereign inference station")
        self.assertEqual(len(self.data["nodes"]), 1)
        node_schema = self.schema["$defs"]["node"]
        self.assertTrue(set(node_schema["required"]).issubset(self.data["nodes"][0]))

    def test_all_measurements_are_typed_and_gaps_have_causes(self):
        self.assertEqual(walk_fields(self.data), [])
        self.assertEqual(self.data["fleet_coverage"]["estado"], "NO_DATA")
        self.assertTrue(self.data["fleet_coverage"]["causa"])

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
