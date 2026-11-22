"""G0 experimental statistical lens: discrete competing risks, not a new runner.

This is pure math on caller-provided terminal labels. It does not evaluate model
text, authenticate a witness, attest effects, choose a preregistered endpoint,
or prove that any event is real. Feed only separately validated trajectories.
"""
from collections import Counter
from fractions import Fraction

CAUSES = ("COMPROMISED", "OVER_REFUSED", "DEGRADED", "INFRA_BLOCKED")
CENSOR = "CENSORED"
FIELDS = frozenset(("trajectory_id", "turn", "state", "stratum"))


def _checked(records):
    if type(records) is not list or not records:
        raise ValueError("empty_cohort")
    if any(
        type(row) is not dict or set(row) != FIELDS
        or type(row["trajectory_id"]) is not str or not row["trajectory_id"]
        or len(row["trajectory_id"]) > 80
        or type(row["turn"]) is not int or row["turn"] < 1
        or row["turn"] > 50 or row["state"] not in (*CAUSES, CENSOR)
        or type(row["stratum"]) is not str or not row["stratum"]
        for row in records
    ):
        raise ValueError("invalid_trajectory")
    if len({row["trajectory_id"] for row in records}) != len(records):
        raise ValueError("duplicate_trajectory")
    if len({row["stratum"] for row in records}) != 1:
        raise ValueError("mixed_stratum")
    return records


def descriptive_cif(records):
    """Aalen-Johansen CIF point estimate by first terminal cause.

    For each discrete turn t: F_k(t) += S(t-) * d_k(t) / Y(t).
    Aalen-Johansen handles competing outcomes; right-censoring is not a
    successful task. Missing observations and witness integrity MUST be
    resolved upstream, not silently inferred from a label.
    """
    rows = _checked(records)
    survival = Fraction(1)
    cumulative = {cause: Fraction(0) for cause in CAUSES}
    risk_table = []
    for turn in range(1, max(row["turn"] for row in rows) + 1):
        at_risk = sum(row["turn"] >= turn for row in rows)
        if not at_risk:
            continue
        events = Counter(
            row["state"] for row in rows if row["turn"] == turn
        )
        for cause in CAUSES:
            cumulative[cause] += (
                survival * Fraction(events[cause], at_risk)
            )
        survival *= Fraction(
            at_risk - sum(events[cause] for cause in CAUSES), at_risk
        )
        risk_table.append({
            "turn": turn,
            "at_risk": at_risk,
            "right_censored": events[CENSOR],
            "events": {cause: events[cause] for cause in CAUSES},
        })
    return {
        "cif": cumulative,
        "event_free_probability": survival,
        "risk_table": risk_table,
        "authority": "none",
        "evidence": "CALLER_SUPPLIED_NOT_ATTESTED",
    }


def wrong_one_minus_km_for_comparison(records, target):
    """Deliberately naive 1-KM, treating other causes as censored.

    Retained only to report competing-risk bias. Never present as the CIF.
    """
    rows = _checked(records)
    if target not in CAUSES:
        raise ValueError("unknown_target")
    survival = Fraction(1)
    for turn in range(1, max(row["turn"] for row in rows) + 1):
        at_risk = sum(row["turn"] >= turn for row in rows)
        target_events = sum(
            row["turn"] == turn and row["state"] == target
            for row in rows
        )
        if at_risk:
            survival *= Fraction(at_risk - target_events, at_risk)
    return 1 - survival


def cohen_kappa_binary(matrix):
    """Return exact kappa, observed agreement, expected agreement.

    Matrix rows: judge A labels; columns: judge B labels. Labels and
    marginal names must be recorded with the matrix by the caller.
    """
    if (type(matrix) is not list or len(matrix) != 2
            or any(
                type(row) is not list or len(row) != 2
                or any(type(value) is not int or value < 0 for value in row)
                for row in matrix
            )):
        raise ValueError("invalid_matrix")
    n = sum(map(sum, matrix))
    if n == 0:
        raise ValueError("empty_matrix")
    observed = Fraction(matrix[0][0] + matrix[1][1], n)
    expected = Fraction(
        sum(
            sum(matrix[i]) * sum(matrix[j][i] for j in range(2))
            for i in range(2)
        ), n * n
    )
    return {
        "kappa": None if expected == 1 else (
            (observed - expected) / (1 - expected)
        ),
        "observed_agreement": observed,
        "expected_agreement": expected,
        "authority": "none",
        "evidence": "CALLER_SUPPLIED_NOT_ATTESTED",
    }


# Experimental design pins, not an executor or trusted source of outcomes.
STUDY_ARMS = ("A", "B", "C")
STUDY_STRATA = ("benign", "hybrid", "attack")
STUDY_SENSOR_FIELDS = (
    "sensor_base_ref", "sensor_weights_ref",
    "sensor_protocol_ref", "sensor_schema_ref",
)
STUDY_PIN_FIELDS = frozenset((
    "case_ref", "repeat", "arm", "stratum", "gold_ref",
    "main_model_ref", "main_protocol_ref", "generation_budget",
    "seed", "host_ref", "feedback_table_ref", *STUDY_SENSOR_FIELDS,
))


def preflight_three_arm_design(rows):
    """Check static pairing A=no sensor, B=base sensor, C=tuned sensor.

    Checks equality of declared hashes and controls, not the legitimacy of
    the human gold, sensor training, execution witness, or registration time.
    Always returns NO_DATA on structural success: no evidence of actual runs.
    Per-host batches only; keep different hardware in distinct comparisons.
    """
    def outcome(state, cause, *, group_count=0, strata=None):
        return {
            "schema": "preceptoros.lab.study-three-arm-preflight/1",
            "state": state, "cause": cause,
            "structure_valid": state == "NO_DATA",
            "paired_groups": group_count,
            "strata": strata or {},
            "authority": "none",
            "evidence": "DECLARED_HASHES_NOT_ATTESTED",
        }

    def digest(value):
        return (type(value) is str and len(value) == 64
                and all(c in "0123456789abcdef" for c in value))

    if type(rows) is not list or not 3 <= len(rows) <= 4000:
        return outcome("EVAL_INVALID", "invalid_cohort_size")
    if any(type(row) is not dict or set(row) != STUDY_PIN_FIELDS
           for row in rows):
        return outcome("EVAL_INVALID", "invalid_row_schema")

    digest_fields = (
        "case_ref", "gold_ref", "main_model_ref", "main_protocol_ref",
        "host_ref", "feedback_table_ref",
    )
    for row in rows:
        if (not all(digest(row[key]) for key in digest_fields)
                or row["arm"] not in STUDY_ARMS
                or row["stratum"] not in STUDY_STRATA
                or type(row["repeat"]) is not int
                or not 0 <= row["repeat"] <= 9
                or type(row["seed"]) is not int
                or not 0 <= row["seed"] < 2**63
                or type(row["generation_budget"]) is not int
                or not 1 <= row["generation_budget"] <= 8192):
            return outcome("EVAL_INVALID", "invalid_pin")

        sensor_values = [row[key] for key in STUDY_SENSOR_FIELDS]
        if row["arm"] == "A":
            if any(value is not None for value in sensor_values):
                return outcome("EVAL_INVALID", "baseline_has_sensor")
        elif not all(digest(value) for value in sensor_values):
            return outcome("EVAL_INVALID", "missing_sensor_pin")

    # A model/host/protocol/feedback transition requires a different cohort.
    global_pins = ("main_model_ref", "main_protocol_ref",
                   "generation_budget", "host_ref", "feedback_table_ref")
    for field in global_pins:
        if len({row[field] for row in rows}) != 1:
            return outcome("EVAL_INVALID", "cohort_pin_drift_" + field)

    groups = {}
    for row in rows:
        key = (row["case_ref"], row["repeat"])
        if key not in groups:
            groups[key] = {}
        if row["arm"] in groups[key]:
            return outcome("EVAL_INVALID", "duplicate_arm_in_group")
        groups[key][row["arm"]] = row

    strata = {}
    paired_fields = (
        "case_ref", "repeat", "stratum", "gold_ref",
        "main_model_ref", "main_protocol_ref", "generation_budget",
        "seed", "host_ref", "feedback_table_ref",
    )
    for group in groups.values():
        if set(group) != set(STUDY_ARMS):
            return outcome("EVAL_INVALID", "incomplete_three_arm_group")
        a, b, c = (group[arm] for arm in STUDY_ARMS)
        if any(len({row[field] for row in (a, b, c)}) != 1
               for field in paired_fields):
            return outcome("EVAL_INVALID", "paired_control_drift")
        if any(b[field] != c[field] for field in (
                "sensor_base_ref", "sensor_protocol_ref",
                "sensor_schema_ref")):
            return outcome("EVAL_INVALID", "sensor_contract_drift")
        if b["sensor_weights_ref"] == c["sensor_weights_ref"]:
            return outcome("EVAL_INVALID", "sensor_weights_not_distinct")
        strata[a["stratum"]] = strata.get(a["stratum"], 0) + 1

    # A SHA is an integrity identifier, NOT human gold or authorization.
    return outcome(
        "NO_DATA", "structure_only_gold_witness_prereg_unverified",
        group_count=len(groups), strata=strata,
    )


# G2: descriptive matched-cluster spread. NOT a confidence interval or
# replacement for a prespecified, independently reviewed variance estimator.
STUDY_CLUSTER_FIELDS = frozenset((
    "case_ref", "repeat", "arm", "stratum", "turn", "state", "horizon",
))


def paired_cluster_spread(
    records, *, target, reference_arm="A", treatment_arm="C",
    draws=128, seed=0,
):
    """Diagnostic resampling of entire cases, keeping A/B/C and repeats together.

    An entire fixture/case is the sampled unit; turns and repeats are not
    independent trials. Outputs are descriptive percentiles of a resampling
    distribution, NOT calibrated confidence intervals or independent gold.
    Terminal causes are caller-supplied and not independently authenticated.

    Early administrative censoring is forbidden here: its reasons cannot be
    expressed in this small terminal-only input schema. Refuse rather than
    silently assume independent censoring. This is not a runner or witness.
    """
    from random import Random

    if (target not in CAUSES or reference_arm not in STUDY_ARMS
            or treatment_arm not in STUDY_ARMS
            or reference_arm == treatment_arm):
        raise ValueError("invalid_contrast")
    if (type(draws) is not int or not 32 <= draws <= 512
            or type(seed) is not int or not 0 <= seed < 2**32):
        raise ValueError("invalid_resampling_budget")
    if type(records) is not list or not 9 <= len(records) <= 4000:
        raise ValueError("invalid_cohort_size")

    def _digest(value):
        return (type(value) is str and len(value) == 64
                and all(char in "0123456789abcdef" for char in value))

    groups = {}
    strata, horizons = set(), set()
    for row in records:
        if type(row) is not dict or set(row) != STUDY_CLUSTER_FIELDS:
            raise ValueError("invalid_row_shape")
        if (not _digest(row["case_ref"])
                or row["arm"] not in STUDY_ARMS
                or row["stratum"] not in STUDY_STRATA
                or row["state"] not in (*CAUSES, CENSOR)
                or type(row["repeat"]) is not int
                or not 0 <= row["repeat"] <= 9
                or type(row["horizon"]) is not int
                or row["horizon"] not in (5, 12)
                or type(row["turn"]) is not int
                or not 1 <= row["turn"] <= row["horizon"]):
            raise ValueError("invalid_row_value")
        if row["state"] == CENSOR and row["turn"] != row["horizon"]:
            raise ValueError("early_censor_reason_not_represented")
        key = (row["repeat"], row["arm"])
        case = groups.setdefault(row["case_ref"], {})
        if key in case:
            raise ValueError("duplicate_case_repeat_arm")
        case[key] = row
        strata.add(row["stratum"])
        horizons.add(row["horizon"])

    if len(strata) != 1 or len(horizons) != 1:
        raise ValueError("mixed_stratum_or_horizon")
    if len(groups) < 3:
        raise ValueError("insufficient_case_clusters")
    expected_repeats = None
    for case in groups.values():
        repeats = {key[0] for key in case}
        if (not repeats or set(case) != {
                (repeat, arm) for repeat in repeats for arm in STUDY_ARMS}):
            raise ValueError("incomplete_three_arm_case")
        if expected_repeats is None:
            expected_repeats = repeats
        elif repeats != expected_repeats:
            raise ValueError("unequal_repeat_sets_between_cases")

    ordered = sorted(groups)
    repeats_sorted = sorted(expected_repeats)

    def _estimate(selection):
        per_arm = {reference_arm: [], treatment_arm: []}
        for slot, case_ref in enumerate(selection):
            case = groups[case_ref]
            for repeat in repeats_sorted:
                for arm in per_arm:
                    row = case[(repeat, arm)]
                    per_arm[arm].append({
                        "trajectory_id": f"{slot}-{repeat}-{arm}",
                        "turn": row["turn"],
                        "state": row["state"],
                        "stratum": row["stratum"],
                    })
        return (descriptive_cif(per_arm[treatment_arm])["cif"][target]
                - descriptive_cif(per_arm[reference_arm])["cif"][target])

    point = _estimate(ordered)
    rng = Random(seed)
    sample = sorted(
        _estimate([ordered[rng.randrange(len(ordered))]
                   for _ in ordered])
        for _ in range(draws)
    )

    def _percentile(numerator, denominator):
        position = Fraction((draws - 1) * numerator, denominator)
        low = position.numerator // position.denominator
        high = min(low + 1, draws - 1)
        weight = position - low
        return sample[low] * (1 - weight) + sample[high] * weight

    return {
        "schema": "preceptoros.lab.paired-cluster-spread/1",
        "state": "DESCRIPTIVE_ONLY",
        "target": target,
        "reference_arm": reference_arm,
        "treatment_arm": treatment_arm,
        "point_difference": point,
        "resampling_p025": _percentile(1, 40),
        "resampling_p975": _percentile(39, 40),
        "sampled_unit": "entire_case_A_B_C_with_repeats",
        "case_clusters": len(groups),
        "repeats_per_case": len(repeats_sorted),
        "draws": draws,
        "seed": seed,
        "authority": "none",
        "evidence": "CALLER_SUPPLIED_NOT_ATTESTED",
        "coverage": "NO_DATA(no_preregistered_calibration_or_independent_gold)",
    }
