import json
import unittest

from meta_harness.local_inference_evidence import normalize, reader_fields

D = "a" * 64
REF = "b" * 64
MODEL = "fixture-model"
COMMON = dict(model=MODEL, pinned_digest=D, before_digest=D, after_digest=D,
              wall_ns=2000000000, observed_at="2026-11-26T23:55:00Z",
              evidence_ref=REF, origin="fixture")


def ollama():
    return dict(model=MODEL, done=True, response="synthetic test answer",
                eval_count=10, eval_duration=1000000000)


def llama():
    return dict(model=MODEL, stop=True, content="synthetic test answer",
                timings=dict(predicted_n=10, predicted_ms=1000))


class LocalInferenceEvidenceTests(unittest.TestCase):
    def run_case(self, engine="ollama", response=None, **overrides):
        args = dict(COMMON, **overrides)
        return normalize(engine, response if response is not None else ollama(), **args)

    def test_parity(self):
        a = self.run_case()
        b = self.run_case("llama.cpp", llama())
        self.assertEqual(a["metrics"], b["metrics"])
        self.assertEqual(a["response_sha256"], b["response_sha256"])
        self.assertEqual(a["metrics"]["generation_tokens_per_s"], 10)
        self.assertEqual(a["metrics"]["wall_ms"], 2000)

    def test_no_authority_or_live(self):
        for origin, expected in [("fixture", "SIMULATED"), ("observed", "REPORTED")]:
            r = self.run_case(origin=origin)
            self.assertEqual(r["state"], expected)
            self.assertFalse(r["execution_authorized"])
            self.assertFalse(r["completion_verified"])
            self.assertNotEqual(reader_fields(r)["seal"], "LIVE")
            self.assertNotIn("synthetic test answer", json.dumps(r))

    def test_digest_change(self):
        for key in ("before_digest", "after_digest", "pinned_digest"):
            self.assertEqual(self.run_case(**{key: REF})["state"], "NO_DATA")

    def test_missing_identity(self):
        self.assertEqual(self.run_case(response=dict(ollama(), model="different"))["state"], "NO_DATA")
        self.assertEqual(self.run_case(model="fixture:cloud")["state"], "NO_DATA")

    def test_incomplete(self):
        self.assertEqual(self.run_case(response=dict(ollama(), done=False))["state"], "NO_DATA")
        self.assertEqual(self.run_case("llama.cpp", dict(llama(), stop=False))["state"], "NO_DATA")

    def test_invalid_timing(self):
        for bad in (False, 0, -1, float("nan"), float("inf")):
            self.assertEqual(self.run_case(response=dict(ollama(), eval_duration=bad))["state"], "NO_DATA")
            self.assertEqual(self.run_case("llama.cpp", dict(llama(), timings={
                "predicted_n": 10, "predicted_ms": bad}))["state"], "NO_DATA")
        self.assertEqual(self.run_case(wall_ns=0)["state"], "NO_DATA")

    def test_memory_distinct(self):
        self.assertEqual(self.run_case()["metrics"]["memory_bytes"]["state"], "NO_DATA")
        self.assertEqual(self.run_case(memory_bytes=1024)["metrics"]["memory_bytes"], 1024)
        self.assertEqual(self.run_case(memory_bytes=True)["metrics"]["memory_bytes"]["state"], "NO_DATA")

    def test_observation_binding(self):
        for bad in (dict(observed_at="2026-11-26"), dict(evidence_ref="bad"), dict(origin="live")):
            self.assertEqual(self.run_case(**bad)["state"], "NO_DATA")

    def test_reject_remote_and_large(self):
        for extra in (dict(remote_host="remote"), dict(response="x"*65537)):
            self.assertEqual(self.run_case(response=dict(ollama(), **extra))["state"], "NO_DATA")

    def test_reader_unknown(self):
        self.assertEqual(reader_fields(self.run_case("other"))["seal"], "NO_DATA")
        self.assertEqual(reader_fields(None)["seal"], "NO_DATA")


if __name__ == "__main__":
    unittest.main()
