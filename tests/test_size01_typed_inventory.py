"""Size limits attach to declared categories, not all JSON or Markdown."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

p = Path(__file__).resolve().parents[1] / "bin" / "size01_typed_inventory.py"
spec = importlib.util.spec_from_file_location("size01", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TestTypedInventory(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.policy = {"schema": m.SCHEMA, "assignments": {}}

    def tearDown(self):
        self.temp.cleanup()

    def put(self, name, length, kind):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x" * length)
        self.policy["assignments"][name] = kind

    def summary(self, *names):
        return m.inspect(self.root, list(names), self.policy)

    def test_frame_1023_green(self):
        self.put("frame.json", 1023, "receipt_frame")
        self.assertEqual(self.summary("frame.json")["state"], "MEASURED_SCOPED")

    def test_frame_1024_red(self):
        self.put("frame.json", 1024, "receipt_frame")
        self.assertEqual(self.summary("frame.json")["state"], "RED")

    def test_lexical_1024_red(self):
        self.put("lexical.json", 1024, "lexical_packet")
        self.assertEqual(self.summary("lexical.json")["state"], "RED")

    def test_piece_16384_green(self):
        self.put("README.md", 16384, "declared_piece")
        self.assertEqual(self.summary("README.md")["state"], "MEASURED_SCOPED")

    def test_piece_16385_red(self):
        self.put("README.md", 16385, "declared_piece")
        self.assertEqual(self.summary("README.md")["state"], "RED")

    def test_raw_benchmark_over_1kb_not_red(self):
        self.put("benchmarks/fixture.json", 30000, "raw_benchmark_artifact")
        r = self.summary("benchmarks/fixture.json")
        self.assertEqual(r["rows"][0]["state"], "OUT_OF_SCOPE")
        self.assertEqual(r["state"], "MEASURED_SCOPED")

    def test_unclassified_nodata(self):
        (self.root / "unknown.json").write_text("{}")
        self.assertEqual(self.summary("unknown.json")["state"], "NO_DATA")

    def test_orphan_policy_nodata(self):
        self.policy["assignments"]["missing.json"] = "receipt_frame"
        self.assertEqual(self.summary()["state"], "NO_DATA")

    def test_duplicate_paths_refused(self):
        with self.assertRaises(ValueError):
            self.summary("dup", "dup")

    def test_unknown_category_refused(self):
        self.policy["assignments"]["x"] = "universal_1024"
        with self.assertRaises(ValueError):
            self.summary("x")

    def test_symlink_outside_blocked(self):
        external = self.root / "data"
        external.write_text("ok")
        (self.root / "link").symlink_to(external)
        self.policy["assignments"]["link"] = "receipt_frame"
        self.assertNotEqual(self.summary("link")["rows"][0]["state"], "GREEN")

    def test_symlink_directory_blocked(self):
        self.put("real/fixture.json", 2, "receipt_frame")
        (self.root / "alias").symlink_to(self.root / "real", target_is_directory=True)
        self.policy["assignments"]["alias/fixture.json"] = "receipt_frame"
        self.assertNotEqual(self.summary("alias/fixture.json")["rows"][0]["state"], "GREEN")

    def test_empty_inventory_nodata(self):
        self.assertEqual(self.summary()["state"], "NO_DATA")

    def test_directory_escape_rejected(self):
        self.policy["assignments"]["../private"] = "receipt_frame"
        self.assertNotEqual(self.summary("../private")["rows"][0]["state"], "GREEN")

    def test_path_not_emitted(self):
        self.put("private_original_name.json", 2, "receipt_frame")
        r = self.summary("private_original_name.json")
        self.assertNotIn("private_original_name", str(r))

    def test_no_content_in_output(self):
        self.put("fixture.json", 3, "receipt_frame")
        self.assertNotIn("xxx", str(self.summary("fixture.json")))

    def test_measured_counts(self):
        self.put("a.json", 1023, "receipt_frame")
        self.put("b.json", 1024, "receipt_frame")
        r = self.summary("a.json", "b.json")
        self.assertEqual(r["tally"]["GREEN"], 1)
        self.assertEqual(r["tally"]["RED"], 1)


if __name__ == "__main__":
    unittest.main()
