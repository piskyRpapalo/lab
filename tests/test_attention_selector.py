import json
import tempfile
import unittest
from pathlib import Path

from attention_selector.core import Chunk, SelectionPolicy, select_chunks
from attention_selector.store import ChunkStore, ingest_files
from attention_selector.package import build_two_pass_package
from attention_selector.evaluation import ndcg_at_k


class SelectorContract(unittest.TestCase):
    def test_priority_is_deterministic_and_exclusions_are_hard(self):
        chunks = [
            Chunk("a", "alpha beta", "src-a", 0, 10),
            Chunk("b", "alpha", "src-b", 0, 5),
            Chunk("c", "alpha beta", "src-c", 0, 10, excluded=True),
        ]
        policy = SelectionPolicy(max_chunks=2, max_chunk_bytes=64)
        first = select_chunks("alpha beta", chunks, policy)
        second = select_chunks("alpha beta", chunks, policy)
        self.assertEqual(first, second)
        self.assertEqual([item.chunk.chunk_id for item in first.selected], ["a", "b"])
        self.assertIn("excluded", first.exclusions[0].cause)

    def test_store_is_verbatim_deduplicated_and_append_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            source = root / "note.txt"
            source.write_text("line one\ná line two\n", encoding="utf-8")
            store = ChunkStore(Path(tmp) / "private-store")
            first = ingest_files(root, store, max_chunk_bytes=64, captured_at="2026-10-17")
            again = ingest_files(root, store, max_chunk_bytes=64, captured_at="2026-10-17")
            later = ingest_files(root, store, max_chunk_bytes=64, captured_at="2026-10-18")
            self.assertGreater(len(first.appended), 0)
            self.assertEqual(again.appended, ())
            self.assertEqual(again.duplicates, len(first.appended))
            self.assertEqual(later.duplicates, len(first.appended))
            for record in store.read_all():
                self.assertEqual(record.sha256, __import__("hashlib").sha256(record.text.encode()).hexdigest())
            self.assertTrue(all((Path(tmp) / "private-store").glob("*.json")))

    def test_store_rejects_tampered_verbatim_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            (root / "note.txt").write_text("verbatim", encoding="utf-8")
            store = ChunkStore(Path(tmp) / "private-store")
            ingest_files(root, store, max_chunk_bytes=64, captured_at="2026-10-17")
            path = next((Path(tmp) / "private-store").glob("*.json"))
            record = json.loads(path.read_text(encoding="utf-8"))
            record["text"] = "altered"
            path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                store.read_all()

    def test_store_rejects_unmeasured_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            (root / "note.txt").write_text("verbatim", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ISO date"):
                ingest_files(root, ChunkStore(Path(tmp) / "private-store"),
                             max_chunk_bytes=64, captured_at="today")

    def test_store_refuses_source_and_store_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            store = ChunkStore(root / "store")
            with self.assertRaisesRegex(ValueError, "separate trees"):
                ingest_files(root, store, max_chunk_bytes=64, captured_at="2026-10-17")

    def test_store_excludes_symlinked_source_with_cause(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            outside = Path(tmp) / "outside.txt"
            outside.write_text("must not be read", encoding="utf-8")
            (root / "linked.txt").symlink_to(outside)
            store = ChunkStore(Path(tmp) / "private-store")
            result = ingest_files(root, store, max_chunk_bytes=64, captured_at="2026-10-17")
            self.assertEqual(result.appended, ())
            self.assertEqual(result.rejected[0][1], "symlink source excluded")
            self.assertEqual(store.read_all(), ())

    def test_store_splits_multibyte_text_without_changing_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            root.mkdir()
            text = "aé水z"
            (root / "note.txt").write_text(text, encoding="utf-8")
            store = ChunkStore(Path(tmp) / "private-store")
            ingest_files(root, store, max_chunk_bytes=3, captured_at="2026-10-17")
            rows = sorted(store.read_all(), key=lambda row: row.start_byte)
            self.assertEqual("".join(row.text for row in rows), text)
            self.assertTrue(all(len(row.text.encode("utf-8")) <= 3 for row in rows))

    def test_two_pass_package_is_stable_and_has_verbatim_hashes(self):
        chunks = [Chunk("abc", "exact text", "source", 0, 10)]
        policy = SelectionPolicy(max_chunks=1, max_chunk_bytes=64)
        package = build_two_pass_package("exact", chunks, policy, index_budget_bytes=1024, chunk_budget_bytes=1024)
        repeated = build_two_pass_package("exact", chunks, policy, index_budget_bytes=1024, chunk_budget_bytes=1024)
        self.assertEqual(package, repeated)
        self.assertEqual(package.pass2[0].sha256, __import__("hashlib").sha256(b"exact text").hexdigest())
        self.assertEqual(package.pass2[0].seal, "VERBATIM")
        self.assertLessEqual(len(package.pass1_bytes), 1024)
        self.assertLessEqual(len(package.pass2_bytes), 1024)
        import json
        first = json.loads(package.pass1_bytes.split(b"|", 2)[2])
        second = json.loads(package.pass2_bytes.split(b"|", 2)[2])
        self.assertEqual([row["chunk_id"] for row in first["items"] if row["seal"] == "VERBATIM"],
                         [row["chunk_id"] for row in second["items"]])
        self.assertEqual(first["query_sha256"], second["query_sha256"])
        self.assertEqual(first["ceilings"], second["ceilings"])
        self.assertEqual(first["ceilings"]["index_bytes"], 1024)

    def test_package_budget_is_a_hard_ceiling(self):
        chunks = [Chunk("abc", "exact text", "source", 0, 10)]
        policy = SelectionPolicy(max_chunks=1, max_chunk_bytes=64)
        result = build_two_pass_package("exact", chunks, policy, index_budget_bytes=8, chunk_budget_bytes=8)
        self.assertEqual(result.status, "NO_DATA")
        self.assertEqual(result.pass1_bytes, b"")
        self.assertEqual(result.pass2_bytes, b"")
        self.assertIn("budget", result.cause)

    def test_chunk_omitted_from_second_pass_has_no_data_cause(self):
        chunk = Chunk("a", "alpha", "src", 0, 5)
        result = build_two_pass_package("alpha", [chunk], SelectionPolicy(1, 32, 32),
                                        index_budget_bytes=1024, chunk_budget_bytes=32)
        self.assertEqual(result.status, "NO_DATA")
        self.assertTrue(result.pass1)
        self.assertEqual(result.pass1[0]["seal"], "NO_DATA")
        self.assertIn("pass-two byte ceiling", result.pass1[0]["cause"])

    def test_index_overflow_reports_unlisted_count_and_cause(self):
        import json
        chunks = [Chunk(str(index), "alpha " + ("x" * 24), "source", 0, 30) for index in range(8)]
        result = build_two_pass_package("alpha", chunks, SelectionPolicy(8, 64, 512),
                                        index_budget_bytes=900, chunk_budget_bytes=4096)
        index = json.loads(result.pass1_bytes.split(b"|", 2)[2])
        self.assertLessEqual(len(result.pass1_bytes), 900)
        self.assertGreater(index["unlisted_count"], 0)
        self.assertEqual(index["unlisted_cause"], "index byte ceiling")

    def test_source_policy_exclusion_uses_sha256_identifier(self):
        import hashlib
        source_id = hashlib.sha256(b"source").hexdigest()
        policy = SelectionPolicy(max_chunks=1, max_chunk_bytes=64, exclude_source_ids=(source_id,))
        result = select_chunks("alpha", [Chunk("a", "alpha", source_id, 0, 5)], policy)
        self.assertEqual(result.status, "NO_DATA")
        self.assertIn("excluded by source policy", result.exclusions[0].cause)

    def test_ndcg_requires_labeled_gold_and_is_exact(self):
        self.assertEqual(ndcg_at_k(["a", "b"], {}), {"status": "NO_DATA", "cause": "gold labels are absent"})
        result = ndcg_at_k(["a", "b"], {"a": 3, "b": 2})
        self.assertEqual(result["status"], "MEASURED")
        self.assertEqual(result["ndcg_milli"], 1000)
        self.assertEqual(ndcg_at_k(["a"], ["invalid"])["status"], "NO_DATA")

    def test_local_explainer_refuses_non_loopback_hosts(self):
        from attention_selector.local_model import LocalModelCaller
        with self.assertRaises(ValueError):
            LocalModelCaller("example.invalid", 11434, "model")
        with self.assertRaises(ValueError):
            LocalModelCaller("localhost", 11434, "model")

    def test_local_explainer_uses_only_loopback_and_fixed_sampling(self):
        from unittest.mock import patch
        from attention_selector.local_model import LocalModelCaller

        calls = []

        class Response:
            def __init__(self, data):
                self.data = data

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(self.data).encode()

        with tempfile.TemporaryDirectory() as tmp:
            blob = Path(tmp) / "installed-model.gguf"
            blob.write_bytes(b"synthetic model marker")

            def fake_urlopen(request, timeout):
                calls.append(request)
                if request.full_url.endswith("/api/show"):
                    return Response({"details": {}, "modelfile": f"FROM {blob}"})
                return Response({"response": "measured explanation"})

            with patch("attention_selector.local_model.urllib.request.urlopen", fake_urlopen):
                answer = LocalModelCaller("127.0.0.1", 11434, "local-model", seed=17).explain("x=1", "matched")
        self.assertEqual(answer, "measured explanation")
        self.assertTrue(all(request.full_url.startswith("http://127.0.0.1:") for request in calls))
        generation = json.loads(calls[1].data)
        self.assertEqual(generation["options"], {"temperature": 0, "seed": 17})

    def test_local_explainer_does_not_call_unavailable_blob(self):
        from unittest.mock import patch
        from attention_selector.local_model import LocalModelCaller

        calls = []

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"details": {}, "modelfile": "FROM /absent/model.gguf"}).encode()

        def fake_urlopen(request, timeout):
            calls.append(request)
            return Response()

        with patch("attention_selector.local_model.urllib.request.urlopen", fake_urlopen):
            with self.assertRaisesRegex(RuntimeError, "no inference attempted"):
                LocalModelCaller("127.0.0.1", 11434, "local-model").explain("x=1", "matched")
        self.assertEqual(len(calls), 1)

    def test_hexagonal_adapters_are_injected_and_model_cannot_rank(self):
        from attention_selector.service import AttentionSelectorService

        class Reader:
            def read_chunks(self):
                return (Chunk("a", "alpha", "src", 0, 5),)

        class Writer:
            def __init__(self):
                self.rows = []

            def write(self, value):
                self.rows.append(value)

        class Caller:
            def explain(self, equation, cause):
                return "explanation only"

        writer = Writer()
        service = AttentionSelectorService(Reader(), writer, SelectionPolicy(1, 32, 32), Caller())
        before = service.rank("alpha")
        explanation = service.explain("score=1", "matched term")
        after = service.rank("alpha")
        self.assertEqual(before.selected, after.selected)
        self.assertEqual(writer.rows[0]["ranked"][0]["seal"], "VERBATIM")
        self.assertEqual(writer.rows[0]["ceilings"]["chunk_bytes_each"], 32)
        self.assertEqual(explanation, "explanation only")
        self.assertEqual(writer.rows[1]["semantic_quality"], "NO_DATA")
        self.assertFalse(writer.rows[1]["authority"])

    def test_cli_refuses_to_write_packages_into_repository(self):
        from attention_selector.cli import _write_private
        root = Path(__file__).resolve().parents[1]
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            _write_private(root / "should-not-be-created.json", b"private")


if __name__ == "__main__":
    unittest.main()
