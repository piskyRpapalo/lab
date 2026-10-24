#!/usr/bin/env python3
"""Offline acceptance checker for shared MVP accessibility and parity evidence."""
import argparse
import base64
import binascii
import hashlib
import json
import math
import re
from pathlib import Path

THEMES = ('basic', 'atlantis', 'zombie')
ORIENTATIONS = ('portrait', 'landscape')
HEIGHTS = (256, 320, 375, 430, 512, 600, 720, 800)
ZOOMS = (0.6, 1.0, 3.0)
CONTRAST = {
    'basic': {'primary': 15.80, 'secondary': 9.91},
    'atlantis': {'primary': 18.27, 'secondary': 9.61},
    'zombie': {'primary': 15.11, 'secondary': 11.93},
}
PARITY_FIELDS = ('state', 'messages', 'errors', 'controls', 'contract')
HEX = re.compile(r'^[0-9a-f]{64}$')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def validate(doc):
    errors = []
    checks = {}
    if not isinstance(doc, dict) or doc.get('schema') != 'preceptoros.mvp-regression-evidence/1':
        return {'schema': 'preceptoros.mvp-regression-receipt/1', 'verdict': 'RED',
                'errors': ['unsupported evidence schema'], 'checks': {},
                'limits': {'contrast_is_certification': False}}

    source = doc.get('source') if isinstance(doc.get('source'), dict) else {}
    source_kind = source.get('kind', 'NO_DATA · evidence source missing')

    narration = doc.get('narration') if isinstance(doc.get('narration'), dict) else {}
    expected_viewports = {(t, o, h) for t in THEMES for o in ORIENTATIONS for h in HEIGHTS}
    seen_viewports = set()
    viewport_bad = False
    for row in narration.get('cases', []) if isinstance(narration.get('cases'), list) else []:
        if not isinstance(row, dict):
            viewport_bad = True
            continue
        theme, orientation, height = row.get('theme'), row.get('orientation'), row.get('height_px')
        if not isinstance(theme, str) or not isinstance(orientation, str) or not isinstance(height, int) or isinstance(height, bool):
            viewport_bad = True
            continue
        key = (theme, orientation, height)
        if key in seen_viewports or key not in expected_viewports:
            viewport_bad = True
        seen_viewports.add(key)
        if row.get('page_scroll_px') != 0 or row.get('narration_visible') is not True or row.get('message_complete') is not True:
            viewport_bad = True
    checks['narration_viewports'] = len(seen_viewports)
    if seen_viewports != expected_viewports:
        errors.append('viewport coverage incomplete')
        viewport_bad = True
    if viewport_bad:
        errors.append('narration viewport failed')

    zoom = doc.get('zoom') if isinstance(doc.get('zoom'), dict) else {}
    if zoom.get('minimum') != 0.6 or zoom.get('maximum') != 3.0:
        errors.append('zoom bounds must be 0.60 and 3.00')
    objects = zoom.get('interactive_objects')
    objects = objects if isinstance(objects, list) and all(isinstance(item, str) and item for item in objects) and len(set(objects)) == len(objects) else []
    expected_zoom_keys = {(t, obj, z) for t in THEMES for obj in objects for z in ZOOMS}
    zoom_sizes = {}
    seen_zoom = set()
    zoom_bad = False
    for row in zoom.get('cases', []) if isinstance(zoom.get('cases'), list) else []:
        if not isinstance(row, dict):
            zoom_bad = True
            continue
        theme, object_id, scale = row.get('theme'), row.get('object_id'), row.get('map_zoom')
        if (not isinstance(theme, str) or not isinstance(object_id, str)
                or not isinstance(scale, (int, float)) or isinstance(scale, bool)):
            zoom_bad = True
            continue
        key = (theme, object_id, scale)
        size = row.get('screen_size_px')
        if key in seen_zoom or key not in expected_zoom_keys:
            zoom_bad = True
        seen_zoom.add(key)
        if (not isinstance(size, list) or len(size) != 2 or
                any(not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0 for value in size)):
            zoom_bad = True
        else:
            zoom_sizes.setdefault(key[:2], set()).add(tuple(size))
    checks['zoom_samples'] = len(seen_zoom)
    if seen_zoom != expected_zoom_keys or not objects:
        errors.append('zoom samples do not match bounds and unit sample')
        zoom_bad = True
    if zoom_bad:
        errors.append('invalid zoom evidence')
    if any(len(sizes) != 1 for sizes in zoom_sizes.values()) or len(zoom_sizes) != len(THEMES) * len(objects):
        errors.append('interactive object size changes with map zoom')

    contrast_doc = doc.get('contrast') if isinstance(doc.get('contrast'), dict) else {}
    contrast_pairs = contrast_doc.get('pairs') if isinstance(contrast_doc.get('pairs'), dict) else {}
    contrast_count = 0
    contrast_bad = False
    for theme, expected in CONTRAST.items():
        rows = contrast_pairs.get(theme)
        found = {row.get('id'): row.get('ratio') for row in rows if isinstance(row, dict)} if isinstance(rows, list) else {}
        if set(found) != set(expected):
            contrast_bad = True
            continue
        for pair, value in expected.items():
            actual = found[pair]
            if not isinstance(actual, (int, float)) or isinstance(actual, bool) or not math.isfinite(actual) or abs(actual - value) > 0.01:
                contrast_bad = True
            contrast_count += 1
    checks['contrast_pairs'] = contrast_count
    if contrast_bad:
        errors.append('contrast regression fixture drift')

    export_doc = doc.get('export') if isinstance(doc.get('export'), dict) else {}
    states = export_doc.get('states')
    states = states if isinstance(states, list) and all(isinstance(item, str) and item for item in states) and len(set(states)) == len(states) else []
    state_digest = _sha(json.dumps(states, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8'))
    if export_doc.get('state_inventory_sha256') != state_digest:
        errors.append('compiled state inventory hash mismatch')
    expected_frames = {(t, state) for t in THEMES for state in states}
    frames = export_doc.get('frames') if isinstance(export_doc.get('frames'), list) else []
    frame_keys = set()
    frame_bad = False
    for row in frames:
        if not isinstance(row, dict):
            frame_bad = True
            continue
        theme, state = row.get('theme'), row.get('state')
        if not isinstance(theme, str) or not isinstance(state, str):
            frame_bad = True
            continue
        key = (theme, state)
        if key in frame_keys or key not in expected_frames:
            frame_bad = True
        frame_keys.add(key)
        if row.get('export_stage') != 'post-export':
            errors.append('frame is not post-export')
            frame_bad = True
        encoded, declared = row.get('payload_base64'), row.get('sha256')
        if not isinstance(encoded, str) or not isinstance(declared, str) or not HEX.fullmatch(declared):
            frame_bad = True
            continue
        try:
            raw = base64.b64decode(encoded, validate=True)
            raw.decode('utf-8')
        except (binascii.Error, UnicodeDecodeError, ValueError):
            frame_bad = True
            continue
        if _sha(raw) != declared:
            errors.append('exported frame hash mismatch')
            frame_bad = True
        if len(raw) > 1024:
            errors.append('exported Bubble frame exceeds 1024 UTF-8 bytes')
            frame_bad = True
    checks['post_export_frames'] = len(frame_keys)
    if export_doc.get('stage') != 'post-export' or frame_keys != expected_frames or not expected_frames:
        errors.append('post-export frame coverage incomplete')
        frame_bad = True
    if frame_bad and not any(item in errors for item in ('frame is not post-export', 'exported frame hash mismatch', 'exported Bubble frame exceeds 1024 UTF-8 bytes', 'post-export frame coverage incomplete')):
        errors.append('invalid exported frame evidence')

    parity_doc = doc.get('task_parity') if isinstance(doc.get('task_parity'), dict) else {}
    if tuple(parity_doc.get('fields', ())) != PARITY_FIELDS:
        errors.append('parity field list must be exact')
    tasks = parity_doc.get('tasks') if isinstance(parity_doc.get('tasks'), list) else []
    ids = set()
    parity_bad = False
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get('task_id'), str) or not task['task_id'] or task['task_id'] in ids:
            parity_bad = True
            continue
        ids.add(task['task_id'])
        if task.get('shared_fixture_sha256') != parity_doc.get('shared_fixture_sha256'):
            parity_bad = True
        web_out, app_out = task.get('web'), task.get('app')
        if not isinstance(web_out, dict) or not isinstance(app_out, dict):
            parity_bad = True
            continue
        if any(field not in web_out or field not in app_out or web_out[field] != app_out[field] for field in PARITY_FIELDS):
            parity_bad = True
    checks['shared_task_cases'] = len(ids)
    if parity_bad or not tasks or not HEX.fullmatch(str(parity_doc.get('shared_fixture_sha256', ''))):
        errors.append('web/app task output mismatch')

    # Keep diagnostics stable and one-per-cause for machine receipts.
    errors = list(dict.fromkeys(errors))
    return {'schema': 'preceptoros.mvp-regression-receipt/1',
            'run_id': doc.get('run_id'), 'source_kind': source_kind,
            'verdict': 'GREEN' if not errors else 'RED', 'checks': checks,
            'errors': errors,
            'limits': {'contrast_is_certification': False,
                       'narration_matrix': '3 themes x 2 orientations x 8 heights (256–800 px)',
                       'frame_ceiling_utf8_bytes': 1024,
                       'parity_compares': list(PARITY_FIELDS)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    args = parser.parse_args()
    try:
        doc = json.loads(args.evidence.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({'schema': 'preceptoros.mvp-regression-receipt/1', 'verdict': 'RED',
                          'errors': [f'evidence unreadable: {type(exc).__name__}'], 'checks': {},
                          'limits': {'contrast_is_certification': False}}, ensure_ascii=False))
        return 2
    result = validate(doc)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result['verdict'] == 'GREEN' else 1


if __name__ == '__main__':
    raise SystemExit(main())
