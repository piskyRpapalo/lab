import copy
import json
import unittest

from benchmarks.norte_record import RecordError, SCHEMA, serialize, validate


def measured(value, source="synthetic fixture"):
    return {"state": "MEASURED", "value": value,
            "source": source, "observed_at": "fixture"}


def no_data(cause, source="synthetic fixture"):
    return {"state": "NO_DATA", "cause": cause,
            "source": source, "attempted_at": "fixture"}


def sample():
    frame = {"v": "preceptoros.bubble/1", "id": "DUEL", "t": 0,
             "atoms": [{"k": "wave", "r": "A wave crosses one live cell.", "i": []}],
             "bands": ["ocean"], "change": [], "sound": "NO_DATA",
             "soundCause": "fixture has no measured sound", "seal": "SIMULATED"}
    return {"schema": SCHEMA,
            "round": {"number": 1, "tick": measured(4),
                      "color": measured("ocean"),
                      "coordinates": measured([[0, 0], [1, 0]]),
                      "frame": frame},
            "summary": {"seed": measured("fixed-seed-1"),
                        "rules_version": measured("rules-fixture-1"),
                        "device": no_data("fleet identity is not present in the versioned census"),
                        "date": no_data("no benchmark run occurred"),
                        "result": no_data("no duel was executed"),
                        "seal": no_data("the duel seal contract is not available in this slice")}}


class NorteRecordTests(unittest.TestCase):
    def test_partial_fixture_preserves_causes_and_serializes_deterministically(self):
        record = sample()
        first = serialize(record)
        second = serialize(copy.deepcopy(record))
        self.assertEqual(first, second)
        self.assertLess(len(first), 16_384)
        self.assertEqual(json.loads(first)["summary"]["result"]["state"], "NO_DATA")

    def test_round_and_bubble_frame_both_refuse_1kib(self):
        record = sample()
        record["round"]["frame"]["atoms"][0]["r"] = "x" * 1100
        with self.assertRaisesRegex(RecordError, "phrase"):
            validate(record)
        record = sample()
        record["round"]["frame"]["atoms"][0]["r"] = "x" * 230
        record["round"]["frame"]["atoms"][0]["i"] = [{"o": "blob", "x": "x" * 900}]
        with self.assertRaisesRegex(RecordError, "ceiling"):
            validate(record)

    def test_every_missing_value_requires_a_cause(self):
        record = sample()
        del record["summary"]["result"]["cause"]
        with self.assertRaisesRegex(RecordError, "cause"):
            validate(record)

    def test_device_must_match_a_census_pseudonym(self):
        record = sample()
        record["summary"]["device"] = measured("private-node")
        with self.assertRaisesRegex(RecordError, "census"):
            validate(record, canonical_devices=())
        self.assertEqual(validate(record, canonical_devices=("private-node",)), record)

    def test_rejects_identity_prompts_and_walker_positions(self):
        for key in ("identity", "prompt", "walker"):
            with self.subTest(key=key):
                record = sample()
                record["summary"][key] = "forbidden"
                with self.assertRaisesRegex(RecordError, "field set|forbidden"):
                    validate(record)

    def test_refuses_unsealed_or_unphrased_bubble_frames(self):
        for key, value in (("seal", "#101010"), ("atoms", [{"k": "wave", "r": ""}])):
            with self.subTest(key=key):
                record = sample()
                record["round"]["frame"][key] = value
                with self.assertRaises(RecordError):
                    validate(record)


if __name__ == "__main__":
    unittest.main()
