#!/usr/bin/env python3
"""DFA-B5 offline family-blind gate for declared model candidates, never a model selector."""
import argparse
import json
import re

SCHEMA = "preceptoros.lab.dfa-b5-pairing/1"
MODEL = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._:-]{0,119}\Z")
FAMILY = re.compile(r"[a-z][a-z0-9_-]{1,47}\Z")


def _member(candidate):
    if not isinstance(candidate, dict) or set(candidate) != {"model", "family"}:
        raise ValueError("closed_candidate_required")
    if not isinstance(candidate["model"], str) or not MODEL.fullmatch(candidate["model"]):
        raise ValueError("invalid_model_id")
    if not isinstance(candidate["family"], str) or not FAMILY.fullmatch(candidate["family"]):
        raise ValueError("invalid_family")
    return candidate


def assess(proposal):
    if not isinstance(proposal, dict) or set(proposal) != {
            "schema", "manipulator", "judge", "cases_per_class", "held_out"}:
        raise ValueError("closed_proposal_required")
    if proposal["schema"] != SCHEMA:
        raise ValueError("unsupported_schema")
    manipulator = _member(proposal["manipulator"])
    judge = _member(proposal["judge"])
    n = proposal["cases_per_class"]
    held_out = proposal["held_out"]
    if type(n) is not int or not 0 <= n <= 100000:
        raise ValueError("invalid_class_denominator")
    if type(held_out) is not bool:
        raise ValueError("invalid_holdout_declaration")
    if judge["model"] == manipulator["model"]:
        state, cause = "DENY", "judge_and_manipulator_same_model"
    elif judge["family"] == manipulator["family"]:
        state, cause = "DENY", "judge_same_declared_family"
    elif n < 60:
        state, cause = "DENY", "insufficient_declared_cases_per_class"
    elif not held_out:
        state, cause = "DENY", "heldout_set_not_declared"
    else:
        state, cause = "NO_DATA", "family_and_model_presence_not_independently_verified"
    return {"schema": SCHEMA, "state": state, "cause": cause,
            "declared_cases_per_class": n, "held_out": held_out,
            "same_declared_family": judge["family"] == manipulator["family"],
            "model_presence": "NO_DATA: no_ollama_probe",
            "judge_selection": "NO_DATA: sovereign_selection_not_supplied",
            "consent": "NO_DATA: no_real_case_data"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("synthetic_pair_file")
    args = parser.parse_args()
    try:
        with open(args.synthetic_pair_file, encoding="utf-8") as stream:
            result = assess(json.load(stream))
        code = 0 if result["state"] in ("DENY", "NO_DATA") else 2
    except (ValueError, OSError, TypeError) as exc:
        result = {"state": "NO_DATA", "cause": type(exc).__name__}
        code = 2
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
