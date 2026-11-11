#!/usr/bin/env python3
"""DFA-B2 offline scorer of declared clause labels; not human comprehension proof."""
import argparse
import json
import re

SCHEMA = "preceptoros.lab.dfa-b2-clarity-labels/1"
LABELS = ("SI", "NO", "CUANDO")
ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,63}\Z")
CAUSE = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")


def score(data):
    if not isinstance(data, dict) or set(data) != {"schema", "cases", "reference_provenance"}:
        raise ValueError("closed_case_set_required")
    if data["schema"] != SCHEMA or data["reference_provenance"] not in (
            "SYNTHETIC", "HUMAN_UNVERIFIED"):
        raise ValueError("invalid_schema_or_provenance")
    rows = data["cases"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:
        raise ValueError("case_count_out_of_range")
    seen = set()
    counters = {"SI": 0, "NO": 0, "CUANDO": 0, "NO_DATA": 0}
    matches = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) - {"id", "reference", "prediction", "cause"}:
            raise ValueError("closed_case_required")
        ident = row.get("id")
        if not isinstance(ident, str) or not ID.fullmatch(ident):
            raise ValueError("invalid_case_id")
        if ident in seen:
            raise ValueError("duplicate_case_id")
        seen.add(ident)
        if row.get("reference") not in LABELS:
            raise ValueError("human_reference_label_missing")
        prediction = row.get("prediction")
        if prediction in LABELS:
            if set(row) != {"id", "reference", "prediction"}:
                raise ValueError("labeled_prediction_has_cause")
        elif prediction == "NO_DATA":
            if set(row) != {"id", "reference", "prediction", "cause"} or not isinstance(
                    row["cause"], str) or not CAUSE.fullmatch(row["cause"]):
                raise ValueError("no_data_requires_scrubbed_cause")
        else:
            raise ValueError("invalid_prediction")
        counters[prediction] += 1
        matches += prediction == row["reference"]
    n = len(rows)
    return {
        "schema": SCHEMA,
        "state": "SYNTHETIC_SCORE" if data["reference_provenance"] == "SYNTHETIC"
                 else "NO_DATA",
        "cause": "synthetic_only" if data["reference_provenance"] == "SYNTHETIC"
                 else "human_reference_attestation_missing",
        "cases": n,
        "matches": matches,
        "agreement_fraction": [matches, n],
        "non_abstention_fraction": [n - counters["NO_DATA"], n],
        "prediction_counts": counters,
        "threshold_evaluation": "NO_DATA: independent_human_evaluation_not_verified",
        "source_clause_content": "NOT_INCLUDED",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture_file")
    a = parser.parse_args()
    try:
        with open(a.fixture_file, encoding="utf-8") as stream:
            result = score(json.load(stream))
        code = 0 if result["state"] == "SYNTHETIC_SCORE" else 2
    except (OSError, TypeError, ValueError) as ex:
        result = {"state": "NO_DATA", "cause": type(ex).__name__}
        code = 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
