#!/usr/bin/env python3
"""F-01 offline weekly composition from F-08/F-09 aggregate observations.

No network, private event IDs, model calls, signatures or authority.
"""
import argparse
import hashlib
import json
import re

CAUSES = {"not_measured", "missing_receipt", "stale_measurement", "source_unavailable"}

def compose(d):
    if not isinstance(d,dict) or set(d)!={"week","f08","f09"}:raise ValueError("closed_week_input")
    if not isinstance(d["week"],str) or not re.fullmatch(r"[0-9]{4}-W(?:0[1-9]|[1-4][0-9]|5[0-3])",d["week"]):raise ValueError("week_format")
    results={}
    for key,required in [("f08",{"signed","pending","verification"}),("f09",{"green","red","unknown","verification"})]:
        row=d[key]
        if not isinstance(row,dict):raise ValueError("observation_required")
        if set(row)=={"cause"} and isinstance(row["cause"],str) and row["cause"] in CAUSES:
            results[key]={"state":"NO_DATA","cause":row["cause"]};continue
        if set(row)!=required:raise ValueError("closed_observation_fields")
        if any(type(row[k]) is not int or row[k]<0 for k in required-{"verification"}):raise ValueError("nonnegative_counts_required")
        if not isinstance(row["verification"],str) or not row["verification"].startswith("NO_DATA:"):raise ValueError("verification_limit_required")
        results[key]={"state":"DECLARED_ONLY",**{k:row[k] for k in sorted(required-{"verification"})}}
    evidence=json.dumps(d,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
    out={"schema":"preceptoros.lab.f01-weekly-draft/1","week":d["week"],
         "state":"UNSIGNED_RESEARCH_DRAFT",
         "verification":"NO_DATA: no_external_receipt_or_human_FIRMO_join",
         "f08":results["f08"],"f09":results["f09"],
         "input_sha256":hashlib.sha256(evidence).hexdigest()}
    if len(json.dumps(out,sort_keys=True,separators=(",",":")).encode())>=1024:raise ValueError("over_1024_byte_ceiling")
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("aggregates_json");a=p.parse_args()
    try:
        with open(a.aggregates_json,encoding="utf-8") as f:result=compose(json.load(f))
    except (ValueError,OSError) as e:p.exit(2,"NO_DATA: invalid_input ("+type(e).__name__+")\n")
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
