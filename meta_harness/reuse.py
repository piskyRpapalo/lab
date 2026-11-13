"""Load the existing canonical LAB instruments without copying their implementation."""
from functools import lru_cache
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = {'throughput': 'benchmarks/station-96-first-pass-20261029/smoke.py',
         'evidence': 'bin/dfa06_evidence_bundle.py', 'family': 'bin/dfa_b5_family_blind_gate.py',
         'compare': 'bin/compare_receipts.py', 'suite': 'bin/eval_harness.py',
         'resources': 'bin/resource_decision.py'}


@lru_cache(None)
def instrument(name):
    spec = importlib.util.spec_from_file_location('meta_reuse_' + name, ROOT / PATHS[name])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
