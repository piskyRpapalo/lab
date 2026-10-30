import copy
import unittest

from benchmarks.norte_decor import movement_record
from benchmarks.norte_record import RecordError


def supplied_movement():
    frame = {"v": "preceptoros.bubble/1", "id": "prop-a", "t": 0,
             "atoms": [{"k": "prop-a", "r": "prop-a moves to cell 1,0.", "i": []}],
             "bands": ["cyan"], "change": ["prop-a moves to cell 1,0."],
             "sound": "NO_DATA: no waves declared", "soundCause": "no measured wave table",
             "seal": "SIMULATED"}
    move = {"id": "prop-a", "from": {"q": 0, "r": 0}, "to": {"q": 1, "r": 0}}
    return {"schema": "preceptoros.decor-move/1", "seed": 7,
            "moves": [move], "frames": [frame]}


class NorteDecorTests(unittest.TestCase):
    def build(self, movement=None):
        return movement_record(movement or supplied_movement(), round_number=1,
                               web_commit="a" * 40, source="synthetic movement",
                               observed_at="fixture", attempted_at="fixture")

    def test_b3_b4_bytes_are_repeatable_and_hashes_match_payloads(self):
        first = self.build()
        second = self.build(copy.deepcopy(supplied_movement()))
        self.assertEqual(first["b3_bytes"], second["b3_bytes"])
        self.assertEqual(first["b4_bytes"], second["b4_bytes"])
        self.assertLess(len(first["b3_bytes"]), 16_384)
        self.assertEqual(first["record"]["summary"]["date"]["state"], "NO_DATA")
        self.assertEqual(first["record"]["summary"]["device"]["state"], "NO_DATA")

    def test_tick_result_and_identity_remain_caused_gaps(self):
        record = self.build()["record"]
        self.assertEqual(record["round"]["tick"]["state"], "NO_DATA")
        self.assertEqual(record["round"]["tick"]["cause"], "DE-1 relocation has no simulation tick")
        self.assertEqual(record["summary"]["result"]["state"], "NO_DATA")
        self.assertEqual(record["summary"]["device"]["state"], "NO_DATA")

    def test_wrong_movement_shape_and_multiple_frames_are_rejected(self):
        movement = supplied_movement()
        movement["extra"] = True
        with self.assertRaisesRegex(ValueError, "closed DE-1"):
            self.build(movement)
        movement = supplied_movement()
        movement["frames"].append(copy.deepcopy(movement["frames"][0]))
        movement["moves"].append(copy.deepcopy(movement["moves"][0]))
        with self.assertRaisesRegex(ValueError, "exactly one"):
            self.build(movement)

    def test_source_time_is_required_and_never_generated(self):
        with self.assertRaisesRegex(ValueError, "source: required"):
            movement_record(supplied_movement(), round_number=1, web_commit="a" * 40,
                            source="", attempted_at="fixture")

    def test_scrub_and_bubble_limits_remain_enforced_by_b3(self):
        movement = supplied_movement()
        movement["frames"][0]["hostname"] = "private"
        with self.assertRaises(RecordError):
            self.build(movement)
        movement = supplied_movement()
        movement["frames"][0]["atoms"][0]["r"] = "x" * 250
        with self.assertRaises(RecordError):
            self.build(movement)


if __name__ == "__main__":
    unittest.main()
