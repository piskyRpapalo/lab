"""LAB-only inference evidence adapter. No network, authority, or model lifecycle."""
import datetime
import hashlib
import math
import re

from .reuse import instrument

HEX = re.compile(r"[0-9a-f]{64}")
LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}")
MAX_NS = 10**18


def _digest(value):
    return type(value) is str and HEX.fullmatch(value) is not None


def _integer(value, low=1, high=MAX_NS):
    return type(value) is int and low <= value <= high


def _stamp(value):
    if type(value) is not str or len(value) > 40:
        return False
    try:
        stamp = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return stamp.tzinfo is not None
    except ValueError:
        return False


def _unknown(cause):
    return {"state": "NO_DATA", "cause": cause}


def normalize(engine, response, *, model, pinned_digest, before_digest, after_digest,
              wall_ns, observed_at, evidence_ref, origin, memory_bytes=None):
    """Normalize an existing completed turn; input is host-owned, not model authority.

    Digests are reported by the caller, not attested by this function. The caller
    must establish same engine, artifact, request, session and provenance.
    Never promotes a result to COMPLETED_VERIFIED or persists response text.
    """
    if engine not in ("ollama", "llama.cpp"):
        return _unknown("engine_unsupported")
    if origin not in ("fixture", "observed") or not _stamp(observed_at) or not _digest(evidence_ref):
        return _unknown("observation_unbound")
    if (type(model) is not str or not LABEL.fullmatch(model)
            or model.lower().endswith(":cloud") or not _digest(pinned_digest)
            or before_digest != pinned_digest or after_digest != pinned_digest):
        return _unknown("model_pin_unconfirmed")
    if not _integer(wall_ns):
        return _unknown("wall_time_unmeasured")
    if (type(response) is not dict or response.get("model") != model
            or any(response.get(k) for k in ("remote_model", "remote_host", "error"))):
        return _unknown("response_model_unconfirmed")
    try:
        if engine == "ollama":
            if not _integer(response.get("eval_count")) or not _integer(response.get("eval_duration")):
                return _unknown("generation_timing_unmeasured")
            answer = response.get("response")
            if type(answer) is not str or not answer.strip() or len(answer.encode()) > 65536:
                return _unknown("response_invalid")
            metrics = instrument("throughput").sample(response, model, wall_ns)
            count = metrics["eval_count"]
            rate = metrics["generation_tokens_per_s"]
            answer_hash = metrics["response_sha256"]
        else:
            answer = response.get("content")
            timings = response.get("timings")
            if response.get("stop") is not True or type(answer) is not str or not answer.strip():
                return _unknown("response_incomplete")
            if len(answer.encode()) > 65536 or type(timings) is not dict:
                return _unknown("response_invalid")
            count, millis = timings.get("predicted_n"), timings.get("predicted_ms")
            if (not _integer(count) or type(millis) not in (int, float)
                    or not 0.001 <= millis <= MAX_NS / 1000000):
                return _unknown("generation_timing_unmeasured")
            rate = round(count * 1000 / millis, 6)
            answer_hash = hashlib.sha256(answer.encode()).hexdigest()
        if not math.isfinite(rate) or rate <= 0:
            return _unknown("generation_timing_unmeasured")
    except (ValueError, TypeError, KeyError, OverflowError, UnicodeError):
        return _unknown("response_invalid")
    # Deliberately neither an execution receipt nor an Acho LIVE assertion.
    return {"state": "SIMULATED" if origin == "fixture" else "REPORTED",
            "cause": "independent_witness_not_checked",
            "source": engine, "observed_at": observed_at, "evidence_ref": evidence_ref,
            "model": model, "model_digest": pinned_digest,
            "metrics": {"wall_ms": round(wall_ns / 1000000, 6), "generation_tokens": count,
                        "generation_tokens_per_s": rate,
                        "memory_bytes": memory_bytes if _integer(memory_bytes) else
                        _unknown("model_memory_not_measured")},
            "response_sha256": answer_hash,
            "execution_authorized": False, "completion_verified": False}


def reader_fields(record):
    """Semantic input for H's existing Acho emitter, not a parallel frame protocol."""
    record = record if type(record) is dict else {}
    state = record.get("state")
    if state not in ("SIMULATED", "REPORTED"):
        cause = record.get("cause")
        if type(cause) is not str or not re.fullmatch(r"[a-z_]{1,64}", cause):
            cause = "inference_evidence_unavailable"
        return {"state": "NO_DATA", "cause": cause, "seal": "NO_DATA",
                "r": "Local inference evidence unavailable: " + cause.replace("_", " ") + ".",
                "sound": "NO_DATA", "soundCause": "sound_not_measured"}
    return {"state": state, "cause": "independent_witness_not_checked",
            "source": record.get("source"), "observed_at": record.get("observed_at"),
            "evidence_ref": record.get("evidence_ref"),
            "seal": "SIMULATED" if state == "SIMULATED" else "NO_DATA",
            "r": ("Synthetic inference fixture; no physical model ran." if state == "SIMULATED"
                  else "Local inference counters reported; independent witness not checked."),
            "sound": "NO_DATA", "soundCause": "sound_not_measured"}
