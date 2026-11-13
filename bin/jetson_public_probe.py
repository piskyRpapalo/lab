#!/usr/bin/env python3
"""Small owned node-d public experiment around the existing throughput runner.

Injected runner/scorer are pinned LAB sources. No model install, service or power
command. Only the sampler process started here is terminated. Sensor peaks are
sampled host-wide lower bounds; no process GPU attribution or capacity claim.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone


def read(path, limit=8192):
    try:
        with open(path) as stream:
            return stream.read(limit)
    except Exception:
        return None


def memory():
    raw = read('/proc/meminfo') or ''
    return {k: int(v)*1024 for k,v in re.findall(r'^(MemTotal|MemAvailable|SwapFree):\s+(\d+) kB$', raw, re.M)}


def temperatures():
    result = []
    for path in Path('/sys/class/thermal').glob('thermal_zone*/temp'):
        try:
            value = int(read(path, 128))
            if -40000 <= value <= 150000:
                result.append(value)
        except (TypeError, ValueError):
            pass
    return result


def parse_tegrastats(line):
    """Known field units only; absent/ambiguous fields stay absent, never zero."""
    row = {}
    gpu = re.search(r'\bGR3D_FREQ\s+(\d+)%', line)
    ram = re.search(r'\bRAM\s+(\d+)/(\d+)MB', line)
    power = re.search(r'\bVDD_IN\s+(\d+)(?:mW)?/(\d+)(?:mW)?\b', line)
    if gpu and 0 <= int(gpu[1]) <= 100:
        row['gpu_util_pct'] = int(gpu[1])
    if ram:
        # Vendor MB field retained literally; avoid silently choosing SI vs MiB.
        row['ram_vendor_MB'] = int(ram[1])
    if power:
        row['vdd_in_mw'] = int(power[1])
    return row


def run(runner, grade, raw, model, digest, *, source, stop=lambda: False):
    observed = datetime.now(timezone.utc).isoformat()
    runner.public_input(raw)
    if runner.model_digest(runner.request('/api/tags'), model) != digest:
        raise ValueError('identity_changed')
    def residents():
        # This metadata read is deliberately separate from the old runner's routes.
        import urllib.request
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), runner.NoRedirect())
        with opener.open('http://127.0.0.1:11434/api/ps', timeout=3) as response:
            data = runner.strict_json(response.read(65537))
        if type(data) is not dict or type(data.get('models')) is not list:
            raise ValueError('resident_metadata_missing')
        return data['models']
    before, temps = memory(), temperatures()
    # Conservative operator ceilings for this experiment, not calibrated admission limits.
    ceilings = {'min_available_bytes': 4*1024**3, 'max_temp_millic': 70000,
                'max_load_1': 1.0, 'max_generations': 2, 'per_request_timeout_s': 25,
                'total_window_s': 65, 'sensor_interval_ms': 200}
    if (stop() or residents() or before.get('MemAvailable', 0) < ceilings['min_available_bytes']
            or not temps or max(temps) >= ceilings['max_temp_millic']
            or os.getloadavg()[0] > ceilings['max_load_1']):
        return {'state': 'NO_DATA', 'cause': 'measurement_window_not_idle_or_safe', 'model_calls': 0}
    if not shutil.which('tegrastats'):
        return {'state': 'NO_DATA', 'cause': 'sensor_observer_missing', 'model_calls': 0}
    observer = subprocess.Popen(['tegrastats', '--interval', '200'], stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True)
    done, rows, phases = threading.Event(), [], {'value': 'idle'}
    failed, calls, quality = [False], [], []
    start = time.monotonic()

    def consume():
        for line in observer.stdout:
            if len(rows) < 400:
                rows.append({'phase': phases['value'], 'elapsed_s': round(time.monotonic()-start, 3),
                             **parse_tegrastats(line)})
    def monitor():
        while not done.wait(.2):
            m, t = memory(), temperatures()
            if len(host_rows) < 400:
                host_rows.append({'phase': phases['value'], 'available_bytes': m.get('MemAvailable'),
                                  'max_temp_millic': max(t) if t else None})
            if (stop() or not t or max(t) >= ceilings['max_temp_millic']
                    or m.get('MemAvailable', 0) < 1024**3
                    or time.monotonic()-start > ceilings['total_window_s']):
                failed[0] = True
    host_rows = []
    sensor_thread = threading.Thread(target=consume, daemon=True)
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    sensor_thread.start(); monitor_thread.start()
    try:
        time.sleep(1.2)  # Bounded idle baseline, no model call.
        if not any('gpu_util_pct' in r for r in rows) or any(r.get('gpu_util_pct', 0) > 0 for r in rows):
            return {'state': 'NO_DATA', 'cause': 'idle_gpu_not_observed', 'model_calls': 0}
        if observer.poll() is not None:
            return {'state': 'NO_DATA', 'cause': 'observer_stopped', 'model_calls': 0}
        phases['value'] = 'execution'
        def call(path, body=None):
            if path != '/api/generate':
                return runner.request(path, body)
            if failed[0] or stop() or len(calls) >= 2:
                raise ValueError('measurement_cancelled_no_retry')
            active = residents()
            if active:
                # Never unload/displace a resident model or join someone else's session.
                failed[0] = True
                raise ValueError('measurement_window_lost')
            calls.append(time.monotonic())
            try:
                # Same public runner controls, including its normal keep_alive=0 lifecycle.
                import urllib.request
                request = urllib.request.Request('http://127.0.0.1:11434/api/generate',
                    data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), runner.NoRedirect())
                with opener.open(request, timeout=ceilings['per_request_timeout_s']) as response:
                    value = runner.strict_json(response.read(1048577))
                quality.append(grade(value.get('response', ''), raw))
                return value
            except Exception:
                failed[0] = True  # Unknown completion never triggers a further generation.
                raise
        result = runner.run_public(model, raw, call=call, source=source)
        phases['value'] = 'post'
        time.sleep(.4)
        def summary(phase):
            selected = [r for r in rows if r['phase'] == phase]
            out = {'samples': len(selected)}
            for key in ('gpu_util_pct', 'ram_vendor_MB', 'vdd_in_mw'):
                values = [r[key] for r in selected if key in r]
                out[key] = {'min': min(values), 'max': max(values), 'mean': round(sum(values)/len(values), 3)} if values else runner.no_data('sensor_field_not_reported')
            return out
        available = [r['available_bytes'] for r in host_rows if type(r['available_bytes']) is int]
        maxima = [r['max_temp_millic'] for r in host_rows if type(r['max_temp_millic']) is int]
        result['model_name'] = 'model-ref-' + hashlib.sha256(model.encode()).hexdigest()[:16]
        out = {'schema': 'preceptoros.lab.node-metadata/1', 'kind': 'public-resource-experiment',
            'node': 'node-d', 'observed_at': observed, 'state': 'VERIFIED' if result['state']=='MEASURED' and not failed[0] else 'NO_DATA',
            'scope': 'two_public_fixture_attempts_not_task_capacity', 'model_version': digest,
            'model_calls': len(calls), 'experiment_policy': ceilings, 'throughput': result,
            'quality': {'scorer': 'existing_grade_public_csv', 'grades': quality,
                        'distinct_cases': 1, 'independent_holdout': runner.no_data('single_public_fixture')},
            'resources': {'memory_scope': 'host_shared_RAM_not_process_or_GPU_peak',
                          'before_available_bytes': before.get('MemAvailable'),
                          'minimum_sampled_available_bytes': min(available) if available else None,
                          'max_sampled_temp_millic': max(maxima) if maxima else None,
                          'idle': summary('idle'), 'execution': summary('execution')},
            'GPU_attribution': runner.no_data('global_activity_not_process_execution_attribution'),
            'TTFT': runner.no_data('nonstreaming_profile'),
            'process_peak_memory': runner.no_data('process_sampler_not_present'),
            'concurrency_admission': runner.no_data('not_calibrated_PSI_unavailable'),
            'energy_joules': runner.no_data('short_sampled_rail_power_not_integrated_energy'),
            'settings_changed': False,
            'limitations': ['Service-reported digest and counters, no rehash of weight bytes.',
                'Sampled maxima are lower bounds; host activity is not process attribution.',
                'Normal runner keep_alive=0 applies only to the newly loaded owned model.',
                'No training/admission profile is inferred from these two attempts.']}
        out['experiment_ref'] = hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        return out
    finally:
        done.set()
        observer.terminate()  # Only this observer, never global tegrastats --stop.
        try: observer.wait(timeout=2)
        except subprocess.TimeoutExpired: observer.kill(); observer.wait(timeout=2)
        sensor_thread.join(timeout=2); monitor_thread.join(timeout=2)
