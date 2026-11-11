#!/usr/bin/env python3
"""Aggregate private synthetic model runs into a SCRUBBED, scope-honest LAB receipt.

Reads local *case IDs and predicted labels* to verify denominators but never emits
per-case IDs, raw prompts, model answers, file paths or host addresses.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import statistics

SCHEMA = "preceptoros.lab.synthetic-model-matrix/1"
INPUT_SCHEMA = "preceptoros.lab.synthetic-model-judgement/1"
LABELS = ("SAFE", "MANIPULATION", "DARK_PATTERN", "FALSE_NO_DATA")
PREDICTIONS = set(LABELS) | {"MALFORMED", "ERROR", "NO_DATA"}
RANGES = ((0, 6), (6, 12), (12, 18), (18, 24))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def checked_input(raw):
    doc = json.loads(raw)
    if not isinstance(doc, dict) or doc.get("schema") != INPUT_SCHEMA:
        raise ValueError("input_schema_invalid")
    if doc.get("scope") != "SYNTHETIC_AUTHORED_GOLD_ONLY":
        raise ValueError("input_scope_invalid")
    if doc.get("endpoint_role") not in ("rack", "station"):
        raise ValueError("unknown_endpoint_role")
    if doc.get("pass") not in (1, 2):
        raise ValueError("invalid_pass")
    if not isinstance(doc.get("range"), list) or tuple(doc["range"]) not in RANGES:
        raise ValueError("invalid_batch_range")
    if not isinstance(doc.get("per_case"), list) or len(doc["per_case"]) != 6:
        raise ValueError("batch_length_not_six")
    if len(set(x.get("id") for x in doc["per_case"])) != 6:
        raise ValueError("duplicate_case_ids")
    if doc.get("attempted") != 6:
        raise ValueError("case_count_mismatch")
    if doc.get("models_resident_after") != 0:
        raise ValueError("loaded_model_after_run")
    if doc.get("fixture_sha256") is None or len(doc["fixture_sha256"]) != 64:
        raise ValueError("fixture_hash_invalid")
    if doc.get("model_digest") is None or len(doc["model_digest"]) != 64:
        raise ValueError("model_digest_invalid")
    for row in doc["per_case"]:
        if row.get("gold") not in LABELS or row.get("pred") not in PREDICTIONS:
            raise ValueError("unknown_label")
        if type(row.get("correct")) is not bool or row["correct"] != (row["gold"] == row["pred"]):
            raise ValueError("invalid_correct_counter")
        if any(x in row for x in ("raw_prompt", "raw_answer", "response", "message_text")):
            raise ValueError("raw_text_field_forbidden")
    return doc


def aggregate(sources):
    if not sources:
        raise ValueError("no_source_receipts")
    groups = defaultdict(list)
    all_hashes = set()
    for raw in sources:
        sha = hashlib.sha256(raw).hexdigest()
        if sha in all_hashes:
            raise ValueError("duplicate_receipt_bytes")
        all_hashes.add(sha)
        d = checked_input(raw)
        cfg = "think_off" if d.get("think") is False else "default"
        groups[(d["endpoint_role"], d["model"], cfg)].append((sha, d))
    results = []
    internal = {}
    fixture_hashes = set()
    for (endpoint, model, cfg), rows in sorted(groups.items()):
        by_pass = defaultdict(list)
        for sha, d in rows:
            by_pass[d["pass"]].append((sha, d))
            fixture_hashes.add(d["fixture_sha256"])
        if set(by_pass) != {1, 2}:
            raise ValueError("two_passes_required")
        head_digests = set()
        pass_reports = []
        pass_predictions = {}
        for number in (1, 2):
            chunks = sorted(by_pass[number], key=lambda x: x[1]["range"][0])
            if [tuple(d["range"]) for _, d in chunks] != list(RANGES):
                raise ValueError("all_four_distinct_batches_required")
            head_digests |= {d["model_digest"] for _, d in chunks}
            case_rows = [r for _, d in chunks for r in d["per_case"]]
            if len(case_rows) != 24 or len(set(r["id"] for r in case_rows)) != 24:
                raise ValueError("not_24_unique_cases")
            gold = Counter(r["gold"] for r in case_rows)
            if set(gold) != set(LABELS) or any(gold[k] != 6 for k in LABELS):
                raise ValueError("class_balance_invalid")
            predictions = {r["id"]:(r["gold"],r["pred"]) for r in case_rows}
            pass_predictions[number] = predictions
            matrix = {k:dict(Counter(r["pred"] for r in case_rows if r["gold"] == k)) for k in LABELS}
            rates = [r["tokens"] * 1e9 / r["eval_ns"] for r in case_rows
                     if type(r.get("tokens")) is int and type(r.get("eval_ns")) is int and r["eval_ns"] > 0]
            pass_reports.append({
                "pass":number,
                "unique_cases":24,
                "correct":sum(r["correct"] for r in case_rows),
                "invalid":sum(r["pred"] in ("MALFORMED","ERROR","NO_DATA") for r in case_rows),
                "by_gold_class":{k:{"n":6, "correct":sum(r["correct"] and r["gold"] == k for r in case_rows)}
                                  for k in LABELS},
                "confusion_counts":matrix,
                "median_generation_tokens_per_second":round(statistics.median(rates),2) if rates else None,
                "total_request_wall_s":round(sum(r.get("wall_s",0) for r in case_rows),3),
                "receipt_sha256":[sha for sha,_ in chunks],
            })
        if len(head_digests) != 1:
            raise ValueError("model_digest_drift_within_group")
        if set(pass_predictions[1]) != set(pass_predictions[2]):
            raise ValueError("case_ids_differ_across_passes")
        if any(pass_predictions[1][id][0] != pass_predictions[2][id][0] for id in pass_predictions[1]):
            raise ValueError("gold_drift_across_passes")
        same=sum(pass_predictions[1][id][1] == pass_predictions[2][id][1] for id in pass_predictions[1])
        results.append({
            "endpoint_role":endpoint, "model":model, "protocol":cfg,
            "model_digest":next(iter(head_digests)),
            "two_passes":pass_reports, "same_predictions_across_passes":[same,24],
            "verdict":"RED_PROTOCOL" if all(p["invalid"]==24 for p in pass_reports)
                      else "SYNTHETIC_ONLY_NOT_CALIBRATED",
            "quality_gate":"NO_DATA: no_human_independent_gold",
        })
        internal[(endpoint,model,cfg)]=pass_predictions[1]
    if len(fixture_hashes)!=1:
        raise ValueError("fixture_hash_drift")
    paired=None
    a=internal.get(("rack","qwen3:1.7b","think_off"))
    b=internal.get(("station","qwen3:1.7b","think_off"))
    if a is not None and b is not None:
        if set(a)!=set(b) or any(a[i][0]!=b[i][0] for i in a):
            raise ValueError("cross_endpoint_gold_mismatch")
        d_a=next(r["model_digest"] for r in results if r["endpoint_role"]=="rack"
                 and r["model"]=="qwen3:1.7b" and r["protocol"]=="think_off")
        d_b=next(r["model_digest"] for r in results if r["endpoint_role"]=="station"
                 and r["model"]=="qwen3:1.7b" and r["protocol"]=="think_off")
        if d_a!=d_b:raise ValueError("cross_endpoint_model_digest_mismatch")
        paired={
          "model":"qwen3:1.7b","same_model_digest":d_a,
          "same_predicted_labels":[sum(a[i][1]==b[i][1] for i in a),24],
          "causality":"NO_DATA: execution_backend_difference_not_isolated",
        }
    return {
       "schema":SCHEMA,"date":"2026-11-11",
       "unique_fixture_cases":24,"source_fixture_sha256":next(iter(fixture_hashes)),
       "total_measured_attempts":sum(sum(p["unique_cases"] for p in g["two_passes"]) for g in results),
       "groups":results,"matched_endpoint_comparison":paired,
       "models_after_each_batch":"0_resident_according_to_ollama_ps",
       "ollama_api_version_at_followup":{"rack":"0.40.3","station_tunnel":"0.40.3"},
       "source_attestation":"NO_DATA: authored_synthetic_labels_not_independently_adjudicated",
       "replay_publicly":"NO_DATA: private_fixture_text_not_committed",
       "DFA_B1_DFA_B5_full_gate":"NO_DATA: real_ux_and_human_gold_not_tested",
       "station_binding":"NO_DATA: inference_tunnel_not_cryptographically_bound_to_ssh_identity",
       "jetson":"NO_DATA: configured_ssh_alias_connection_timeout",
       "phone":"NO_DATA: no_authorized_adb_device",
       "power":"NO_DATA: meter_not_validated",
       "model_family_blind_judge":"NO_DATA: no_separate_manipulator_and_holdout_gold",
       "gpt_oss_120b":"NO_DATA: model_artifact_larger_than_station_available_ram; not_loaded",
       "signature":"NO_DATA: human_signature_not_performed",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    inputs=sorted(a.input_dir.glob("run_*.json"))
    result=aggregate([f.read_bytes() for f in inputs])
    if a.output.exists():
        raise ValueError("refuse_overwrite_existing_receipt")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(json.dumps(result,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()+b"\n")
    print("GROUPS",len(result["groups"]),"ATTEMPTS",result["total_measured_attempts"],
          "RECEIPT_SHA256",hashlib.sha256(a.output.read_bytes()).hexdigest())

if __name__=="__main__":
    main()
