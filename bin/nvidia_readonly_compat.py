#!/usr/bin/env python3
"""Narrow installed-stack observation. No inference, engine loading or settings."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

PACKAGES = ['nvidia-l4t-core', 'nvidia-jetpack', 'cuda-cudart-*', 'cuda-runtime-*', 'libnvinfer*']


def nd(cause):
    return {'state': 'NO_DATA', 'cause': cause}


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def command(args):
    env = {k: v for k, v in os.environ.items() if not k.lower().endswith('_proxy')}
    env['OLLAMA_HOST'] = 'http://127.0.0.1:11434'
    try:
        result = subprocess.run(args, capture_output=True, timeout=4, env=env)
        if len(result.stdout) + len(result.stderr) > 65536:
            return None
        # dpkg can return1 for a missing optional package while listing others.
        return result.stdout.decode(errors='replace') if result.returncode in (0, 1) else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def read(path):
    try:
        with Path(path).open('rb') as stream:
            raw = stream.read(8193)
        return raw.decode(errors='replace') if len(raw) <= 8192 else None
    except OSError:
        return None


def collect(*, run=command, read_file=read, exists=lambda p: Path(p).exists(), which=shutil.which, now=None):
    captured = now or datetime.now(timezone.utc).isoformat()
    raw = read_file('/etc/nv_tegra_release') or ''
    l4t = re.search(r'#\s*R([0-9]+).*?REVISION:\s*([0-9.]+)', raw)
    packages = {}
    text = run(['dpkg-query', '-W', '-f=${binary:Package}\t${Version}\n', *PACKAGES])
    if text is not None:
        for line in text.splitlines():
            row = line.split('\t')
            if (len(row) == 2 and re.fullmatch(r'[a-z0-9.+:-]{1,80}', row[0])
                    and re.fullmatch(r'[0-9A-Za-z:.+~_-]{1,80}', row[1])):
                packages[row[0]] = row[1]
    backend = run(['ollama', '--version']) if which('ollama') else None
    version = re.search(r'(?i)ollama version(?: is)?\s+([0-9]+\.[0-9]+\.[0-9]+)', backend or '')
    cuda = {}
    for path in ('/usr/local/cuda/version.json', '/usr/local/cuda/version.txt'):
        value = read_file(path)
        if value:
            candidate = None
            if path.endswith('.json'):
                try:
                    item = json.loads(value).get('cuda', {})
                    candidate = item.get('version') if type(item) is dict else None
                except (ValueError, AttributeError):
                    pass
            else:
                match = re.search(r'(?i)CUDA Version\s+([0-9.]+)', value)
                candidate = match[1] if match else None
            if type(candidate) is str and re.fullmatch(r'[0-9]+\.[0-9]+(?:\.[0-9]+)?', candidate):
                cuda['version_file_reported'] = candidate
                break
    cuda['runtime_packages'] = {k: v for k, v in packages.items() if k.startswith(('cuda-cudart-', 'cuda-runtime-'))}
    result = {
        'schema': 'preceptoros.lab.node-metadata/1', 'kind': 'compatibility-observation',
        'node': 'node-d', 'observed_at': captured, 'clock_basis': 'target_OS_not_independently_attested',
        'collector_sha256': hashlib.sha256(globals().get('_SOURCE_BYTES') or Path(__file__).read_bytes()).hexdigest(),
        'l4t': {'state': 'OBSERVED', 'release': l4t[1], 'revision': l4t[2]} if l4t else nd('release_file_unavailable'),
        'jetpack': {'state': 'DECLARED', 'package_version': packages['nvidia-jetpack']}
                   if 'nvidia-jetpack' in packages else nd('metapackage_not_reported'),
        'cuda': {'state': 'DECLARED', 'value': cuda} if cuda['runtime_packages'] or len(cuda) > 1 else nd('cuda_version_not_reported'),
        'tensorrt': {'state': 'DECLARED', 'packages': {k: v for k, v in packages.items() if k.startswith('libnvinfer')}}
                    if any(k.startswith('libnvinfer') for k in packages) else nd('tensorrt_packages_not_reported'),
        'backend_cli': {'state': 'DECLARED', 'version': version[1]} if version else nd('backend_cli_version_unavailable'),
        'driver_module': {'state': 'OBSERVED', 'nvgpu_present': bool(exists('/sys/module/nvgpu'))},
        'tools': {name: bool(which(name)) for name in ('tegrastats', 'trtexec', 'nvcc')},
        'standard_trtexec_present': bool(exists('/usr/src/tensorrt/bin/trtexec')),
        'model_catalog': nd('not_recensused'),
        'compatibility': nd('no_backend_inference_or_engine_validation'),
        'gpu_execution': nd('not_measured'), 'first_token_latency': nd('no_streaming_probe'),
        'peak_memory_temperature_energy': nd('no_active_benchmark'),
        'settings_changed': False,
    }
    result['compatibility_ref'] = sha(result)
    return result


if __name__ == '__main__':
    print(json.dumps(collect(), sort_keys=True, separators=(',', ':')))
