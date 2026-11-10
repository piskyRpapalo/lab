#!/usr/bin/env python3
"""F-11 offline provenance split admission for LoRA evaluation; not a model benchmark."""
import argparse
import json
import re
HEX=re.compile(r"^[0-9a-f]{64}$")
def admit(d):
    if not isinstance(d,dict) or set(d)!={"samples"} or not isinstance(d["samples"],list):raise ValueError("closed_samples_required")
    samples=set(); origins={"train":set(),"eval":set()};counts={"train":0,"eval":0,"same":0,"cross":0}
    for x in d["samples"]:
        if not isinstance(x,dict) or set(x)!={"sample_sha256","origin_sha256","split","class"}:raise ValueError("closed_sample_required")
        for k in ("sample_sha256","origin_sha256"):
            if not isinstance(x[k],str) or not HEX.fullmatch(x[k]):raise ValueError("sha256_hex_required")
        if x["sample_sha256"] in samples:raise ValueError("duplicate_sample_sha")
        samples.add(x["sample_sha256"])
        if x["split"] not in ("train","eval") or x["class"] not in ("same","cross"):raise ValueError("split_or_class_invalid")
        origins[x["split"]].add(x["origin_sha256"])
        counts[x["split"]]+=1
        if x["split"]=="eval":counts[x["class"]]+=1
    overlap=origins["train"] & origins["eval"]
    if overlap:raise ValueError("origin_leakage_across_splits")
    sufficient=counts["same"]>=6 and counts["cross"]>=6
    return {"schema":"preceptoros.lab.f11-origin-admission/1",
            "state":"READY_FOR_EVAL_FIXTURE_ONLY" if sufficient else "NO_DATA",
            "cause":"NO_DATA: model_judgments_and_runtime_not_run" if sufficient else "NO_DATA: eval_requires_six_per_class",
            "train_samples":counts["train"],"eval_samples":counts["eval"],
            "eval_same":counts["same"],"eval_cross":counts["cross"],
            "train_origins":len(origins["train"]),"eval_origins":len(origins["eval"]),
            "origin_overlap":0,
            "verification":"NO_DATA: sample_and_origin_digest_preimages_not_verified"}

if __name__=="__main__":
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("samples_json");a=p.parse_args()
 try:
  with open(a.samples_json,encoding="utf-8") as f:out=admit(json.load(f))
 except (ValueError,OSError) as e:p.exit(2,"NO_DATA: invalid_input ("+type(e).__name__+")\n")
 print(json.dumps(out,sort_keys=True,separators=(",",":")))
