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
