"""Read-only, propose-only preflight; injected witnesses are host trust boundaries.

This checks a proposal, never a build result or a grant. Source and evidence
witnesses must independently check the exact digest binding, including actual
repository/diff identity and evidence freshness. Callbacks in tests are fixtures.
"""
import copy
import re
from pathlib import PurePosixPath

from .improvement import _digest, _hex

SHA1 = re.compile(r'[0-9a-f]{40}\Z')
PATH = re.compile(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\Z')
# Conservative classes, not a permission system. Changes to these classes may
# be proposed via a separate sovereign review, never this ordinary path.
PROTECTED_COMPONENTS = frozenset({'.git', '.github', 'tests', 'test', 'bin',
                                  'firmas', 'signatures', 'permissions', 'policies',
                                  'governance', 'security', 'migrations', 'deploy'})
PROTECTED_NAMES = frozenset({'agents.md', 'claude.md', '.gitmodules', '.gitattributes',
                             '.gitignore', 'pyproject.toml', 'setup.py', 'setup.cfg',
                             'makefile', 'dockerfile', 'compose.yml', 'compose.yaml',
                             'package.json', 'package-lock.json', 'requirements.txt'})
ENTRYPOINT = re.compile(r'(?:^|[-_.])(install|setup|deploy|launch|entrypoint|bootstrap|permission|permissions|policy|policies|governance|security|authorization|auth|signature|signatures)(?:[-_.]|$)')


def protected_path(path):
    parts = tuple(part.casefold() for part in PurePosixPath(path).parts)
    name = parts[-1]
    return (bool(set(parts) & PROTECTED_COMPONENTS) or name in PROTECTED_NAMES
            or bool(ENTRYPOINT.search(name)) or name.startswith('test_')
            or name.endswith(('_test.py', '.test.js', '.test.mjs'))
            or parts[0] == 'meta_harness')


KEYS = {'schema', 'repo_ref', 'base_sha', 'patch_ref', 'paths', 'reason_ref',
        'problem_ref', 'test_plan_ref', 'budget', 'dependencies', 'recovery_ref',
        'human_review_ref'}


def _result(state, cause, checked=(), missing=(), ref=None):
    return {'schema': 'preceptoros.self-build-preflight/1', 'state': state,
            'cause': cause, 'checked': list(checked), 'not_checked': list(missing),
            'proposal_ref': ref, 'execution_authorized': False}


def check(proposal, *, allowed_paths, source_witness=None, evidence_witness=None,
          independent_judge=None):
    """The allowlist and all callbacks belong to the host, never the proposer.

    source_witness(binding) verifies actual repo, base, patch bytes and paths;
    evidence_witness(binding) checks original problem, plans, dependencies and
    recovery provenance; independent_judge(binding) checks reasoning, not grants.
    Literal True is the only affirmative answer. No callback is a signature.
    """
    checked = []
    try:
        p = copy.deepcopy(proposal)
        if type(p) is not dict or set(p) != KEYS or p['schema'] != 'preceptoros.self-build-proposal/1':
            return _result('REFUSED', 'invalid_schema')
        if not all(_hex(p[k]) for k in ('repo_ref', 'patch_ref', 'reason_ref', 'problem_ref',
                                          'test_plan_ref', 'recovery_ref', 'human_review_ref')):
            return _result('REFUSED', 'invalid_reference')
        if type(p['base_sha']) is not str or not SHA1.fullmatch(p['base_sha']):
            return _result('REFUSED', 'invalid_base')
        paths = p['paths']
        if (type(paths) is not list or not 1 <= len(paths) <= 32 or len(set(paths)) != len(paths)
                or any(type(x) is not str or len(x) > 240 or not PATH.fullmatch(x)
                       or any(part in ('.', '..') for part in PurePosixPath(x).parts) for x in paths)):
            return _result('REFUSED', 'invalid_paths')
        if any(protected_path(x) for x in paths):
            return _result('REFUSED', 'protected_path')
        if (type(allowed_paths) is not frozenset or any(x not in allowed_paths for x in paths)):
            return _result('REFUSED', 'path_not_allowlisted')
        b = p['budget']
        if (type(b) is not dict or set(b) != {'seconds', 'memory_bytes', 'cost_microunits'}
                or any(type(b[k]) is not int or not 0 <= b[k] <= limit for k, limit in
                       [('seconds', 86400), ('memory_bytes', 2**40), ('cost_microunits', 10**9)])):
            return _result('REFUSED', 'invalid_budget')
        if (type(p['dependencies']) is not list or len(p['dependencies']) > 32
                or any(not _hex(x) for x in p['dependencies'])
                or len(set(p['dependencies'])) != len(p['dependencies'])):
            return _result('REFUSED', 'invalid_dependencies')
        checked.extend(('schema', 'scope', 'budget_shape'))
        ref = _digest(p)
        binding = {'proposal_ref': ref, 'proposal': p}
        for name, witness in (('source', source_witness), ('evidence', evidence_witness),
                              ('independent_judge', independent_judge)):
            if not callable(witness) or witness(copy.deepcopy(binding)) is not True:
                return _result('NO_DATA', name + '_unavailable', checked,
                               tuple(n for n in ('source', 'evidence', 'independent_judge') if n not in checked), ref)
            checked.append(name)
        return _result('PROPOSE_ONLY', 'human_review_required', checked,
                       ('execution', 'signature', 'independent_improvement_measurement'), ref)
    except Exception:
        return _result('NO_DATA', 'verification_failed', checked)
