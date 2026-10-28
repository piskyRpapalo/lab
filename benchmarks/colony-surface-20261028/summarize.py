#!/usr/bin/env python3
"""Aggregate the raw frame intervals without losing per-run evidence."""
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence"


def nearest_rank(values, quantile):
    ordered = sorted(values)
    if not ordered:
        return None
    index = max(0, int((quantile * len(ordered) + 0.999999999)) - 1)
    return ordered[index]


def median(values):
    return nearest_rank(values, 0.5)


def read_runs():
    rows = []
    for alias in ("android", "rack"):
        source = EVIDENCE / f"{alias}-samples.json"
        if source.exists():
            payload = json.loads(source.read_text(encoding="utf-8"))
            rows.extend({"device": payload.get("device", alias), **row} for row in payload["results"])
    return rows


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["device"], row["surface"], row["reduced_motion"])].append(row)
    output = []
    for (device, surface, reduced), runs in sorted(groups.items()):
        fps = [1000 / value for run in runs for value in run["frame_interval_ms"] if value > 0]
        pss = [value for run in runs for value in (
            [run.get("process_memory_kb_start"), *run.get("process_memory_kb_samples", []), run.get("process_memory_kb_end")]
        ) if isinstance(value, (int, float))]
        heap = [value for run in runs for value in (
            [run.get("js_heap_start_bytes"), *run.get("js_heap_bytes_samples", []), run.get("js_heap_end_bytes")]
        ) if isinstance(value, (int, float))]
        heap_constant = bool(heap) and len(set(heap)) == 1
        output.append({
            "device": device, "surface": surface, "reduced_motion": reduced,
            "run_count": len(runs), "frame_interval_count": len(fps),
            "fps_median": median(fps), "fps_p05": nearest_rank(fps, 0.05),
            "per_run_fps_median": [run["fps_median"] for run in runs],
            "per_run_fps_p05": [run["fps_p05"] for run in runs],
            "js_heap_sample_count": len(heap),
            "js_heap_median_bytes": None if heap_constant else median(heap),
            "js_heap_max_bytes": None if heap_constant else (max(heap) if heap else None),
            "js_heap_no_data_cause": (
                "Chrome returned the same rounded performance.memory value in every sample; page heap is not resolved"
                if heap_constant else (None if heap else "Chrome did not expose performance.memory on this page")
            ),
            "process_memory_scope": runs[0]["process_memory_scope"],
            "process_memory_sample_count": len(pss),
            "process_memory_median_kb": median(pss),
            "process_memory_min_kb": min(pss) if pss else None,
            "process_memory_max_kb": max(pss) if pss else None,
            "transition_runs_per_repetition": [run["transition_runs"] for run in runs],
            "synthetic_input_cycles_per_repetition": [run["clicks"] for run in runs],
            "viewport_css_px": runs[0]["viewport_css_px"],
            "response_status_per_repetition": [run["response_status"] for run in runs],
        })
    return output


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def weakest_endpoint(summaries, environment):
    by_device = defaultdict(list)
    for row in summaries:
        if row["fps_p05"] is not None:
            by_device[row["device"]].append(row["fps_p05"])
    minima = {device: min(values) for device, values in by_device.items()}
    if not minima:
        measured = {"state": "NO_DATA", "cause": "no FPS sample was completed"}
    else:
        low = min(minima.values())
        devices = sorted(device for device, value in minima.items() if value == low)
        measured = {"state": "MEDIDO", "aliases": devices, "worst_condition_p05_fps": low,
                    "scope": "measured endpoints only; minimum p05 across surface and motion-preference conditions"}
    peers = environment.get("network_census", {}).get("online_network_peer_count")
    uninstrumented_usb = environment.get("android", {}).get("additional_usb_mobile_device_count_without_adb")
    fleet = {"state": "NO_DATA", "cause": "seven network peers expose no browser/CDP sampler; three additional USB mobile devices expose no ADB browser target; the workstation sustained sample lost visibility or focus"}
    fleet["online_network_peer_count"] = peers
    fleet["additional_usb_mobile_without_adb"] = uninstrumented_usb
    return {"weakest_measured_endpoint": measured, "whole_fleet_weakest": fleet}


def main():
    rows = read_runs()
    if not rows:
        raise SystemExit("NO_DATA: no completed samples were found")
    screenshots = []
    for image in sorted(EVIDENCE.glob("*.png")):
        screenshots.append({"file": image.name, "bytes": image.stat().st_size, "sha256": file_sha(image)})
    environment = json.loads((EVIDENCE / "environment.json").read_text(encoding="utf-8"))
    summaries = summarize(rows)
    raw_files = []
    for source in sorted(EVIDENCE.glob("*-samples.json")):
        raw_files.append({"file": source.name, "bytes": source.stat().st_size, "sha256": file_sha(source)})
    live_source = json.loads((EVIDENCE / "live-surface.json").read_text(encoding="utf-8"))
    workstation_failure = json.loads((EVIDENCE / "rack-no-data.json").read_text(encoding="utf-8"))
    app_source = json.loads((EVIDENCE / "app-source.json").read_text(encoding="utf-8"))
    receipt = {
        "schema": "preceptoros.lab.colony-surface-benchmark-summary/1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": {
            "live_surface": "https://preceptoros.org/openworld/",
            "live_source_head": "NO_DATA (the served page does not expose its source commit)",
            "app_fixture_commit": app_source["commit"],
            "app_fixture_tree_sha256": app_source["tree_archive_sha256"],
        },
        "live_document": live_source,
        "protocol": {
            "frame_measure": "requestAnimationFrame callback intervals, reciprocal per interval; nearest-rank p50 and lower-tail p05 pooled over repeated samples",
            "sample_duration_ms": 60000,
            "warmup_ms": 8000,
            "repetitions_per_condition": 2,
            "app_driver": "deterministic Next cycle click every 250 ms; live web passive",
            "reduced_motion": "Chrome DevTools emulation, confirmed with matchMedia on every run",
            "interpretation_limit": "callback cadence does not prove compositor presentation or physical display scanout",
        },
        "environment": environment,
        "runner_provenance": {
            "android_run_file": "measure-android-runner.mjs",
            "android_reconstructed_source_sha256": file_sha(EVIDENCE / "measure-android-runner.mjs"),
            "android_direct_invocation_hash": "NO_DATA (the source file digest was not captured at process start)",
            "android_source_note": "reconstructed from the pre-run version by reversing the later recorded harness patches; direct invocation hashing was omitted",
            "android_command": "node benchmarks/colony-surface-20261028/measure.mjs --device=android --duration-ms=60000 --repeat=2 --output=benchmarks/colony-surface-20261028/evidence",
            "future_phase_runner_file": "measure.mjs",
            "future_phase_runner_sha256": file_sha(ROOT / "measure.mjs"),
            "summary_file": "summarize.py",
            "summary_sha256": file_sha(ROOT / "summarize.py"),
        },
        "summaries": summaries,
        "weakest_endpoint": weakest_endpoint(summaries, environment),
        "raw_files": raw_files,
        "other_endpoint_attempts": workstation_failure,
        "screenshots": screenshots,
    }
    target = EVIDENCE / "receipt.json"
    target.write_text(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": target.name, "bytes": target.stat().st_size, "sha256": file_sha(target), "conditions": len(receipt["summaries"])}, sort_keys=True))


if __name__ == "__main__":
    main()
