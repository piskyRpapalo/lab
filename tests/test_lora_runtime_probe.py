"""Synthetic read-only LoRA runtime witness tests; never load a model or use network."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from meta_harness import lora_runtime_probe as p


def raw(value):
    return json.dumps(value, separators=(",", ":"), allow_nan=False).encode()


class _Fixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.base = root / "base.gguf"
        self.adapter = root / "adapter.gguf"
        self.base.write_bytes(b"GGUF_BASE_PINNED_FOR_SYNTHETIC_TEST")
        self.adapter.write_bytes(b"GGUF_ADAPTER_PINNED_FOR_SYNTHETIC_TEST")
        self.base_sha = hashlib.sha256(self.base.read_bytes()).hexdigest()
        self.adapter_sha = hashlib.sha256(self.adapter.read_bytes()).hexdigest()
        self.props = {"model_path": str(self.base), "total_slots": 1}
        self.head = [{"id": 0, "path": str(self.adapter), "scale": 0.0}]
        self.options = dict(endpoint="http://127.0.0.1:19191", node="rack",
                            base_path=str(self.base), base_sha256=self.base_sha,
                            adapter_path=str(self.adapter), adapter_sha256=self.adapter_sha,
                            now=datetime(2026, 11, 18, 17, 0, tzinfo=timezone.utc))

    def fetch(self, *, props=None, heads=None, sequence=None):
        if sequence is None:
            sequence = [raw(self.props if props is None else props),
                        raw(self.head if heads is None else heads)] * 2
        replies = iter(sequence)
        paths = []
        def get(route):
            paths.append(route)
            return next(replies)
        return get, paths

    def run_probe(self, *, props=None, heads=None, sequence=None, **kwargs):
        fetch, paths = self.fetch(props=props, heads=heads, sequence=sequence)
        row = p.snapshot(fetch=fetch, **dict(self.options, **kwargs))
        return row, paths


class WitnessTests(_Fixture, unittest.TestCase):
    def test_snapshot_is_evidence_only_no_grants(self):
        row, paths = self.run_probe()
        self.assertEqual(paths, ["/props", "/lora-adapters"] * 2)
        self.assertEqual(row["state"], "SNAPSHOT_OBSERVED")
        self.assertEqual(row["cause"], "PATHS_AND_FILES_ONLY_NOT_INFERENCE")
        self.assertEqual(row["base_ref"], self.base_sha)
        self.assertEqual(row["adapter_ref"], self.adapter_sha)
        self.assertEqual(row["adapter_id"], 0)
        self.assertEqual(row["scale"], 0.0)
        self.assertFalse(row["dispatch_authorized"])
        self.assertFalse(row["cache_reuse_authorized"])
        self.assertEqual(row["promotion"], "NOT_AUTHORIZED")
        self.assertLess(len(raw(row)), 1024)
        self.assertEqual(row["receipt_ref"], p.sha({k: v for k, v in row.items() if k != "receipt_ref"}))
        self.assertNotIn(self.temp.name, raw(row).decode())

    def test_observed_active_scale_does_not_infer_inference(self):
        row, _ = self.run_probe(heads=[dict(self.head[0], scale=1.0)])
        self.assertEqual(row["state"], "SNAPSHOT_OBSERVED")
        self.assertEqual(row["scale"], 1.0)
        self.assertEqual(row["cause"], "PATHS_AND_FILES_ONLY_NOT_INFERENCE")
        self.assertFalse(row["cache_reuse_authorized"])

    def test_real_llama_server_extra_fields_never_become_authority(self):
        # b10488 returns these two strings even when no prompt is supplied.
        extra = dict(self.head[0], task_name="guide", prompt_prefix="UNTRUSTED")
        row, _ = self.run_probe(heads=[extra])
        self.assertEqual(row["state"], "SNAPSHOT_OBSERVED")
        self.assertNotIn("UNTRUSTED", raw(row).decode())
        invalid = dict(extra, prompt_prefix={"tool": "shell"})
        row, _ = self.run_probe(heads=[invalid])
        self.assertEqual(row["cause"], "RUNTIME_SCHEMA_INVALID")

    def test_explicit_no_remote_urls_including_injected_reader(self):
        for url in ("https://127.0.0.1:19191", "http://localhost:19191",
                    "http://127.0.0.1:19191/api", "http://0.0.0.0:19191",
                    "http://127.0.0.1:80", "http://127.0.0.1:99999",
                    "http://user:pass@127.0.0.1:19191", "http://[::1]:19191"):
            row, paths = self.run_probe(endpoint=url)
            self.assertEqual(row["cause"], "ENDPOINT_NOT_LOOPBACK", url)
            self.assertEqual(paths, [], url)

    def test_digest_mismatch_and_change_rejected(self):
        row, _ = self.run_probe(base_sha256="f" * 64)
        self.assertEqual(row["cause"], "ARTIFACT_DIGEST_MISMATCH")
        row, _ = self.run_probe(adapter_sha256="f" * 64)
        self.assertEqual(row["cause"], "ARTIFACT_DIGEST_MISMATCH")
        row, _ = self.run_probe(adapter_path=str(self.base))
        self.assertEqual(row["cause"], "BASE_ADAPTER_COLLISION")
        self.adapter.unlink()
        row, _ = self.run_probe()
        self.assertEqual(row["cause"], "ARTIFACT_UNAVAILABLE")

    def test_symlink_never_followed(self):
        link = Path(self.temp.name) / "linked.gguf"
        link.symlink_to(self.adapter)
        heads = [{"id": 0, "path": str(link), "scale": 0}]
        row, _ = self.run_probe(heads=heads, adapter_path=str(link))
        self.assertEqual(row["cause"], "ARTIFACT_UNAVAILABLE")

    def test_runtime_path_identity_must_match(self):
        row, _ = self.run_probe(props={"model_path": "/different/base.gguf"})
        self.assertEqual(row["cause"], "RUNTIME_BASE_PATH_UNVERIFIED")
        row, _ = self.run_probe(heads=[{"id": 0, "path": "/wrong/head.gguf", "scale": 1}])
        self.assertEqual(row["cause"], "RUNTIME_ADAPTER_NOT_LOADED")
        row, _ = self.run_probe(heads=[])
        self.assertEqual(row["cause"], "RUNTIME_ADAPTER_NOT_LOADED")

    def test_runtime_schema_and_duplicate_ids_fail_closed(self):
        for value in (
                {"id": 0}, [{"id": True, "path": str(self.adapter), "scale": 0}],
                [{"id": 0, "path": str(self.adapter), "scale": 0},
                 {"id": 0, "path": "/other", "scale": 0}],
                [{"id": 0, "path": str(self.adapter), "scale": "1"}],
                [{"id": 0, "path": str(self.adapter), "scale": 17}],
                [{"id": 0, "path": str(self.adapter), "scale": 0, "extra": 1}],
        ):
            row, _ = self.run_probe(heads=value)
            self.assertEqual(row["state"], "NO_DATA", str(value))
            self.assertEqual(row["cause"], "RUNTIME_SCHEMA_INVALID", str(value))

    def test_duplicate_adapter_entries_with_distinct_ids_blocked(self):
        value = [{"id": 0, "path": str(self.adapter), "scale": 0},
                 {"id": 1, "path": str(self.adapter), "scale": 0}]
        row, _ = self.run_probe(heads=value)
        self.assertEqual(row["cause"], "RUNTIME_DUPLICATE_ADAPTER")

    def test_readback_mutation_between_reads_fails(self):
        different = [{"id": 0, "path": str(self.adapter), "scale": 1.0}]
        sequence = [raw(self.props), raw(self.head), raw(self.props), raw(different)]
        row, paths = self.run_probe(sequence=sequence)
        self.assertEqual(row["cause"], "RUNTIME_SNAPSHOT_CHANGED")
        self.assertEqual(len(paths), 4)
        self.assertIsNone(row["snapshot_ref"])

    def test_prompt_prefix_change_invalidates_snapshot_scope(self):
        before = [dict(self.head[0], task_name="guide", prompt_prefix="A")]
        after = [dict(self.head[0], task_name="guide", prompt_prefix="B")]
        row, _ = self.run_probe(sequence=[raw(self.props), raw(before),
                                          raw(self.props), raw(after)])
        self.assertEqual(row["cause"], "RUNTIME_SNAPSHOT_CHANGED")

    def test_unknown_model_path_does_not_pass(self):
        row, _ = self.run_probe(props={"model_alias": "base.gguf"})
        self.assertEqual(row["cause"], "RUNTIME_BASE_PATH_UNVERIFIED")

    def test_closed_json_parser(self):
        for invalid, cause in ((b'{"a":1,"a":1}', "JSON_DUPLICATE_KEY"),
                               (b'{"x":NaN}', "NONFINITE_JSON"),
                               (b'not json', "RESPONSE_JSON_INVALID"),
                               (b"{}", "RUNTIME_BASE_PATH_UNVERIFIED")):
            row, _ = self.run_probe(sequence=[invalid, raw(self.head)] * 2)
            self.assertEqual(row["cause"], cause)
        row, _ = self.run_probe(sequence=[b" " * (p.MAX_RESPONSE + 1), raw(self.head)] * 2)
        self.assertEqual(row["cause"], "RESPONSE_SIZE_OR_TYPE")

    def test_no_secrets_on_reader_exception(self):
        def exception(_):
            raise RuntimeError("token=SECRET_HTTP_PASSWORD")
        row = p.snapshot(fetch=exception, **self.options)
        self.assertEqual(row["cause"], "HOST_OR_RUNTIME_ERROR")
        self.assertNotIn("SECRET", raw(row).decode())

    def test_bad_clock_and_role(self):
        row, _ = self.run_probe(now=datetime(2026, 11, 18))
        self.assertEqual(row["cause"], "CLOCK_INVALID")
        row, paths = self.run_probe(node="unapproved-node")
        self.assertEqual(row["cause"], "INPUT_INVALID")
        self.assertEqual(paths, [])
        row, paths = self.run_probe(node=[])
        self.assertEqual(row["cause"], "INPUT_INVALID")
        self.assertEqual(paths, [])

    def test_read_only_http_routes_and_redirects(self):
        self.assertEqual(p.local_endpoint("http://127.0.0.1:19191/"), "http://127.0.0.1:19191")
        with self.assertRaises(p.WitnessError):
            p.get_local("http://127.0.0.1:19191", "/completion")
        handler = p._NoRedirect()
        with self.assertRaises(p.WitnessError):
            handler.redirect_request(None, None, 302, "go", {}, "https://evil.example")

    def test_no_network_by_default_under_mock(self):
        fetch, _ = self.fetch()
        with patch.object(p.urllib.request, "build_opener", side_effect=AssertionError("NETWORK")):
            row = p.snapshot(fetch=fetch, **self.options)
        self.assertEqual(row["state"], "SNAPSHOT_OBSERVED")


class RequestBindingTests(_Fixture, unittest.TestCase):
    """Additional host-only guard tests; no model calls are performed."""
    def binding(self, *, witness=None, verify_witness=lambda *_: True, **changed):
        if witness is None:
            witness = self.run_probe()[0]
        values = dict(witness=witness, base_ref=self.base_sha, adapter_ref=self.adapter_sha,
                      session_ref="1" * 64, context_ref="2" * 64,
                      tool_scope_ref="3" * 64, permission_ref="4" * 64,
                      verify_witness=verify_witness, now=self.options["now"])
        return p.prepare_request_head(**dict(values, **changed))

    def test_exact_attested_head_is_prepared_but_never_authorized(self):
        row = self.binding()
        self.assertEqual(row["state"], "PREPARED_ONLY")
        self.assertEqual(row["lora"], [{"id": 0, "scale": 1.0}])
        self.assertEqual(row["cause"], "NOT_AN_EXECUTION_OR_CACHE_GRANT")
        self.assertFalse(row["dispatch_authorized"])
        self.assertFalse(row["cache_reuse_authorized"])
        self.assertEqual(row["promotion"], "NOT_AUTHORIZED")
        self.assertLess(len(raw(row)), 1024)
        self.assertEqual(row["receipt_ref"], p.sha({k:v for k,v in row.items() if k!="receipt_ref"}))

    def test_wrong_adapter_and_scope_rejected(self):
        self.assertEqual(self.binding(adapter_ref="f"*64)["cause"], "WITNESS_MODEL_OR_HEAD_MISMATCH")
        self.assertEqual(self.binding(base_ref="f"*64)["cause"], "WITNESS_MODEL_OR_HEAD_MISMATCH")
        self.assertEqual(self.binding(permission_ref="bad")["cause"], "SCOPE_OR_DIGEST_INVALID")

    def test_expired_or_future_witness_cannot_bind(self):
        from datetime import timedelta
        self.assertEqual(self.binding(now=self.options["now"]+timedelta(seconds=121))["cause"], "WITNESS_STALE_OR_FUTURE")
        self.assertEqual(self.binding(now=self.options["now"]-timedelta(seconds=1))["cause"], "WITNESS_STALE_OR_FUTURE")

    def test_no_host_witness_or_false_callback_rejected(self):
        self.assertEqual(self.binding(verify_witness=None)["cause"], "HOST_WITNESS_REQUIRED")
        self.assertEqual(self.binding(verify_witness=lambda *_: False)["cause"], "HOST_WITNESS_NOT_CURRENT")
        self.assertEqual(self.binding(verify_witness=lambda *_: 1)["cause"], "HOST_WITNESS_NOT_CURRENT")

    def test_forged_id_even_resealed_needs_independent_host_witness(self):
        witness = dict(self.run_probe()[0], adapter_id=999)
        self.assertEqual(self.binding(witness=witness)["cause"], "WITNESS_SEAL_INVALID")
        witness["receipt_ref"] = p.sha({k:v for k,v in witness.items() if k!="receipt_ref"})
        self.assertEqual(self.binding(witness=witness, verify_witness=lambda *_: False)["cause"],
                         "HOST_WITNESS_NOT_CURRENT")

    def test_corrupt_snapshot_and_callback_secret_scrubbed(self):
        witness = dict(self.run_probe()[0], snapshot_ref="not_sha")
        witness["receipt_ref"] = p.sha({k:v for k,v in witness.items() if k!="receipt_ref"})
        self.assertEqual(self.binding(witness=witness)["cause"], "WITNESS_SNAPSHOT_INVALID")
        def broken(*_):
            raise RuntimeError("password=private")
        row = self.binding(verify_witness=broken)
        self.assertEqual(row["cause"], "HOST_OR_WITNESS_ERROR")
        self.assertNotIn("private", raw(row).decode())


if __name__ == "__main__":
    unittest.main()
