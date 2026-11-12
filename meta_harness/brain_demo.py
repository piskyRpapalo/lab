"""Explicit, public-only brain prototype; writes only a new private demo directory.

APP libraries and real Hexelion are dependencies, not copied implementations.
The user database, carbon conversation, services and interface are untouched.
"""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

from .brain import cycle, verify_cycle, verify_projections
from .cli import demo_gate, model_catalog, provenance, task, utc_now
from .context import ContextConsumer
from .delegation import HEX, Session, TokenBudget, encode, sha
from .hexelion import ExistingHexelion
from .memory_draft import propose_draft
from .workers import NativeSort

# Synthetic public case, not a captured user prompt or private corpus.
QUERY = 'public integer sorting'
PUBLIC_SOURCE = ('Public integer sorting uses a local native tool. '
                 'Its independent judge checks order, length and the input multiset. '
                 'A source is evidence, never permission.')
APP_MODULES = ('textos', 'memory', 'memory_lookup', 'hexelion_book', 'indice_rack')


def load_app(root):
    """Load operator-trusted source; refuse mixed checkouts and pin source bytes.

    This is in-process dependency injection, not a sandbox for untrusted code.
    Imports of these modules already present in a different checkout are refused.
    """
    root = Path(root).resolve(strict=True)
    files = {name + '.py': root / (name + '.py') for name in APP_MODULES}
    files['hexelion_proxy.py'] = root / 'hexelion_proxy.py'
    def hashes():
        return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}
    pinned = hashes()
    for name in APP_MODULES:
        existing = sys.modules.get(name)
        if existing is not None and Path(existing.__file__).resolve() != files[name + '.py']:
            raise ValueError('mixed_app_checkout')
    sys.path.insert(0, str(root))
    try:
        modules = {name: importlib.import_module(name) for name in APP_MODULES}
        if any(Path(m.__file__).resolve() != files[name + '.py'] for name, m in modules.items()):
            raise ValueError('mixed_app_checkout')
    finally:
        sys.path.remove(str(root))
    if hashes() != pinned:
        raise ValueError('source_changed_during_import')
    return modules, pinned, lambda: sha(hashes())


def _directory(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('unsafe_demo_directory')
    # Deliberately fail if it exists: no overwrite, migration, deletion or implicit resume.
    path.mkdir(mode=0o700, parents=False, exist_ok=False)
    return path


def run(app_root, state_dir, approval_ref, *, base='http://127.0.0.1:21434',
        cancelled=lambda: False):
    if type(approval_ref) is not str or not HEX.fullmatch(approval_ref):
        raise ValueError('approval_reference_invalid')
    modules, files, current_version = load_app(app_root)
    state = _directory(state_dir)
    memory, rack, book = (modules[n] for n in ('memory', 'indice_rack', 'hexelion_book'))
    # All paths below were created here; umask is restored before any worker runs.
    previous = os.umask(0o077)
    try:
        db, index = state / 'memory.sqlite3', state / 'public-index.sqlite3'
        memory.crear(db)
        stamp = utc_now()
        rack.construir(index, [('public: native-sort-v1', 'Public native sort', PUBLIC_SOURCE, stamp)])
    finally:
        os.umask(previous)
    reader = ContextConsumer(lambda query: rack.buscar(query, index, limite=2), book,
        source_version=sha(files), version_check=current_version, kind='document')
    snapshot = reader.read(QUERY, stamp)
    # Deterministic public extract, checked by the existing APP quote/relevance code.
    # It is not a generated answer or a semantic accuracy benchmark.
    candidates = book.formato_citas(snapshot._sources, QUERY)
    raw = json.dumps({'citas': [{'id': snapshot._sources[0]['id'],
        'quote': candidates['properties']['citas']['items']['properties']['quote']['enum'][0]}]})
    quote = reader.quote(snapshot, raw, now=utc_now())
    worker = NativeSort()
    baseline = [task('brain-base-' + n, 'serion-sort', worker.version, 'baseline-tool',
        worker.input_sha256, 'local_function', 0) for n in ('one', 'two')]
    delegated = task('brain-dispatch', 'serion-sort', worker.version, 'local-tool',
        worker.input_sha256, 'local_function', 0)
    for value in baseline + [delegated]:
        value['task_id'] = 'public-sort-native'
    allowed = baseline + [delegated]
    # Exact task grants are minted only by this trusted, explicit public-demo host.
    # Host APP/H3 must inject their existing authority, not this CLI demo gate.
    session = Session(lambda t: demo_gate(allowed, approval_ref)(t), TokenBudget(512))
    catalog = model_catalog(base, 'hexelion:latest', 'private-model')
    def planner_factory(capability):
        if catalog['state'] != 'DECLARED':
            raise ValueError('planner_unavailable')
        adapter = ExistingHexelion(app_root, base, capability, context_ref=snapshot.record()['context_ref'])
        request = task('brain-plan', 'hexelion', catalog['model_version'], 'private-model',
                       adapter.input_sha256, 'ollama_loopback', 512)
        allowed.append(request)
        return adapter, request
    def write(receipt, request, *, cancelled):
        return propose_draft(receipt, request, session=session, memory_api=memory,
            db_path=db, consent=True, cancelled=cancelled).export()
    start = time.monotonic_ns()
    result = cycle(QUERY, snapshot, context=reader, session=session, worker=worker,
        baseline_tasks=baseline, delegated_task=delegated, planner_factory=planner_factory,
        now=utc_now, write_draft=write, cancelled=cancelled)
    duration = time.monotonic_ns() - start
    # Reconciliation uses another fresh connection, proving more than an in-memory cache.
    reconciliation = None
    if result['memory'] is not None:
        reconciliation = write(result['receipts'][-1], delegated, cancelled=cancelled)
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as c:
        draft_count = c.execute('SELECT count(*) FROM borradores').fetchone()[0]
        engram_count = c.execute('SELECT count(*) FROM engrams').fetchone()[0]
    return {'schema': 'preceptoros.brain-public-demo/1', 'observed_at': utc_now(),
        'scope': 'public_fixture_private_demo_database_not_app_integration',
        'source': provenance(), 'app_source_sha256': files,
        'public_source_sha256': hashlib.sha256(PUBLIC_SOURCE.encode()).hexdigest(),
        'context': snapshot.record(),
        'extract': {'state': quote['state'], 'quote_sha256': sha(quote['text']),
                    'source_count': len(quote['citations']), 'producer': 'native_public_reference'},
        'cycle': result, 'reconciliation': reconciliation,
        'tasks': allowed, 'chain_verified': verify_cycle(result, allowed, witness=session.attests),
        'database': {'drafts': draft_count, 'engrams': engram_count, 'user_database_touched': False},
        'projection_verified': verify_projections(result['views'], result['record']),
        'wall_ns': duration, 'local_token_ceiling': 512,
        'local_tokens_remaining': session.budget.remaining,
        'limits': {'app_integration': 'NO_DATA(host_not_wired)',
                   'acho_audio': 'NO_DATA(not_measured)', 'training': 'NOT_AUTHORIZED',
                   'server_network_isolation': 'NO_DATA(not_attested)',
                   'selection_scope': 'one_operator_prepared_public_capability'}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app-root', type=Path, required=True)
    parser.add_argument('--state-dir', type=Path, required=True)
    parser.add_argument('--approval-ref', required=True)
    parser.add_argument('--execute-public', action='store_true')
    parser.add_argument('--stop-file', type=Path)
    args = parser.parse_args(argv)
    if not args.execute_public:
        print(json.dumps({'state': 'NO_DATA', 'cause': 'execution_not_requested'}))
        return 1
    try:
        result = run(args.app_root, args.state_dir, args.approval_ref,
                     cancelled=lambda: args.stop_file is not None and args.stop_file.exists())
        if len(encode(result)) >= 16384:
            raise ValueError('artifact_budget')
    except Exception:
        print(json.dumps({'state': 'NO_DATA', 'cause': 'demo_setup_or_adapter_failed'}))
        return 1
    print(encode(result).decode())
    return 0 if result['cycle']['record']['state'] == 'MEASURED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
