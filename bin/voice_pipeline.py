"""Pure, step-driven voice planning and receipt prototype; performs no audio I/O."""
import hashlib
import json

PRIORITY = {"state": 0, "seal": 1, "narration": 2, "label": 3}


class PipelineError(ValueError):
    pass


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def plan(window):
    if not isinstance(window, dict):
        raise PipelineError("window must be an object")
    if window.get("schema") != "preceptoros.app.voice-window/1":
        raise PipelineError("unsupported window schema")
    if not isinstance(window.get("window_id"), str) or not window["window_id"].strip():
        raise PipelineError("window_id is required")
    items = window.get("visible_items")
    if not isinstance(items, list):
        raise PipelineError("visible_items must be a list")
    if (not isinstance(window.get("visible_count"), int)
            or isinstance(window["visible_count"], bool)):
        raise PipelineError("visible_count is required")
    if window["visible_count"] != len(items):
        raise PipelineError("visible_count does not match visible_items")
    ids = set()
    indexed = []
    for index, item in enumerate(items):
        if (not isinstance(item, dict) or not isinstance(item.get("kind"), str)
                or item["kind"] not in PRIORITY):
            raise PipelineError("visible item has invalid kind")
        item_id, text = item.get("id"), item.get("text")
        if not isinstance(item_id, str) or not item_id or item_id in ids:
            raise PipelineError("visible item id is missing or duplicated")
        if not isinstance(text, str) or not text.strip():
            raise PipelineError("visible item text is empty")
        ids.add(item_id)
        indexed.append((PRIORITY[item["kind"]], index, item))
    ordered = sorted(indexed, key=lambda row: (row[0], row[1], row[2]["id"]))
    inventory_complete = window.get("inventory_complete") is True
    inventory_source = window.get("inventory_source")
    inventory_verified = inventory_complete and isinstance(inventory_source, str) and bool(inventory_source.strip())
    completeness = "CALLER_ATTESTED_COMPLETE" if inventory_verified else "NO_DATA"
    sound_setting = window.get("sound_enabled")
    hardware_setting = window.get("hardware_sound_available")
    sound_ready = sound_setting is True and hardware_setting is True
    causes = []
    if sound_setting is False:
        causes.append("sound disabled by user setting")
    elif sound_setting is not True:
        causes.append("sound setting is unknown")
    if hardware_setting is False:
        causes.append("audio hardware guard disabled")
    elif hardware_setting is not True:
        causes.append("audio hardware availability is unknown")
    if not inventory_verified:
        causes.append("visible inventory is incomplete or unverified")
    ready = sound_ready and inventory_verified
    queue = ([{"id": item["id"], "kind": item["kind"], "text": item["text"],
               "priority": priority, "sequence": sequence}
              for sequence, (priority, _, item) in enumerate(ordered)] if ready else [])
    fallback = [item["text"] for item in items]
    inventory = [{"id": item["id"], "kind": item["kind"], "text": item["text"]} for item in items]
    return {
        "schema": "preceptoros.app.voice-plan/1",
        "window_id": str(window.get("window_id", "")),
        "inventory_sha256": _hash(_canonical(inventory)),
        "inventory_source": inventory_source if inventory_verified else "NO_DATA",
        "completeness": completeness,
        "status": "READY" if ready else "NO_DATA",
        "cause": None if ready else "; ".join(causes),
        "queue": queue,
        "visual_fallback": fallback,
        "motion_mode": ("static" if window.get("reduced_motion") is True else
                        "normal" if window.get("reduced_motion") is False else "NO_DATA"),
        "acoustic_output": "NOT_MEASURED",
    }


def advance(plan_value, prior_receipt, utterance_id, sink_result):
    if plan_value["status"] != "READY":
        raise PipelineError("sound-off plan cannot advance to spoken")
    if prior_receipt is not None and not isinstance(prior_receipt, dict):
        raise PipelineError("prior receipt must be an object")
    prior_rows = [] if prior_receipt is None else prior_receipt.get("receipts", [])
    if not isinstance(prior_rows, list):
        raise PipelineError("prior receipt rows must be a list")
    receipts = list(prior_rows)
    if not _verify_receipts(plan_value, receipts):
        raise PipelineError("prior receipt chain is invalid")
    index = len(receipts)
    if index >= len(plan_value["queue"]):
        raise PipelineError("queue is already complete")
    expected = plan_value["queue"][index]
    if utterance_id != expected["id"]:
        raise PipelineError("utterance is not next in deterministic priority order")
    if sink_result != "completed":
        raise PipelineError("utterance was not acknowledged by the output sink")
    receipt = {"window_id": plan_value["window_id"], "sequence": index,
               "utterance_id": expected["id"], "text": expected["text"],
               "text_sha256": _hash(expected["text"].encode("utf-8")),
               "delivery": "SINK_ACKNOWLEDGED", "acoustic_output": "NOT_MEASURED"}
    receipt["receipt_sha256"] = _hash(_canonical(receipt))
    receipts.append(receipt)
    return {"schema": "preceptoros.app.voice-receipts/1", "receipts": receipts,
            "spoken_claim": False, "acoustic_output": "NOT_MEASURED"}


def verify_receipt_chain(plan_value, result):
    if (not isinstance(result, dict)
            or result.get("schema") != "preceptoros.app.voice-receipts/1"
            or result.get("spoken_claim") is not False
            or result.get("acoustic_output") != "NOT_MEASURED"):
        return False
    return _verify_receipts(plan_value, result.get("receipts"))


def _verify_receipts(plan_value, receipts):
    if not isinstance(receipts, list) or len(receipts) > len(plan_value["queue"]):
        return False
    for index, receipt in enumerate(receipts):
        if not isinstance(receipt, dict):
            return False
        expected = plan_value["queue"][index]
        if (receipt.get("sequence") != index or receipt.get("utterance_id") != expected["id"]
                or receipt.get("window_id") != plan_value["window_id"]
                or receipt.get("text") != expected["text"]
                or receipt.get("text_sha256") != _hash(expected["text"].encode("utf-8"))
                or receipt.get("delivery") != "SINK_ACKNOWLEDGED"
                or receipt.get("acoustic_output") != "NOT_MEASURED"):
            return False
        body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        if receipt.get("receipt_sha256") != _hash(_canonical(body)):
            return False
    return True
