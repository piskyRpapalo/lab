"""Offline, metadata-only aggregation and Serion LoRA *proposal* gate.

aggregate(runs) and evaluate(runs, proposal=None, *, verify_receipt=None,
verify_review=None) return bounded dictionaries; neither executes any action.
Runs are closed records: content_sha256, split, target, arm, repeat, failure,
origin. Splits: train/holdout/regression/negative_control; arms:
baseline/control/candidate (control is the best measured simpler fix).
Repeat IDs are exactly 1 and 2. Verdicts come from the existing judge;
this module never scores answers. Content hashes identify independent cases.
Alternatively wrap canonical receipts in records with keys receipt,
content_sha256, split, target, arm, repeat. aggregate_receipts(records) and
evaluate(records, ...) accept these wrappers. Receipt integrity is NOT authority.

Proposal fields and example construction live in tests/test_meta_improvement.py.
Receipt verifier(ref, binding) must return True only after independently
checking source receipts, case hashes, repeat execution, model identity,
split assignment, and existing judge/gold provenance. simpler_fix_ref must
document prompt/retrieval/contract alternatives and the best measured control.
Review verifier(ref,
binding) returns a reviewer identity SHA256, or None. It must independently
check the referenced review, its exact binding, and its role; evidence review
covers judge family/presence/selection and gold, governance covers license,
privacy/consent, compute ceilings and rollback. Two distinct reviewers required.
These are trusted runtime capabilities, NEVER serialized approval flags.
All callbacks must be local, bounded, deterministic, and side-effect free.
SIMULATED inputs can only produce a SIMULATED_PROPOSAL. Successful measured gates
only recommend human review; training/activation authorization is always false.
"""
import hashlib
import re

from meta_harness.reuse import instrument
from meta_harness.delegation import FAILURES, NEXT

SPLITS = ("train", "holdout", "regression", "negative_control")
ARMS = ("baseline", "control", "candidate")
TARGETS = ("OUTPUT_SCHEMA", "TASK_SKILL")
INFRA = frozenset(FAILURES) - {"NONE", *TARGETS}
MAX_RUNS = 24000
HEX = re.compile(r"[0-9a-f]{64}\Z")
ROW = {"content_sha256", "split", "target", "arm", "repeat", "failure", "origin"}


def _digest(value):
    return hashlib.sha256(instrument("evidence").encode(value)).hexdigest()


def _hex(value):
    return type(value) is str and HEX.fullmatch(value) is not None


def _closed(value, keys):
    return type(value) is dict and set(value) == set(keys)


def _result(state, action, cause, **extra):
    return dict(state=state, action=action, cause=cause,
                lora_authorized=False, **extra)


class _Invalid(Exception):
    pass


def _require(condition):
    if not condition:
        raise _Invalid


def _aggregate(runs):
    _require(type(runs) is list and len(runs) <= MAX_RUNS)
    if runs and type(runs[0]) is dict and "receipt" in runs[0]:
        runs = _receipt_runs(runs)
    seen, cases, assignments = {}, {}, {}
    failures = {key: 0 for key in sorted(FAILURES)}
    for row in runs:
        _require(_closed(row, ROW))
        h, split, target, arm = (row[k] for k in
                                 ("content_sha256", "split", "target", "arm"))
        _require(_hex(h) and type(split) is str and split in SPLITS
                 and type(target) is str and target in TARGETS
                 and type(arm) is str and arm in ARMS
                 and type(row["repeat"]) is int and row["repeat"] in (1, 2)
                 and type(row["failure"]) is str and row["failure"] in FAILURES
                 and type(row["origin"]) is str
                 and row["origin"] in ("MEASURED", "SIMULATED"))
        # Reusing content under another target/split is leakage, not new evidence.
        _require(h not in assignments or assignments[h] == (split, target))
        assignments[h] = split, target
        key = (h, split, target, arm, row["repeat"])
        _require(key not in seen or seen[key] == row)
        seen[key] = dict(row)
        cases.setdefault((h, split, target), {})[arm, row["repeat"]] = row["failure"]
    rows = [seen[key] for key in sorted(seen)]
    counts = {s: {t: dict(unique=0, complete=0, eligible=0, infra=0,
                          incomplete=0, unstable=0, baseline=0, control=0,
                          candidate=0, baseline_losses=0, control_losses=0)
                  for t in TARGETS} for s in SPLITS}
    for row in rows:
        failures[row["failure"]] += 1
    for (_, split, target), outcomes in cases.items():
        c = counts[split][target]
        c["unique"] += 1
        if len(outcomes) != 6:
            c["incomplete"] += 1
            continue
        c["complete"] += 1
        if any(v in INFRA for v in outcomes.values()):
            c["infra"] += 1
            continue
        if any(outcomes[a, 1] != outcomes[a, 2] for a in ARMS):
            c["unstable"] += 1
            continue
        # A different task failure must not masquerade as a successful fix.
        if any(v not in ("NONE", target) for v in outcomes.values()):
            c["unstable"] += 1
            continue
        c["eligible"] += 1
        for a in ARMS:
            c[a] += outcomes[a, 1] != "NONE"
        for a in ("baseline", "control"):
            c[a + "_losses"] += outcomes[a, 1] == "NONE" and outcomes["candidate", 1] != "NONE"
    return dict(state="AGGREGATED" if rows else "NO_DATA",
                cause="metadata_only_not_source_verified" if rows else "no_runs",
                lora_authorized=False,
                origin=("SIMULATED" if any(r["origin"] == "SIMULATED" for r in rows)
                        else "MEASURED" if rows else "NO_DATA"),
                unique_cases=len(cases), unique_runs=len(rows),
                duplicates=len(runs) - len(rows), data_sha256=_digest(rows),
                split_sha256={s: _digest([r for r in rows if r["split"] == s]) for s in SPLITS},
                failures=failures, counts=counts)


def aggregate(runs):
    """Deduplicate repeats; return fixed labels/counts/hashes, never raw records."""
    try:
        return _aggregate(runs)
    except Exception:
        return _result("NO_DATA", "repair_contract", "invalid_or_unavailable_evidence")


def _receipt_runs(records):
    from meta_harness.delegation import verify
    rows, bindings = [], {}
    for record in records:
        _require(_closed(record, (ROW - {"failure", "origin"}) | {"receipt"}))
        r = record["receipt"]
        _require(verify(r))
        row = {k: v for k, v in record.items() if k != "receipt"}
        row["origin"] = "SIMULATED" if r["confidence_basis"] == "synthetic" else "MEASURED"
        row["failure"] = r["failure_class"]
        if r["measurement"] and r["measurement"]["grade"] == "NOT_EVALUATED":
            row["failure"] = "EVIDENCE"
        binding = (r["receipt_ref"], row)
        _require(r["run_id"] not in bindings or bindings[r["run_id"]] == binding)
        bindings[r["run_id"]] = binding
        rows.append(row)
    return rows


def aggregate_receipts(records):
    """Aggregate canonical receipt wrappers; no authentication claim is made."""
    return aggregate(records)


def _proposal(p):
    _require(_closed(p, {"adapter", "target_classes", "data_sha256", "evidence_ref",
                         "license_ref", "privacy_ref", "rollback_ref", "simpler_fix_ref", "compute_budget",
                         "pairing", "comparisons", "reviews", "min_gain_pp"}))
    _require(type(p["adapter"]) is str and p["adapter"] == "serion_lora"
             and type(p["target_classes"]) is list and 1 <= len(p["target_classes"]) <= 2
             and all(type(t) is str and t in TARGETS for t in p["target_classes"])
             and len(set(p["target_classes"])) == len(p["target_classes"])
             and type(p["min_gain_pp"]) is int and 10 <= p["min_gain_pp"] <= 100)
    for key in ("data_sha256", "evidence_ref", "license_ref", "privacy_ref", "rollback_ref", "simpler_fix_ref"):
        _require(_hex(p[key]))
    b = p["compute_budget"]
    _require(_closed(b, {"max_seconds", "max_memory_bytes", "max_cost_microunits"}))
    _require(all(type(v) is int and 0 < v <= 10**15 for v in b.values()))
    _require(_closed(p["pairing"], {"manipulator", "judge"}))
    _require(type(p["comparisons"]) is list and len(p["comparisons"]) <= 12)
    _require(type(p["reviews"]) is list and len(p["reviews"]) <= 2)
    # Bound receipt/proposal encoding before invoking external instruments.
    for pair in p["comparisons"]:
        _require(_closed(pair, {"split", "target", "arm", "left", "right"}))
        _require(type(pair["split"]) is str and pair["split"] in SPLITS[1:]
                 and type(pair["target"]) is str and pair["target"] in TARGETS
                 and type(pair["arm"]) is str and pair["arm"] in ARMS[:2])
        for side in ("left", "right"):
            r = pair[side]
            _require(_closed(r, {"state", "device", "value", "workload", "workload_version",
                                 "parameters_digest", "metric", "unit", "method", "observed_at", "source"}))
            for k, v in r.items():
                _require((type(v) is str and len(v) <= 120) if k != "value"
                         else type(v) is int and 0 <= v <= MAX_RUNS)
    for role in ("manipulator", "judge"):
        member = p["pairing"][role]
        _require(_closed(member, {"model", "family"}))
        _require(all(type(v) is str and len(v) <= 120 for v in member.values()))
    for r in p["reviews"]:
        _require(_closed(r, {"role", "ref"}) and _hex(r["ref"])
                 and type(r["role"]) is str and r["role"] in ("evidence", "governance"))
    _require(len(instrument("evidence").encode(p)) < 16384)


def _comparisons(p, summary):
    required = {(s, t, a) for s in SPLITS[1:] for t in p["target_classes"]
                for a in ARMS[:2]}
    seen = set()
    for pair in p["comparisons"]:
        key = (pair["split"], pair["target"], pair["arm"])
        _require(key in required and key not in seen)
        seen.add(key)
        s, t, a = key
        c = summary["counts"][s][t]
        left, right = pair["left"], pair["right"]
        _require(left["value"] == c[a] and right["value"] == c["candidate"])
        _require(left["metric"] == "failure_count" and left["unit"] == "cases"
                 and left["parameters_digest"] == summary["split_sha256"][s])
        _require(instrument("compare").compare(left, right)["state"] == "COMPARABLE")
    _require(seen == required)


def evaluate(runs, proposal=None, *, verify_receipt=None, verify_review=None):
    """Return NO_DATA, NO_LORA, SIMULATED_PROPOSAL, or PROPOSAL_ONLY.

    Verifier binding is {data_sha256, proposal_sha256, role}; proposal digest
    excludes reviews to avoid circular reference hashes. Evidence and governance
    review refs bind the exact proposal, including provenance and safety refs.
    Aggregation is recomputed; caller-supplied summary counts are never trusted.
    """
    try:
        summary = _aggregate(runs)
        p = proposal
        if p is not None:
            _proposal(p)
            _require(p["data_sha256"] == summary["data_sha256"])
        targets = p["target_classes"] if p is not None else [
            t for t in TARGETS if any(summary["counts"][s][t]["unique"] for s in SPLITS)] or ["TASK_SKILL"]
        base = dict(origin=summary["origin"], unique_cases=summary["unique_cases"],
                    data_sha256=summary["data_sha256"])
        if p is None:
            for category in sorted(INFRA):
                if summary["failures"][category]:
                    return _result("NO_DATA", NEXT[category], "infrastructure_not_lora_evidence", **base)
        if "OUTPUT_SCHEMA" in targets:
            return _result("NO_LORA", "repair_contract", "schema_requires_contract_fix", **base)
        for t in targets:
            c = summary["counts"]
            if c["holdout"][t]["unique"] < 60:
                return _result("NO_DATA", "collect_independent_holdout", "insufficient_independent_cases", **base)
            if any(c[s][t]["incomplete"] or c[s][t]["unstable"] for s in SPLITS):
                return _result("NO_DATA", "collect_more", "two_stable_paired_repeats_required", **base)
            if c["holdout"][t]["eligible"] < 60:
                return _result("NO_DATA", "collect_independent_holdout", "insufficient_independent_cases", **base)
            if (c["train"][t]["eligible"] < 1
                    or any(c[s][t]["eligible"] < 20 for s in SPLITS[2:])):
                return _result("NO_DATA", "collect_more", "insufficient_independent_cases", **base)
        if p is None:
            return _result("NO_DATA", "collect_more", "proposal_contract_missing", **base)
        family = instrument("family")
        pairing = family.assess(dict(schema=family.SCHEMA, **p["pairing"], held_out=True,
                                    cases_per_class=min(summary["counts"]["holdout"][t]["eligible"]
                                                        for t in p["target_classes"])))
        if pairing["state"] == "DENY":
            return _result("NO_LORA", "repair_contract", "canonical_pairing_denied", **base)
        _comparisons(p, summary)
        for t in p["target_classes"]:
            if any(summary["counts"]["negative_control"][t][a] for a in ARMS):
                return _result("NO_LORA", "repair_contract", "negative_control_failed", **base)
            for s in SPLITS[1:]:
                c = summary["counts"][s][t]
                if any(c[a + "_losses"] for a in ARMS[:2]):
                    return _result("NO_LORA", "repair_contract", "paired_regression_detected", **base)
            c = summary["counts"]["holdout"][t]
            if any((c[a] - c["candidate"]) * 100 < p["min_gain_pp"] * c["eligible"]
                   for a in ARMS[:2]):
                return _result("NO_LORA", "prefer_simpler_fix", "meaningful_gain_not_established", **base)
        binding = dict(data_sha256=summary["data_sha256"],
                       proposal_sha256=_digest({k: v for k, v in p.items() if k != "reviews"}),
                       role="receipts")
        if summary["origin"] == "SIMULATED":
            return _result("SIMULATED_PROPOSAL", "collect_more", "simulation_cannot_authorize_lora", **base)
        if not callable(verify_receipt) or verify_receipt(p["evidence_ref"], dict(binding)) is not True:
            return _result("NO_DATA", "collect_more", "receipts_not_independently_verified", **base)
        if {r["role"] for r in p["reviews"]} != {"evidence", "governance"} or not callable(verify_review):
            return _result("NO_DATA", "collect_more", "independent_reviews_missing", **base)
        identities = set()
        for review in p["reviews"]:
            binding["role"] = review["role"]
            identity = verify_review(review["ref"], dict(binding))
            if not _hex(identity) or identity in identities:
                return _result("NO_DATA", "collect_more", "independent_reviews_unverified", **base)
            identities.add(identity)
        if len({r["ref"] for r in p["reviews"]}) != 2:
            return _result("NO_DATA", "collect_more", "independent_reviews_unverified", **base)
        return _result("PROPOSAL_ONLY", "human_review", "prerequisites_verified_not_authorization",
                       canonical_family_state=pairing["state"], **base)
    except Exception:
        return _result("NO_DATA", "repair_contract", "invalid_or_unavailable_evidence")
