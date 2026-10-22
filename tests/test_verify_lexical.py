import unittest

from bin.verify_lexical import SCHEMA_ID, validate_envelope


SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "properties": {
        "v": {"const": SCHEMA_ID},
        "bytes": {"maximum": 1023},
        "p": {"required": ["id", "t", "sound", "motion", "n", "a"]},
    },
}


class VerifyLexicalTests(unittest.TestCase):
    def test_live_payload_and_utf8_byte_count(self):
        payload = {"id": "radio", "t": "Radio", "sound": "soft", "motion": "steady",
                   "n": 0, "a": []}
        import json
        size = len(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":")).encode())
        self.assertEqual(validate_envelope({"v": SCHEMA_ID, "st": "LIVE",
                                            "bytes": size, "p": payload}, SCHEMA), size)

    def test_no_data_requires_cause_and_omits_payload(self):
        good = {"v": SCHEMA_ID, "st": "NO_DATA", "bytes": 0, "causa": "no frame"}
        self.assertEqual(validate_envelope(good, SCHEMA), 0)
        for bad in ({"v": SCHEMA_ID, "st": "NO_DATA", "bytes": 0},
                    dict(good, p={"id": "invented"})):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_envelope(bad, SCHEMA)

    def test_sabotage_size_boundary_is_rejected(self):
        value = {"v": SCHEMA_ID, "st": "LIVE", "bytes": 1024,
                 "p": {"id": "x", "t": "x", "sound": "x", "motion": "x", "n": 0, "a": []}}
        with self.assertRaises(ValueError):
            validate_envelope(value, SCHEMA)

    def test_bad_payload_count_and_unknown_status_are_rejected(self):
        value = {"v": SCHEMA_ID, "st": "LIVE", "bytes": 1,
                 "p": {"id": "x", "t": "x", "sound": "x", "motion": "x", "n": 0, "a": []}}
        with self.assertRaisesRegex(ValueError, "byte count"):
            validate_envelope(value, SCHEMA)
        with self.assertRaisesRegex(ValueError, "unsupported"):
            validate_envelope(dict(value, st="SIMULATED"), SCHEMA)


if __name__ == "__main__":
    unittest.main()
