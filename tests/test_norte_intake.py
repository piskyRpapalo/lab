import copy
import hashlib
import unittest

from benchmarks.norte_intake import (
    RecordError, prepare_intake, serialize_intake, validate_intake,
)
from benchmarks.norte_record import SCHEMA as RECORD_SCHEMA, canonical_bytes


def measured(value):
    return {"state": "MEASURED", "value": value,
            "source": "synthetic fixture", "observed_at": "fixture"}


def no_data(cause):
    return {"state": "NO_DATA", "cause": cause,
            "source": "synthetic fixture", "attempted_at": "fixture"}


def record_fixture():
    frame = {"v": "preceptoros.bubble/1", "id": "DUEL", "t": 0,
             "atoms": [{"k": "wave", "r": "A wave crosses one live cell.", "i": []}],
             "bands": ["ocean"], "change": [], "sound": "NO_DATA",
             "soundCause": "fixture has no measured sound", "seal": "SIMULATED"}
    return {"schema": RECORD_SCHEMA,
            "round": {"number": 1, "tick": measured(4),
                      "color": measured("ocean"),
                      "coordinates": measured([[0, 0]]), "frame": frame},
            "summary": {"seed": measured("seed-1"),
                        "rules_version": measured("rules-1"),
                        "device": no_data("fleet identity is unavailable"),
                        "date": no_data("no benchmark was run"),
                        "result": no_data("no duel was executed"),
                        "seal": no_data("no upstream seal was supplied")}}


class NorteIntakeTests(unittest.TestCase):
    def test_preflight_and_serialization_are_stable(self):
        record = record_fixture()
        envelope = prepare_intake(record, "a" * 40)
        first = serialize_intake(envelope)
        second = serialize_intake(copy.deepcopy(envelope))
        self.assertEqual(first, second)
        self.assertEqual(validate_intake(envelope), envelope)

    def test_record_hash_detects_mutation(self):
        envelope = prepare_intake(record_fixture(), "a" * 40)
        envelope["record"]["summary"]["seed"]["value"] = "mutated"
        with self.assertRaisesRegex(RecordError, "record_sha256"):
            validate_intake(envelope)

    def test_frame_hash_detects_mutation(self):
        envelope = prepare_intake(record_fixture(), "a" * 40)
        envelope["record"]["round"]["frame"]["atoms"][0]["r"] = "changed phrase"
        envelope["provenance"]["record_sha256"] = hashlib.sha256(
            canonical_bytes(envelope["record"])).hexdigest()
        with self.assertRaisesRegex(RecordError, "frame_sha256"):
            validate_intake(envelope)

    def test_full_web_commit_hash_required(self):
        for value in ("short", "A" * 40, "z" * 40):
            with self.subTest(value=value):
                with self.assertRaisesRegex(RecordError, "commit hash"):
                    prepare_intake(record_fixture(), value)

    def test_missing_provenance_and_extra_fields_are_rejected(self):
        envelope = prepare_intake(record_fixture(), "b" * 40)
        del envelope["provenance"]["web_commit"]
        with self.assertRaisesRegex(RecordError, "required"):
            validate_intake(envelope)
        envelope = prepare_intake(record_fixture(), "b" * 40)
        envelope["user"] = "forbidden"
        with self.assertRaisesRegex(RecordError, "field set"):
            validate_intake(envelope)

    def test_measured_device_requires_explicit_census_allowlist(self):
        record = record_fixture()
        record["summary"]["device"] = measured("canonical-alias")
        with self.assertRaisesRegex(RecordError, "census"):
            prepare_intake(record, "c" * 40)
        envelope = prepare_intake(record, "c" * 40, ("canonical-alias",))
        self.assertEqual(envelope["record"]["summary"]["device"]["value"], "canonical-alias")


if __name__ == "__main__":
    unittest.main()
