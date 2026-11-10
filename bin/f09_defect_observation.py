#!/usr/bin/env python3
"""F-09 offline PR evidence counters; not a CI runner, no network or authority."""
import argparse
import json

def summarize(data):
    if not isinstance(data,dict) or set(data)!={"observations"} or not isinstance(data["observations"],list):raise ValueError("closed_observations_required")
    seen=set(); n={"GREEN":0,"RED":0,"NO_DATA":0};attempted=0;caught=0
    for row in data["observations"]:
        if not isinstance(row,dict) or set(row)-{"id","state","cause","sabotage"}:raise ValueError("unknown_observation_fields")
        if not isinstance(row.get("id"),str) or not row["id"]:raise ValueError("id_required")
        if row["id"] in seen:raise ValueError("duplicate_id")
        seen.add(row["id"])
        state=row.get("state")
        if state not in n:raise ValueError("state_unknown")
        if state=="NO_DATA":
            if not isinstance(row.get("cause"),str) or not row["cause"].strip():raise ValueError("no_data_requires_cause")
        elif "cause" in row:raise ValueError("observed_state_cannot_have_cause")
        sab=row.get("sabotage")
        if not isinstance(sab,dict) or set(sab)-{"attempted","red_before_green"} or type(sab.get("attempted")) is not bool:raise ValueError("closed_sabotage_required")
        if sab["attempted"]:
            if type(sab.get("red_before_green")) is not bool:raise ValueError("sabotage_requires_measured_red")
            if state=="NO_DATA":raise ValueError("sabotage_result_requires_observation")
            attempted+=1;caught+=int(sab["red_before_green"])
        elif "red_before_green" in sab:raise ValueError("not_attempted_must_not_claim_result")
        n[state]+=1
    observed=n["GREEN"]+n["RED"]
    return {"schema":"preceptoros.lab.f09-observation/1","state":"COMPUTED_FROM_DECLARED_INPUT",
            "verification":"NO_DATA: source_ci_receipts_not_verified",
            "total":len(seen),"observed":observed,"green":n["GREEN"],"red":n["RED"],
            "unknown":n["NO_DATA"],"red_fraction":([n["RED"],observed] if observed else None),
            "sabotage_attempted":attempted,"sabotage_red_before_green":caught,
            "sabotage_fraction":([caught,attempted] if attempted else None),
            "cause_red_fraction":None if observed else "NO_DATA: no_observed_prs",
            "cause_sabotage_fraction":None if attempted else "NO_DATA: no_sabotage_attempts"}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("observations_json");a=p.parse_args()
    try:
        with open(a.observations_json,encoding="utf-8") as f:out=summarize(json.load(f))
    except (ValueError,OSError) as ex:p.exit(2,"NO_DATA: invalid_input ("+type(ex).__name__+")\n")
    print(json.dumps(out,sort_keys=True,separators=(",",":")))

if __name__=="__main__":main()
