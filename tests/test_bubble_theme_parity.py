import json
import tempfile
import unittest
from pathlib import Path

from bin.check_bubble_theme_parity import compare, GREEN, RED, NO_DATA


class ThemeParity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        base = {
            "v": "preceptoros.bubble/1", "id": "scene", "cv": [412, 515],
            "atoms": [{"k": "island", "r": "one island", "i": [
                {"o": "blob", "x": 190, "y": 180, "rx": 70, "ry": 30, "seed": "island", "f": "ocean", "s": "ink"}
            ]}],
        }
        self.frames = {}
        for theme, bands, fill in (("basic", ["ink", "paper"], "paper"),
                                   ("atlantis", ["cyan", "ocean"], "cyan"),
                                   ("zombie", ["vermilion.base", "ink"], "vermilion.base")):
            frame = json.loads(json.dumps(base))
            frame["bands"] = bands
            frame["atoms"][0]["i"][0]["f"] = fill
            self.frames[theme] = frame

    def tearDown(self):
        self.temp.cleanup()

    def test_equal_scene_geometry_and_distinct_palettes_pass(self):
        layouts = {"basic": {"panel": "left"}, "atlantis": {"panel": "bottom"}, "zombie": {"panel": "overlay"}}
        result = compare(self.frames, layouts=layouts)
        self.assertEqual(result["state"], GREEN)
        self.assertTrue(result["layout_ignored"])
        self.assertEqual(len(set(result["geometry_sha256"].values())), 1)
        self.assertEqual(len(set(result["palette_sha256"].values())), 3)

    def test_scene_coordinate_drift_is_red(self):
        self.frames["zombie"]["atoms"][0]["i"][0]["x"] += 1
        self.assertEqual(compare(self.frames)["state"], RED)

    def test_reused_palette_is_red(self):
        self.frames["zombie"]["bands"] = self.frames["basic"]["bands"]
        self.frames["zombie"]["atoms"][0]["i"][0]["f"] = "paper"
        self.assertEqual(compare(self.frames)["state"], RED)

    def test_frame_over_1024_bytes_is_red(self):
        self.frames["basic"]["change"] = ["x" * 1100]
        self.assertEqual(compare(self.frames)["state"], RED)

    def test_missing_theme_is_no_data(self):
        result = compare({"basic": self.frames["basic"]})
        self.assertEqual(result["state"], NO_DATA)
        self.assertIn("missing", result["cause"])

    def test_bad_frame_version_is_red(self):
        self.frames["basic"]["v"] = "other"
        self.assertEqual(compare(self.frames)["state"], RED)


if __name__ == "__main__":
    unittest.main()
