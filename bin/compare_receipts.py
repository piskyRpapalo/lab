#!/usr/bin/env python3
"""Compare two declared benchmark receipts without running a benchmark.

A metadata match is necessary, not proof of identical conditions or of a valid
measurement. The caller supplies already-reviewed, non-private receipts.
"""
import json
import math
import re
import sys

MATCH = ("workload", "workload_version", "parameters_digest", "metric", "unit", "method")


def compare(left, right):
    if not isinstance(left, dict) or not isinstance(right, dict):
        return {"state": "NO_DATA", "cause": "two receipt objects are required"}
    for index, item in enumerate((left, right), 1):
        if item.get("state") != "MEASURED":
            return {"state": "NO_DATA", "cause": "receipt %d is not MEASURED" % index}
        for field in MATCH + ("device", "observed_at", "source"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                return {"state": "NO_DATA", "cause": "receipt %d missing %s" % (index, field)}
        if not re.fullmatch(r"[0-9a-f]{64}", item["parameters_digest"]):
            return {"state": "NO_DATA", "cause": "receipt %d has invalid parameters digest" % index}
        value = item.get("value")
        try:
            finite = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            return {"state": "NO_DATA", "cause": "receipt %d has no finite value" % index}
    for field in MATCH:
        if left[field] != right[field]:
            return {"state": "NO_DATA", "cause": "receipt mismatch: " + field}
    delta = right["value"] - left["value"]
    try:
        finite_delta = math.isfinite(delta)
    except OverflowError:
        finite_delta = False
    if not finite_delta:
        return {"state": "NO_DATA", "cause": "difference is not finite"}
    return {"state": "COMPARABLE", "metric": left["metric"], "unit": left["unit"],
            "left": {"device": left["device"], "value": left["value"], "source": left["source"], "observed_at": left["observed_at"]},
            "right": {"device": right["device"], "value": right["value"], "source": right["source"], "observed_at": right["observed_at"]},
            "difference": delta,
            "scope": "declared metadata matches; source validity and complete equivalence not independently verified"}


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("usage: compare_receipts.py FILE.json")
        with open(sys.argv[1], encoding="utf-8") as stream:
            data = json.load(stream)
        if not isinstance(data, dict) or set(data) != {"left", "right"}:
            raise ValueError("input must contain left and right")
        result = compare(data["left"], data["right"])
    except (OSError, ValueError) as exc:
        result = {"state": "NO_DATA", "cause": str(exc)}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result["state"] == "COMPARABLE" else 1


if __name__ == "__main__":
    sys.exit(main())
