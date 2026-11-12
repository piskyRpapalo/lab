"""Generated metadata only. MEASURED-shaped fixtures and verifier doubles test
code paths, never actual measurements or human review. No private harness.
"""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from meta_harness import improvement as m


def sha(label):
    return hashlib.sha256(label.encode()).hexdigest()


def runs(n=60, origin="MEASURED", target="TASK_SKILL"):
    rows = []
    for split, count in (("train", 1), ("holdout", n),
                         ("regression", 20), ("negative_control", 20)):
        for i in range(count):
            for arm in m.ARMS:
                failed = split == "train" and arm != "candidate"
                if split == "holdout":
                    failed = i < {"baseline": 36, "control": 24, "candidate": 6}[arm]
                for repeat in (1, 2):
                    rows.append(dict(content_sha256=sha(split + str(i)), split=split,
                                     target=target, arm=arm, repeat=repeat,
                                     failure=target if failed else "NONE", origin=origin))
    return rows


def receipt(split, value, digest):
    return dict(state="MEASURED", device="fixture", value=value,
                workload=split, workload_version="1", parameters_digest=digest,
                metric="failure_count", unit="cases", method="existing-judge-fixture",
                observed_at="2026-11-12T00:00:00Z", source="fixture-not-measurement")


def proposal(rows):
    a = m.aggregate(rows)
    target = rows[0]["target"]
    comparisons = []
    for split in m.SPLITS[1:]:
        c = a["counts"][split][target]
        for arm in m.ARMS[:2]:
            comparisons.append(dict(split=split, target=target, arm=arm,
                                    left=receipt(split, c[arm], a["split_sha256"][split]),
                                    right=receipt(split, c["candidate"], a["split_sha256"][split])))
    return dict(adapter="serion_lora", target_classes=[target], data_sha256=a["data_sha256"],
                evidence_ref=sha("receipts"), license_ref=sha("license"),
                privacy_ref=sha("privacy"), rollback_ref=sha("rollback"), simpler_fix_ref=sha("simpler-fixes"),
                compute_budget=dict(max_seconds=3600, max_memory_bytes=2**30,
                                    max_cost_microunits=1000000),
                pairing=dict(manipulator=dict(model="fixture_subject", family="subject"),
                             judge=dict(model="fixture_judge", family="judge")),
                comparisons=comparisons, min_gain_pp=10,
                reviews=[dict(role=role, ref=sha(role)) for role in ("evidence", "governance")])


def trusted_receipt(ref, binding):
    return ref == sha("receipts") and binding["role"] == "receipts"


def trusted_review(ref, binding):
    role = binding["role"]
    return sha("reviewer-" + role) if ref == sha(role) else None


class ImprovementTests(unittest.TestCase):
    def setUp(self):
        self.rows = runs()
        self.p = proposal(self.rows)

    def evaluate(self, rows=None, p=None, **overrides):
        options = dict(verify_receipt=trusted_receipt, verify_review=trusted_review)
        options.update(overrides)
        return m.evaluate(self.rows if rows is None else rows,
                          self.p if p is None else p, **options)

    def refresh(self):
        self.p = proposal(self.rows)

    def assertCause(self, cause, **options):
        self.assertEqual(self.evaluate(**options)["cause"], cause)

    def test_aggregation_counts_cases_not_runs(self):
        a = m.aggregate(self.rows)
        c = a["counts"]["holdout"]["TASK_SKILL"]
        self.assertEqual((a["unique_cases"], a["unique_runs"]), (101, 606))
        self.assertEqual((c["eligible"], c["baseline"], c["control"], c["candidate"]), (60, 36, 24, 6))
        self.assertEqual(c["control_losses"], 0)
        self.assertEqual(set(a["failures"]), set(m.FAILURES))

    def test_positive_proposal_is_never_authorization(self):
        r = self.evaluate()
        self.assertEqual((r["state"], r["action"]), ("PROPOSAL_ONLY", "human_review"))
        self.assertFalse(r["lora_authorized"])
        self.assertEqual(r["canonical_family_state"], "NO_DATA")

    def test_simulated_demo_never_authorizes(self):
        rows = runs(origin="SIMULATED")
        r = self.evaluate(rows=rows, p=proposal(rows))
        self.assertEqual((r["state"], r["origin"]), ("SIMULATED_PROPOSAL", "SIMULATED"))
        self.assertEqual(r["action"], "collect_more")
        self.assertFalse(r["lora_authorized"])

    def test_duplicate_flood(self):
        rows = runs(n=12)
        p = proposal(rows)
        a = m.aggregate(rows * 20)
        self.assertEqual(a["counts"]["holdout"]["TASK_SKILL"]["eligible"], 12)
        self.assertEqual(a["data_sha256"], m.aggregate(rows)["data_sha256"])
        self.assertCause("insufficient_independent_cases", rows=rows * 20, p=p)

    def test_order_and_duplicate_invariance(self):
        a = m.aggregate(self.rows)
        b = m.aggregate(list(reversed(self.rows)) + self.rows[:5])
        self.assertEqual(a["data_sha256"], b["data_sha256"])
        self.assertEqual(a["counts"], b["counts"])
        self.assertEqual(self.evaluate(), self.evaluate(list(reversed(self.rows))))

    def test_conflicting_duplicate_rejected(self):
        row = dict(self.rows[0], failure="NONE")
        self.assertEqual(m.aggregate(self.rows + [row])["action"], "repair_contract")

    def test_split_leakage_rejected(self):
        for source in m.SPLITS:
            for dest in m.SPLITS:
                if source == dest:
                    continue
                rows = copy.deepcopy(self.rows)
                h = next(r["content_sha256"] for r in rows if r["split"] == source)
                next(r for r in rows if r["split"] == dest)["content_sha256"] = h
                with self.subTest(source=source, dest=dest):
                    self.assertEqual(m.aggregate(rows)["action"], "repair_contract")

    def test_59_cases_cannot_pass(self):
        rows = runs(n=59)
        self.assertCause("insufficient_independent_cases", rows=rows, p=proposal(rows))

    def test_two_repeats_required_in_every_arm(self):
        for arm in m.ARMS:
            rows = [r for r in self.rows if not
                    (r["split"] == "holdout" and r["arm"] == arm and r["repeat"] == 2)]
            with self.subTest(arm=arm):
                self.assertCause("two_stable_paired_repeats_required", rows=rows, p=proposal(rows))

    def test_unstable_verdicts_are_not_evidence(self):
        next(r for r in self.rows if r["split"] == "holdout")["failure"] = "NONE"
        self.refresh()
        self.assertCause("two_stable_paired_repeats_required")

    def test_infra_excluded(self):
        for failure in sorted(m.INFRA):
            rows = copy.deepcopy(self.rows)
            next(r for r in rows if r["split"] == "holdout")["failure"] = failure
            a = m.aggregate(rows)
            c = a["counts"]["holdout"]["TASK_SKILL"]
            with self.subTest(failure=failure):
                self.assertEqual((c["eligible"], c["infra"]), (59, 1))
                self.assertEqual(self.evaluate(rows=rows, p=proposal(rows))["action"], "collect_independent_holdout")

    def test_other_failure_not_success(self):
        for r in self.rows:
            if r["split"] == "holdout" and r["arm"] == "candidate":
                r["failure"] = "OUTPUT_SCHEMA"
        self.refresh()
        self.assertCause("two_stable_paired_repeats_required")

    def test_output_schema_recommends_contract_fix(self):
        rows = runs(target="OUTPUT_SCHEMA")
        self.assertCause("schema_requires_contract_fix", rows=rows, p=proposal(rows))

    def test_required_splits_are_distinct_and_present(self):
        for split in m.SPLITS:
            rows = [r for r in self.rows if r["split"] != split]
            with self.subTest(split=split):
                self.assertCause("insufficient_independent_cases", rows=rows, p=proposal(rows))

    def test_paired_regressions_veto_aggregate_benefit(self):
        for split in m.SPLITS[1:]:
            rows = copy.deepcopy(self.rows)
            h = [r["content_sha256"] for r in rows if r["split"] == split][-1]
            for r in rows:
                if r["content_sha256"] == h and r["arm"] == "candidate":
                    r["failure"] = "TASK_SKILL"
            cause = "negative_control_failed" if split == "negative_control" else "paired_regression_detected"
            self.assertCause(cause, rows=rows, p=proposal(rows))

    def test_negative_controls_must_pass(self):
        for r in self.rows:
            if r["split"] == "negative_control":
                r["failure"] = "TASK_SKILL"
        self.refresh()
        self.assertCause("negative_control_failed")

    def test_simpler_fix_equal_to_candidate_blocks_lora(self):
        for r in self.rows:
            if r["split"] == "holdout" and r["arm"] == "control":
                i_hash = r["content_sha256"]
                r["failure"] = next(x["failure"] for x in self.rows if
                                    x["content_sha256"] == i_hash and x["arm"] == "candidate")
        self.refresh()
        self.assertEqual(self.evaluate()["action"], "prefer_simpler_fix")

    def test_meaningful_gain_target_is_enforced(self):
        self.p["min_gain_pp"] = 31
        self.assertCause("meaningful_gain_not_established")
        self.p["min_gain_pp"] = 30
        self.assertEqual(self.evaluate()["state"], "PROPOSAL_ONLY")

    def test_pairing_canonical_same_model_and_family_denials(self):
        for field in ("family", "model"):
            p = copy.deepcopy(self.p)
            p["pairing"]["judge"][field] = p["pairing"]["manipulator"][field]
            self.assertCause("canonical_pairing_denied", p=p)

    def test_comparison_sabotage(self):
        for sabotage in ("count", "missing", "duplicate", "digest"):
            p = copy.deepcopy(self.p)
            if sabotage == "count":
                p["comparisons"][0]["left"]["value"] += 1
            elif sabotage == "missing":
                p["comparisons"].pop()
            elif sabotage == "duplicate":
                p["comparisons"][-1] = p["comparisons"][0]
            else:
                p["comparisons"][0]["left"]["parameters_digest"] = sha("forged")
            self.assertEqual(self.evaluate(p=p)["action"], "repair_contract")

    def test_receipt_verifier(self):
        for verifier in (None, True, lambda *_: {"verified": True}, lambda *_: 1):
            self.assertCause("receipts_not_independently_verified", verify_receipt=verifier)
        self.p["human_verified"] = True
        self.assertEqual(self.evaluate()["action"], "repair_contract")

    def test_no_serialized_review(self):
        self.p["reviews"] = []
        self.assertCause("independent_reviews_missing")
        self.p = proposal(self.rows)
        self.assertCause("independent_reviews_unverified", verify_review=lambda *_: True)
        self.assertCause("independent_reviews_missing", verify_review=None)

    def test_review_independence(self):
        self.assertCause("independent_reviews_unverified", verify_review=lambda *_: sha("one-person"))
        self.p["reviews"][1]["ref"] = self.p["reviews"][0]["ref"]
        self.assertNotEqual(self.evaluate()["state"], "PROPOSAL_ONLY")

    def test_reviews_bind_exact_data_proposal_and_role(self):
        accepted = []
        def capture(ref, binding):
            accepted.append(dict(binding))
            return trusted_review(ref, binding)
        self.assertEqual(self.evaluate(verify_review=capture)["state"], "PROPOSAL_ONLY")
        self.assertEqual({b["role"] for b in accepted}, {"evidence", "governance"})
        seal = accepted[0]["proposal_sha256"]
        self.p["rollback_ref"] = sha("different rollback")
        def stale(ref, binding):
            return trusted_review(ref, binding) if binding["proposal_sha256"] == seal else None
        self.assertCause("independent_reviews_unverified", verify_review=stale)
        self.assertEqual(accepted[0]["data_sha256"], self.p["data_sha256"])

    def test_proposal_requirements(self):
        for field in ("license_ref", "privacy_ref", "rollback_ref", "simpler_fix_ref", "data_sha256", "evidence_ref", "compute_budget"):
            p = copy.deepcopy(self.p)
            del p[field]
            self.assertEqual(self.evaluate(p=p)["action"], "repair_contract")
        for key in self.p["compute_budget"]:
            for value in (0, -1, True, 1.5, 10**16):
                p = copy.deepcopy(self.p)
                p["compute_budget"][key] = value
                self.assertEqual(self.evaluate(p=p)["action"], "repair_contract")

    def test_invalid_rows_closed_schema_and_safe_errors(self):
        for field, value in (("target", "private-label"), ("failure", "private-error"),
                             ("repeat", True), ("repeat", 3), ("origin", "human_verified"),
                             ("content_sha256", "bad"), ("split", "control")):
            rows = copy.deepcopy(self.rows)
            rows[0][field] = value
            result = m.aggregate(rows)
            self.assertEqual(result["action"], "repair_contract")
            self.assertNotIn("private", json.dumps(result))
        self.rows[0]["raw_answer"] = "SECRET"
        self.assertNotIn("SECRET", json.dumps(m.aggregate(self.rows)))
        self.assertEqual(m.aggregate(self.rows)["state"], "NO_DATA")

    def test_limits_and_arbitrary_bad_inputs(self):
        for value in (None, {}, "SECRET", [None], self.rows * 40):
            self.assertEqual(m.aggregate(value)["state"], "NO_DATA")
        for value in (None, {}, "SECRET"):
            self.assertEqual(m.evaluate(self.rows, value)["state"], "NO_DATA")

    def test_private_exception(self):
        def explode(*_):
            raise RuntimeError("SECRET/private/error")
        for options in (dict(verify_receipt=explode), dict(verify_review=explode)):
            result = self.evaluate(**options)
            self.assertEqual(result["state"], "NO_DATA")
            self.assertNotIn("SECRET", json.dumps(result))

    def test_canonical_instruments_are_actually_used(self):
        with patch.object(m, "instrument", wraps=m.instrument) as instrument:
            self.assertEqual(self.evaluate()["state"], "PROPOSAL_ONLY")
            self.assertEqual({c.args[0] for c in instrument.call_args_list}, {"evidence", "compare", "family"})

    def test_no_mutation_and_bounded_safe_outputs(self):
        self.p["pairing"]["judge"]["model"] = "PRIVATE_MODEL"
        self.p["comparisons"][0]["left"]["source"] = "PRIVATE_SOURCE"
        before = copy.deepcopy((self.rows, self.p))
        for result in (m.aggregate(self.rows), self.evaluate()):
            encoded = json.dumps(result, sort_keys=True)
            self.assertLess(len(encoded.encode()), 8192)
            self.assertNotIn("PRIVATE", encoded)
            self.assertFalse(result["lora_authorized"])
        self.assertEqual((self.rows, self.p), before)

    def test_public_pilot_no_lora(self):
        rows = [dict(self.rows[0], split="holdout", repeat=i) for i in (1, 2)]
        a, r = m.aggregate(rows), m.evaluate(rows)
        self.assertEqual(a["counts"]["holdout"]["TASK_SKILL"]["complete"], 0)
        self.assertEqual((r["unique_cases"], r["action"]), (1, "collect_independent_holdout"))
        self.assertFalse(r["lora_authorized"])

    def test_each_owned_file_under_house_ceiling(self):
        for path in (Path(m.__file__), Path(__file__)):
            self.assertLess(path.stat().st_size, 16384)


if __name__ == "__main__":
    unittest.main()
