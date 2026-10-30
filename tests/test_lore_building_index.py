import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate_index(data):
    assert len(data["objects"]) == 9
    source_ids = {source["id"] for source in data["sources"]}
    for row in data["objects"]:
        assert row["index_key"]
        assert row["sources"] and set(row["sources"]).issubset(source_ids)
        if row["id_state"] == "NO_DATA":
            assert row["id"] is None
            assert row.get("cause", "").strip()
            assert "claim" not in row


class LoreBuildingIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "lore/building-index.json").read_text(encoding="utf-8"))

    def test_nine_entries_and_four_canonical_objects(self):
        rows = self.data["objects"]
        self.assertEqual(len(rows), 9)
        known = [r for r in rows if r["id_state"] == "MEDIDO"]
        missing = [r for r in rows if r["id_state"] == "NO_DATA"]
        self.assertEqual(len(known), 4)
        self.assertEqual(len(missing), 5)
        self.assertTrue(all(r["status"] == "HECHO" for r in known))

    def test_missing_objects_have_causes_not_invented_ids(self):
        for row in self.data["objects"]:
            self.assertTrue(row.get("index_key"))
            if row["id_state"] == "NO_DATA":
                self.assertIsNone(row["id"])
                self.assertTrue(row.get("cause", "").strip())
                self.assertNotIn("claim", row)

    def test_every_claim_cites_existing_sources(self):
        ids = {source["id"] for source in self.data["sources"]}
        for row in self.data["objects"]:
            self.assertTrue(row["sources"])
            self.assertTrue(set(row["sources"]).issubset(ids))
        self.assertEqual(self.data["authority"], "ideas13oct v2.0.1")
        self.assertTrue(self.data["source_conflicts"])

    def test_sabotage_missing_cause_is_rejected_by_contract(self):
        broken = json.loads(json.dumps(self.data))
        row = next(r for r in broken["objects"] if r["id_state"] == "NO_DATA")
        row.pop("cause")
        with self.assertRaises(AssertionError):
            validate_index(broken)


if __name__ == "__main__":
    unittest.main()
