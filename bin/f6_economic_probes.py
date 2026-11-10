#!/usr/bin/env python3
"""Offline F6 economic adversarial consistency checks, never an authorization service."""
import argparse
import json

KINDS={"reach_inflation","budget_overpromise","arbitration_spoof"}

def assess(p):
    if not isinstance(p,dict) or set(p)!={"kind","facts"} or p["kind"] not in KINDS or not isinstance(p["facts"],dict):
        raise ValueError("closed_probe_required")
    kind,f=p["kind"],p["facts"]
    if kind=="reach_inflation":
        if set(f)!={"claimed_reach","receipt_digests"}:raise ValueError("closed_reach_facts")
        if type(f["claimed_reach"]) is not int or f["claimed_reach"]<0:raise ValueError("invalid_reach")
        hashes=f["receipt_digests"]
        if not isinstance(hashes,list) or any(not isinstance(x,str) or not x for x in hashes):raise ValueError("invalid_digests")
        if f["claimed_reach"]>len(set(hashes)):
            verdict,cause="DENY","claimed_reach_exceeds_distinct_receipts"
        else:verdict,cause="NO_DATA","receiver_signatures_not_verified"
    elif kind=="budget_overpromise":
        if set(f)!={"promised_j","available_j"}:raise ValueError("closed_budget_facts")
        if any(type(f[k]) is not int or f[k]<0 for k in f):raise ValueError("invalid_joules")
        if f["promised_j"]>f["available_j"]:
            verdict,cause="DENY","promised_budget_exceeds_declared_capacity"
        else:verdict,cause="NO_DATA","energy_sensor_attestation_missing"
    else:
        if set(f)!={"role","requests_arbitration"} or not isinstance(f["role"],str) or type(f["requests_arbitration"]) is not bool:
            raise ValueError("closed_arbitration_facts")
        if f["requests_arbitration"] and f["role"]!="sovereign":
            verdict,cause="DENY","non_sovereign_attempted_arbitration"
        else:verdict,cause="NO_DATA","signature_and_policy_not_verified"
    return {"schema":"preceptoros.lab.f6-offline-probe/1","kind":kind,
            "verdict":verdict,"cause":cause,"scope":"SYNTHETIC_ONLY",
            "authority":"NONE"}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("fixture_json");args=parser.parse_args()
    try:
        with open(args.fixture_json,encoding="utf-8") as stream: verdict=assess(json.load(stream))
    except (ValueError,OSError) as ex:parser.exit(2,"NO_DATA: invalid_fixture ("+type(ex).__name__+")\n")
    print(json.dumps(verdict,sort_keys=True,separators=(",",":")))
