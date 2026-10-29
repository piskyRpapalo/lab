"""Read-only inventory of a supplied adapter directory and local model service."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import urllib.error
import urllib.request


def digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            sha.update(block)
    return sha.hexdigest()


def adapters(root):
    if not root.is_dir():
        return {'state': 'NO_DATA', 'cause': 'adapter directory unavailable'}
    rows = []
    for weight in root.rglob('adapter_model.safetensors'):
        config = weight.with_name('adapter_config.json')
        try:
            row = {'sha256': digest(weight), 'bytes': weight.stat().st_size,
                   'config_sha256': digest(config) if config.is_file() else None,
                   'config_state': 'MEASURED' if config.is_file() else 'NO_DATA'}
            if not config.is_file():
                row['config_cause'] = 'adjacent configuration absent'
            rows.append(row)
        except OSError:
            return {'state': 'NO_DATA', 'cause': 'an adapter or configuration could not be read'}
    rows.sort(key=lambda row: (row['sha256'], row['config_sha256'] or ''))
    return {'state': 'MEASURED', 'weight_files': len(rows), 'weight_bytes': sum(r['bytes'] for r in rows), 'rows': rows}


def models():
    try:
        with urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=5) as response:
            data = json.load(response)
        rows = []
        for item in data['models']:
            sha, size = item['digest'], item['size']
            if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
                raise ValueError('invalid digest')
            if type(size) is not int or size < 0:
                raise ValueError('invalid size')
            rows.append({'manifest_sha256': sha, 'declared_bytes': size})
        rows.sort(key=lambda row: (row['manifest_sha256'], row['declared_bytes']))
        return {'state': 'MEASURED', 'manifest_entries': len(rows), 'unique_manifest_digests': len({r['manifest_sha256'] for r in rows}), 'rows': rows}
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return {'state': 'NO_DATA', 'cause': 'local model inventory unavailable or malformed'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adapters-root', type=Path, required=True)
    args = parser.parse_args()
    receipt = {'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
               'machine': {'architecture': platform.machine(), 'logical_cpus': os.cpu_count()},
               'models': models(), 'adapters': adapters(args.adapters_root),
               'limits': {'artifact_authenticity': 'NO_DATA: no signed expected digests supplied',
                          'compatibility': 'NO_DATA: no load or inference exercised',
                          'quality': 'NO_DATA: no evaluation performed',
                          'adapter_scope': 'only the supplied directory tree',
                          'model_digest': 'service-reported manifest digest; blob bytes not verified'}}
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
