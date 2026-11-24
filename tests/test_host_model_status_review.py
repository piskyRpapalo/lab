"""HOST must reject model authority despite syntactically valid JSON."""
import copy
from dataclasses import replace
import json
import unittest

from meta_harness.delegation import encode, sha
from meta_harness.host_model_status_review import (
    HostExpectation, MODEL_LIMIT_BYTES, review, views, verify_views,
)

def expected(**overrides):
    default = HostExpectation(
        source_ref=sha("host-source-private-only"), model_ref=sha("Qwen2.5-0.5B"),
        status="NO_DATA", cause="missing_source", answer="",
        observed_epoch=11, permission_epoch=7,
    )
    return replace(default, **overrides)


def output(status="NO_DATA", cause="missing_source", answer=""):
    return json.dumps({"status": status, "cause": cause, "answer": answer},
                      sort_keys=True, separators=(",", ":"))


class HostModelStatusReviewTests(unittest.TestCase):
    def test_missing_witness_fails_without_a_live_claim(self):
        r = review(expected(), output())
        self.assertEqual((r["verdict"], r["cause"], r["expected_state"]),
                         ("NO_DATA", "host_verifier_missing", "NO_DATA"))
        self.assertFalse(r["execution_authorized"])

    def test_negative_witness_rejects_forged_live(self):
        exp = expected(status="LIVE", cause="source_witnessed")
        r = review(exp, output("LIVE", "source_witnessed"), verify_host=lambda _: False)
        self.assertEqual(r["cause"], "host_evidence_not_witnessed")
        self.assertEqual(r["expected_state"], "NO_DATA")

    def test_host_match_is_not_execution_or_promotion(self):
        r = review(expected(), output(), verify_host=lambda _: True)
        self.assertEqual(r["verdict"], "EXACT")
        self.assertEqual(r["cause"], "matches_host_expectation_not_authority")
        self.assertEqual(r["source_authority"], "NONE")
        self.assertFalse(r["execution_authorized"])
        self.assertFalse(r["promotion_authorized"])
        self.assertFalse(r["training_authorized"])
        self.assertLess(len(encode(r)), 1024)

    def test_false_live_and_forged_cause_rejected(self):
        for raw in (output("LIVE", "missing_source"),
                    output("NO_DATA", "fake_signature"),
                    output("SIMULATED", "missing_source"),
                    output("NO_DATA", "missing_source", "unauthorized")):
            with self.subTest(raw=raw):
                r = review(expected(), raw, verify_host=lambda _: True)
                self.assertEqual((r["verdict"], r["cause"]),
                                 ("REJECTED", "model_semantic_mismatch"))
                self.assertFalse(r["execution_authorized"])

    def test_invalid_json_unsafe_fields_duplicates_and_overflow(self):
        samples = (
            "not json",
            '{"status":"NO_DATA","status":"LIVE","cause":"missing_source","answer":""}',
            '{"status":"NO_DATA","cause":"missing_source","answer":"","grant":true}',
            '{"status":null,"cause":"missing_source","answer":""}',
            '{"status":"NO_DATA","cause":"missing_source","answer":NaN}',
            '{"status":"NO_DATA","cause":"missing_source","answer":"' + "a" * (MODEL_LIMIT_BYTES+1) + '"}',
            "",
        )
        for raw in samples:
            with self.subTest(size=len(raw)):
                r = review(expected(), raw, verify_host=lambda _: True)
                self.assertEqual((r["verdict"], r["cause"]),
                                 ("REJECTED", "model_format_invalid"))
                self.assertNotIn("NaN", json.dumps(r))

    def test_host_rechecks_epoch_after_model_parse(self):
        n = {"calls": 0}
        def witness(snapshot):
            n["calls"] += 1
            return n["calls"] == 1
        r = review(expected(), output(), verify_host=witness)
        self.assertEqual(n["calls"], 2)
        self.assertEqual((r["verdict"], r["cause"]),
                         ("NO_DATA", "host_evidence_changed"))

    def test_witness_exceptions_scrub_private_source(self):
        def witness(_):
            raise RuntimeError("private path /home/owner/secrets")
        record = review(expected(), output(), verify_host=witness)
        self.assertEqual(record["cause"], "host_evidence_not_witnessed")
        self.assertNotIn("/home", json.dumps(record))

    def test_invalid_host_epoch_and_digest_fails(self):
        for exp in (expected(observed_epoch=True),
                    expected(permission_epoch=-1),
                    expected(source_ref="private-id"),
                    expected(cause="BAD_UPPER_CASE")):
            with self.subTest(exp=exp):
                r = review(exp, output(), verify_host=lambda _: True)
                self.assertEqual(r["cause"], "host_expectation_invalid")

    def test_acho_visual_speech_machine_share_ref_and_text(self):
        record = review(expected(), output(), verify_host=lambda _: True)
        packet = views(record)
        self.assertEqual(packet["text"], packet["speech"])
        self.assertEqual(packet["text"]["state_ref"], packet["machine"]["state_ref"])
        self.assertEqual(packet["text"]["summary"], packet["machine"]["summary"])
        self.assertTrue(verify_views(packet, expected(), output(), verify_host=lambda _: True))
        corrupt = copy.deepcopy(packet)
        corrupt["speech"]["summary"] = "LIVE approved"
        self.assertFalse(verify_views(corrupt, expected(), output(), verify_host=lambda _: True))

    def test_broken_self_digest_and_forged_grant_rejected(self):
        record = review(expected(), output(), verify_host=lambda _: True)
        for key,val in (("receipt_ref", sha("forged")), ("execution_authorized", True),
                        ("source_authority", "OWNER")):
            x = copy.deepcopy(record)
            x[key] = val
            with self.subTest(field=key), self.assertRaises(ValueError):
                views(x)

    def test_epoch_or_reference_change_changes_receipt(self):
        x = review(expected(), output(), verify_host=lambda _: True)
        for changed in (expected(observed_epoch=12),
                        expected(permission_epoch=8),
                        expected(model_ref=sha("different-base"))):
            y = review(changed, output(), verify_host=lambda _: True)
            self.assertNotEqual(x["receipt_ref"], y["receipt_ref"])

    def test_invalid_unhashable_host_state_fails_closed(self):
        malformed = expected(status=["LIVE"])
        r = review(malformed, output(), verify_host=lambda _: True)
        self.assertEqual((r["verdict"], r["cause"]),
                         ("NO_DATA", "host_expectation_invalid"))

    def test_invalid_unicode_and_oversize_model_fail_closed(self):
        for raw in ("\\ud800", "Z" * (MODEL_LIMIT_BYTES + 1)):
            r = review(expected(), raw, verify_host=lambda _: True)
            self.assertEqual((r["verdict"], r["cause"]),
                             ("REJECTED", "model_format_invalid"))

    def test_status_live_requires_host_witness_but_does_not_authorize(self):
        exp = expected(status="LIVE", cause="source_witnessed")
        x = review(exp, output("LIVE", "source_witnessed"), verify_host=lambda _: True)
        self.assertEqual(x["verdict"], "EXACT")
        self.assertFalse(x["execution_authorized"])
        self.assertEqual(x["source_authority"], "NONE")


    def test_physical_ab_readback_accounting(self):
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / (
            "benchmarks/big-models-20261123/train02-host-json-ab-dev-20261124.json"
        )
        d = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual((d["n_cases"], d["repetitions"], d["n_generations"]), (5, 2, 30))
        self.assertFalse(d["promotion_authorized"])
        for arm in ("base", "two_step", "four_step"):
            with self.subTest(arm=arm):
                self.assertEqual((d["control"][arm]["n"], d["control"][arm]["strict"]), (10, 4))
                e = d["experiment"][arm]
                self.assertEqual((e["n"], e["strict"], e["exact"], e["status_correct"]), (10, 10, 0, 0))
                self.assertEqual(e["false_live"], 0)
        self.assertLess(d["gpu_peak"]["gpu_vram_bytes"], 12_000_000_000)
        self.assertLess(d["gpu_peak"]["gpu_temp_c"], 65)

    def test_ab_public_record_scrub_and_no_gold_claim(self):
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / (
            "benchmarks/big-models-20261123/train02-host-json-ab-dev-20261124.json"
        )
        raw = path.read_text(encoding="utf-8")
        d = json.loads(raw)
        for fragment in ("/home/", "100.81.", "100.125.", "BEGIN PRIVATE",
                         "private_model_reply", "source_excerpt", '"raw":'):
            self.assertNotIn(fragment, raw)
        self.assertLess(len(raw.encode("utf-8")), 9000)
        self.assertFalse(d["promotion_authorized"])
        self.assertIn("NO_DATA(external_blind_gold)", d["caveats"])
        self.assertIn("NO_DATA(edge_e2e_audio)", d["caveats"])
        self.assertEqual(len(d["private_raw_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
