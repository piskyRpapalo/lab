#!/usr/bin/env python3
"""F-08 offline duration summary. Declared timestamps do not prove FIRMO."""
import argparse
from datetime import datetime
import json
import math

def utc(s):
    if not isinstance(s,str) or not s.endswith("Z"): raise ValueError("utc_z_required")
    try: t=datetime.fromisoformat(s.replace("Z","+00:00"))
    except ValueError: raise ValueError("invalid_timestamp")
    if t.utcoffset() is None or t.utcoffset().total_seconds()!=0: raise ValueError("utc_required")
    return t

def summary(data):
    if not isinstance(data,dict) or set(data)!={"events"} or not isinstance(data["events"],list): raise ValueError("closed_events_required")
    seen=set(); durations=[]; pending=0
    for e in data["events"]:
        if not isinstance(e,dict) or not isinstance(e.get("id"),str) or not e["id"]: raise ValueError("missing_id")
        if e["id"] in seen: raise ValueError("duplicate_id")
        seen.add(e["id"])
        if set(e)-{"id","opened_at","signed_at","receipt_ref","cause"}: raise ValueError("unknown_fields")
        start=utc(e.get("opened_at"))
        if e.get("signed_at") is None:
            if not isinstance(e.get("cause"),str) or not e["cause"].strip() or "receipt_ref" in e: raise ValueError("pending_requires_cause")
            pending+=1;continue
        if "cause" in e or not isinstance(e.get("receipt_ref"),str) or not e["receipt_ref"]:raise ValueError("signed_requires_reference")
        seconds=(utc(e["signed_at"])-start).total_seconds()
        if seconds<0:raise ValueError("negative_elapsed")
        durations.append(seconds)
    durations.sort()
    out={"schema":"preceptoros.lab.f08-observation/1","state":"COMPUTED_FROM_DECLARED_INPUT","verification":"NO_DATA: declared_reference_not_verified","total":len(seen),"pending":pending,"signed":len(durations)}
    if durations:
        out["elapsed_seconds"]={f"p{p}":durations[math.ceil(len(durations)*p/100)-1] for p in (50,90,99)}
    else:
        out["elapsed_seconds"]=None;out["cause"]="NO_DATA: no_signed_pairs"
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("json_file");a=p.parse_args()
    try:
        with open(a.json_file,encoding="utf-8") as f: result=summary(json.load(f))
    except (ValueError,OSError) as ex:p.exit(2,"NO_DATA: invalid_input ("+type(ex).__name__+")\n")
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
