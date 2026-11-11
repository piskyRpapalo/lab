"""Safeguard a synthetic model matrix: denominators, red protocols and no raw answers."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "bin/aggregate_synthetic_model_matrix.py"
REAL = ROOT / "benchmarks/receipts/20261111-mini-large-model-synthetic-matrix.json"
spec = importlib.util.spec_from_file_location("synthetic_matrix", SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def reports(endpoint="rack", model="synthetic:tiny", think=False):
    chunks = []
    for passno in (1, 2):
        for start, stop in mod.RANGES:
            cases = []
            for i in range(start, stop):
                gold = mod.LABELS[i // 6]
                cases.append({"id":"case_%02d" % i, "gold":gold,
                              "pred":gold, "correct":True,
                              "tokens":5,"eval_ns":100000000,"wall_s":0.2})
            obj = {
                "schema":mod.INPUT_SCHEMA, "scope":"SYNTHETIC_AUTHORED_GOLD_ONLY",
                "endpoint_role":endpoint, "model":model,
                "model_digest":"a"*64, "fixture_sha256":"b"*64,
                "pass":passno, "range":[start,stop],
                "per_case":cases, "attempted":6,
                "models_resident_after":0,
            }
            if think:obj["think"]=False
            chunks.append(obj)
    return chunks


def as_bytes(rows):
    return [json.dumps(x,sort_keys=True).encode() for x in rows]


class TestMatrixAggregator(unittest.TestCase):
    def test_valid_two_passes(self):
        out = mod.aggregate(as_bytes(reports()))
        self.assertEqual(out["unique_fixture_cases"], 24)
        self.assertEqual(out["total_measured_attempts"], 48)
        group = out["groups"][0]
        self.assertEqual([p["correct"] for p in group["two_passes"]], [24, 24])
        self.assertEqual(group["same_predictions_across_passes"], [24, 24])

    def test_no_duplicate_receipt(self):
        chunks=as_bytes(reports())
        with self.assertRaisesRegex(ValueError,"duplicate_receipt"):
            mod.aggregate(chunks+[chunks[0]])

    def test_two_independent_passes_required(self):
        with self.assertRaisesRegex(ValueError,"two_passes"):
            mod.aggregate(as_bytes(reports()[:4]))

    def test_all_four_batches_required(self):
        rows=reports()
        del rows[0]
        with self.assertRaisesRegex(ValueError,"four"):
            mod.aggregate(as_bytes(rows))

    def test_valid_per_class_denominator(self):
        out=mod.aggregate(as_bytes(reports()))["groups"][0]["two_passes"][0]
        self.assertEqual([out["by_gold_class"][x]["n"] for x in mod.LABELS], [6]*4)

    def test_wrong_gold_rejected(self):
        rows=reports()
        rows[0]["per_case"][0]["gold"]="UNKNOWN"
        with self.assertRaisesRegex(ValueError,"unknown_label"):
            mod.aggregate(as_bytes(rows))

    def test_fake_correct_flag_rejected(self):
        rows=reports()
        rows[0]["per_case"][0]["correct"]=False
        with self.assertRaisesRegex(ValueError,"correct_counter"):
            mod.aggregate(as_bytes(rows))

    def test_no_raw_model_answer_admitted(self):
        rows=reports()
        rows[0]["per_case"][0]["raw_answer"]="private text"
        with self.assertRaisesRegex(ValueError,"raw_text"):
            mod.aggregate(as_bytes(rows))

    def test_resident_model_blocks_receipt(self):
        rows=reports()
        rows[0]["models_resident_after"]=1
        with self.assertRaisesRegex(ValueError,"loaded_model_after"):
            mod.aggregate(as_bytes(rows))

    def test_fixture_drift_blocks_receipt(self):
        rows=reports()
        rows[2]["fixture_sha256"]="c"*64
        with self.assertRaisesRegex(ValueError,"fixture_hash_drift"):
            mod.aggregate(as_bytes(rows))

    def test_same_endpoint_different_case_ids_blocks(self):
        rows=reports()
        rows[4]["per_case"][0]["id"]="different"
        with self.assertRaisesRegex(ValueError,"case_ids"):
            mod.aggregate(as_bytes(rows))

    def test_model_digest_drift_blocks(self):
        rows=reports()
        rows[4]["model_digest"]="c"*64
        with self.assertRaisesRegex(ValueError,"digest_drift"):
            mod.aggregate(as_bytes(rows))

    def test_nodata_not_promoted_to_agreement(self):
        rows=reports()
        for row in rows:
            for x in row["per_case"]:
                x["pred"]="MALFORMED"
                x["correct"]=False
        out=mod.aggregate(as_bytes(rows))
        self.assertEqual(out["groups"][0]["verdict"],"RED_PROTOCOL")
        self.assertEqual([p["invalid"] for p in out["groups"][0]["two_passes"]],[24,24])

    def test_cross_endpoint_only_same_model_digest(self):
        rows=reports("rack","qwen3:1.7b",True)+reports("station","qwen3:1.7b",True)
        out=mod.aggregate(as_bytes(rows))
        self.assertEqual(out["matched_endpoint_comparison"]["same_predicted_labels"],[24,24])

    def test_cross_endpoint_mismatch_counts(self):
        rows=reports("rack","qwen3:1.7b",True)+reports("station","qwen3:1.7b",True)
        for i in range(8,16):
            if rows[i]["range"]==[0,6]:
                rows[i]["per_case"][0]["pred"]="MANIPULATION"
                rows[i]["per_case"][0]["correct"]=False
        out=mod.aggregate(as_bytes(rows))
        self.assertEqual(out["matched_endpoint_comparison"]["same_predicted_labels"],[23,24])

    def test_real_scoped_receipt(self):
        record=json.loads(REAL.read_text(encoding="utf-8"))
        self.assertEqual(record["total_measured_attempts"],288)
        self.assertEqual(len(record["groups"]),6)
        self.assertEqual(record["unique_fixture_cases"],24)
        self.assertEqual(record["matched_endpoint_comparison"]["same_predicted_labels"],[23,24])
        self.assertTrue(record["DFA_B1_DFA_B5_full_gate"].startswith("NO_DATA"))
        self.assertTrue(record["source_attestation"].startswith("NO_DATA"))
        self.assertTrue(record["jetson"].startswith("NO_DATA"))

    def test_real_red_protocol_survives(self):
        record=json.loads(REAL.read_text(encoding="utf-8"))
        red=[g for g in record["groups"] if g["verdict"]=="RED_PROTOCOL"]
        self.assertEqual(len(red),1)
        self.assertEqual([p["invalid"] for p in red[0]["two_passes"]],[24,24])
        self.assertTrue(all(g["verdict"]!="GREEN" for g in record["groups"]))

    def test_receipt_under_piece_budget_and_scrubbed(self):
        raw=REAL.read_bytes()
        self.assertLessEqual(len(raw),16384)
        for private_value in (b"/home/", b"127.0.0.1", b"100.101.", b"raw_prompt",
                              b"raw_answer", b"client_secret", b"private_key", b"email_address"):
            self.assertNotIn(private_value,raw)
        self.assertTrue(raw.endswith(b"\n"))


if __name__=="__main__":
    unittest.main()
