#!/usr/bin/env python3
"""Format a measured receipt into a privacy-safe ~150-word plain-text log.

The receipt is the post (ideas20oct §2): silicon drafts from measured
figures only; the Sovereign reviews, signs (FIRMO), and publishes.
Usage:
  python3 bin/format_receipt.py RECEIPT.json [--words 150]
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

CEILING_WORDS = 150

# ---------------------------------------------------------------------------
# Privacy-safe sanitization patterns
# ---------------------------------------------------------------------------

# Private filesystem paths that must never appear in public output
_PRIVATE_PATH_PATTERNS = [
    re.compile(r"/home/[a-zA-Z0-9_]+/\.ssh", re.IGNORECASE),
    re.compile(r"/home/[a-zA-Z0-9_]+/\.gnupg", re.IGNORECASE),
    re.compile(r"/home/[a-zA-Z0-9_]+/\.config/", re.IGNORECASE),
    re.compile(r"/root/", re.IGNORECASE),
    re.compile(r"/etc/shadow", re.IGNORECASE),
    re.compile(r"/etc/passwd", re.IGNORECASE),
    re.compile(r"private-mesa", re.IGNORECASE),
    re.compile(r"no-publicar", re.IGNORECASE),
]

# Credential-like patterns
_CREDENTIAL_PATTERNS = [
    re.compile(r"password\s+(?:is|==|=|:)\s*\S+", re.IGNORECASE),
    re.compile(r"password\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"api[_\-]?key\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"token\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"secret\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"credential\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9\-_\.]+", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9\-_]+", re.IGNORECASE),
    re.compile(r"eyJ[A-Za-z0-9\-_]+", re.IGNORECASE),  # JWT-like
    re.compile(r"ghp_[A-Za-z0-9]+", re.IGNORECASE),    # GitHub personal token
    re.compile(r"token_synthetic", re.IGNORECASE),
]

# Private network identifiers
_PRIVATE_NET_PATTERNS = [
    re.compile(r"\b192\.168\.\d+\.\d+\b"),
    re.compile(r"\b10\.\d+\.\d+\.\d+\b"),
    re.compile(r"\b172\.(1[6-9]|2\d|3[01])\.\d+\.\d+\b"),
    re.compile(r"\blocalhost:\d+\b"),
]

# Hostname patterns that look private
_PRIVATE_HOST_PATTERNS = [
    re.compile(r"node-internal", re.IGNORECASE),
    re.compile(r"node-secret", re.IGNORECASE),
    re.compile(r"internal-", re.IGNORECASE),
]


def _has_sensitive(value: str) -> bool:
    """Return True if *value* contains any sensitive pattern."""
    if not isinstance(value, str):
        return False
    for pat in _PRIVATE_PATH_PATTERNS + _CREDENTIAL_PATTERNS + _PRIVATE_NET_PATTERNS:
        if pat.search(value):
            return True
    return False


def _has_private_host(value: str) -> bool:
    """Return True if *value* looks like a private hostname."""
    if not isinstance(value, str):
        return False
    for pat in _PRIVATE_HOST_PATTERNS:
        if pat.search(value):
            return True
    return False


def _sanitize(value, allow_host: bool = True) -> str:
    """Sanitize a single value for public output.

    Returns the original value if safe, otherwise 'NO_DATA'.
    Never echoes the rejected value.

    When allow_host=False (machine fields), private hostnames are always rejected.
    When allow_host=True (general fields), private hostnames pass through.
    """
    if value is None:
        return "NO_DATA"
    if not isinstance(value, str):
        # Non-string values (int, float, bool) are safe to stringify
        s = str(value)
    else:
        s = value

    # Check for sensitive content
    if _has_sensitive(s):
        return "NO_DATA"

    # Check for private hostnames — reject when this is a machine field
    if not allow_host and _has_private_host(s):
        return "NO_DATA"

    return s


def _truncate_words(text: str, max_words: int = 40) -> str:
    """Truncate *text* to at most *max_words* words to control output size."""
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "..."
    return text


def _safe_field(value, max_words: int = 40, allow_host: bool = True) -> str:
    """Sanitize and truncate a field value for public output."""
    s = _sanitize(value, allow_host=allow_host)
    return _truncate_words(s, max_words)


def format_harness_receipt(r: dict) -> str:
    suite = _safe_field(r.get("suite", "NO_DATA"))
    verdict = _safe_field(r.get("verdict", "NO_DATA"))
    cov = r.get("coverage", 0)
    total = r.get("total", 0)
    det = r.get("determinism", False)
    weight = r.get("weight_b", 0)
    speed = r.get("speed_s", 0)
    sha = _safe_field(r.get("sha256", "NO_DATA"))
    machine = _safe_field(
        r.get("runtime", {}).get("machine", "NO_DATA"),
        allow_host=False,
    )
    date = _safe_field(r.get("observed_at", "NO_DATA"))
    py = _safe_field(r.get("runtime", {}).get("python", "NO_DATA"))
    schema = _safe_field(r.get("schema", "NO_DATA"))
    det_txt = "deterministic across both runs" if det else "NOT deterministic"
    return (
        f"Harness receipt · {suite} · verdict {verdict} · {date}. "
        f"Coverage {cov}/{total} tests passed. {det_txt}. "
        f"Weight {weight} B. Runtime {speed} s per pass. "
        f"Machine {machine} · Python {py}. "
        f"Schema {schema}. "
        f"Receipt sha256 {sha}. "
        f"Privacy: counts only; no test names, no output, no prompts. "
        f"Drafted by silicon from measured figures; pending Sovereign sign-off (FIRMO)."
    )


def format_yardstick_receipt(r: dict) -> str:
    state = _safe_field(r.get("state", "NO_DATA"))
    # Handle empty state -> NO_DATA
    if not state or state == "":
        state = "NO_DATA"
    runs = r.get("runs", [])
    date = _safe_field(r.get("observed_at", "NO_DATA"))
    cmd = _safe_field(r.get("command", "NO_DATA"))
    machine = _safe_field(
        r.get("runtime", {}).get("machine", "NO_DATA"),
        allow_host=False,
    )
    py = _safe_field(r.get("runtime", {}).get("python", "NO_DATA"))
    schema = _safe_field(r.get("schema", "NO_DATA"))
    parts = []
    for i, run in enumerate(runs):
        parts.append(
            f"run {i + 1}: {run.get('state', 'NO_DATA')} "
            f"{run.get('passed', 0)}/{run.get('tests', 0)} passed "
            f"in {run.get('elapsed_s', 0)} s"
        )
    runs_txt = "; ".join(parts) if parts else "NO_DATA"
    cause = r.get("cause")
    cause_safe = _safe_field(cause) if cause else None
    cause_txt = f" Cause: {cause_safe}." if cause_safe else ""
    return (
        f"Yardstick receipt · state {state} · {date}. "
        f"Command: {cmd}. {runs_txt}.{cause_txt} "
        f"Machine {machine} · Python {py}. "
        f"Schema {schema}. "
        f"Privacy: counts only; test names, stdout, stderr, prompts and answers omitted. "
        f"Drafted by silicon from measured figures; pending Sovereign sign-off (FIRMO)."
    )


def format_receipt_dict(r: dict) -> str:
    """Format a receipt dict directly (without reading from file)."""
    schema = r.get("schema", "")
    if "harness-receipt" in str(schema):
        return format_harness_receipt(r)
    if "yardstick-receipt" in str(schema):
        return format_yardstick_receipt(r)
    state = _safe_field(r.get("state", r.get("verdict", "NO_DATA")))
    date = _safe_field(r.get("observed_at", "NO_DATA"))
    schema_safe = _safe_field(schema, allow_host=True)
    return (
        f"Receipt · schema {schema_safe or 'NO_DATA'} · observed {date}. "
        f"State {state}. "
        f"Drafted by silicon; pending Sovereign sign-off (FIRMO)."
    )


def format_receipt(path: str) -> str:
    r = json.loads(Path(path).read_text(encoding="utf-8"))
    return format_receipt_dict(r)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("receipt", help="path to a JSON receipt")
    ap.add_argument("--words", type=int, default=CEILING_WORDS,
                    help="soft ceiling for the drafted log (default 150)")
    args = ap.parse_args(argv)
    text = format_receipt(args.receipt)
    words = len(text.split())
    print(text)
    print(f"\n---\nwords: {words} (soft ceiling {args.words})", file=sys.stderr)
    return 0 if words <= args.words * 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
