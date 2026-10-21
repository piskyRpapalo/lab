import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "study_spec.json"
SCHEMA = ROOT / "data" / "study_spec.schema.json"


class StudySpecContractTests(unittest.TestCase):
    def _accepts(self, spec):
        if set(spec) != {"schema", "variables"} or spec["schema"] != "lab.study-spec/1":
            return False
        variables = spec["variables"]
        expected = {"TREND_VECTOR", "BASE_MODELS", "RAG_CORPUS", "LORA_ADAPTER", "HARDWARE_MATRIX"}
        if set(variables) != expected:
            return False
        for name, value in variables.items():
            if name == "HARDWARE_MATRIX":
                if set(value) == {"state", "cause", "rings"}:
                    if value["state"] != "NO_DATA" or not value["cause"]:
                        return False
                    rings = value["rings"]
                    if set(rings) != {"FORGE", "EDGE", "SANCTUARY"} or any(rings[key] for key in rings):
                        return False
                    continue
                if set(value) != {"state", "rings"} or value["state"] != "DECLARED":
                    return False
                rings = value["rings"]
                if set(rings) != {"FORGE", "EDGE", "SANCTUARY"}:
                    return False
                if any(not all(self._is_hash(item) for item in rings[key]) for key in rings):
                    return False
                continue
            if set(value) == {"state", "cause"}:
                if value["state"] != "NO_DATA" or not value["cause"]:
                    return False
                continue
            if name in {"BASE_MODELS", "RAG_CORPUS"}:
                hashes = value.get("sha256")
                if set(value) != {"state", "sha256"} or value["state"] != "DECLARED":
                    return False
                if not isinstance(hashes, list) or not hashes or len(hashes) != len(set(hashes)):
                    return False
                if not all(self._is_hash(item) for item in hashes):
                    return False
            elif set(value) != {"state", "sha256"} or value["state"] != "DECLARED" or not self._is_hash(value["sha256"]):
                return False
        return True

    @staticmethod
    def _is_hash(value):
        return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)

    def test_template_is_under_channel_ceiling_and_has_five_variables(self):
        raw = SPEC.read_bytes()
        self.assertLess(len(raw), 1024)
        spec = json.loads(raw)
        self.assertEqual(spec["schema"], "lab.study-spec/1")
        self.assertEqual(set(spec["variables"]), {
            "TREND_VECTOR", "BASE_MODELS", "RAG_CORPUS",
            "LORA_ADAPTER", "HARDWARE_MATRIX",
        })

    def test_unselected_values_keep_causes_instead_of_sample_data(self):
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        for name, value in spec["variables"].items():
            self.assertEqual(value["state"], "NO_DATA", name)
            self.assertTrue(value["cause"].strip(), name)
            self.assertNotIn("value", value, name)

    def test_hardware_matrix_declares_exactly_three_empty_rings(self):
        value = json.loads(SPEC.read_text(encoding="utf-8"))["variables"]["HARDWARE_MATRIX"]
        self.assertEqual(set(value["rings"]), {"FORGE", "EDGE", "SANCTUARY"})
        self.assertTrue(all(members == [] for members in value["rings"].values()))

    def test_schema_rejects_extra_top_level_fields(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("variables", schema["required"])
        self.assertEqual(set(schema["properties"]["variables"]["required"]), {
            "TREND_VECTOR", "BASE_MODELS", "RAG_CORPUS",
            "LORA_ADAPTER", "HARDWARE_MATRIX",
        })
        for name in schema["properties"]["variables"]["required"]:
            self.assertEqual(len(schema["properties"]["variables"]["properties"][name]["oneOf"]), 2)

    def test_invalid_declarations_fail_closed(self):
        template = json.loads(SPEC.read_text(encoding="utf-8"))
        self.assertTrue(self._accepts(template))
        cases = []
        for name in ("TREND_VECTOR", "BASE_MODELS", "RAG_CORPUS", "LORA_ADAPTER", "HARDWARE_MATRIX"):
            value = json.loads(json.dumps(template))
            value["variables"][name]["state"] = "DECLARED"
            cases.append(value)
        value = json.loads(json.dumps(template))
        value["extra"] = True
        cases.append(value)
        self.assertEqual(sum(self._accepts(value) for value in cases), 0)


if __name__ == "__main__":
    unittest.main()
