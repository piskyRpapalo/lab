"""All witnesses here are synthetic; no host authority is represented."""
import copy
import unittest

from meta_harness.self_build_preflight import check


def proposal():
    return {'schema': 'preceptoros.self-build-proposal/1', 'repo_ref': 'a' * 64,
            'base_sha': 'b' * 40, 'patch_ref': 'c' * 64, 'paths': ['docs/example.md'],
            'reason_ref': 'd' * 64, 'problem_ref': 'e' * 64, 'test_plan_ref': 'f' * 64,
            'budget': {'seconds': 60, 'memory_bytes': 1024, 'cost_microunits': 0},
            'dependencies': [], 'recovery_ref': '1' * 64, 'human_review_ref': '2' * 64}


class PreflightTests(unittest.TestCase):
    def run_check(self, p=None, **kw):
        args = dict(allowed_paths=frozenset({'docs/example.md'}), source_witness=lambda _: True,
                    evidence_witness=lambda _: True, independent_judge=lambda _: True)
        args.update(kw)
        return check(proposal() if p is None else p, **args)

    def test_deterministic_proposal_is_not_authority(self):
        a = self.run_check()
        self.assertEqual(a, self.run_check())
        self.assertEqual(a['state'], 'PROPOSE_ONLY')
        self.assertIs(a['execution_authorized'], False)
        self.assertIn('signature', a['not_checked'])
        self.assertIn('independent_improvement_measurement', a['not_checked'])

    def test_protected_or_unallowlisted_paths_are_refused(self):
        for name in ('tests/test_example.py', 'AGENTS.md', '.github/workflows/test.yml',
                     'meta_harness/execution_journal.py', 'meta_harness/resource_admission.py',
                     'bin/verify_llms_tree.py', '../file'):
            p = proposal()
            p['paths'] = [name]
            self.assertEqual(self.run_check(p, allowed_paths=frozenset({name}))['state'],
                             'REFUSED', name)
        self.assertEqual(self.run_check(allowed_paths=frozenset())['cause'], 'path_not_allowlisted')

    def test_missing_witnesses_fail_closed(self):
        for name, cause in [('source_witness', 'source_unavailable'),
                            ('evidence_witness', 'evidence_unavailable'),
                            ('independent_judge', 'independent_judge_unavailable')]:
            for value in (None, lambda _: False, lambda _: 1):
                r = self.run_check(**{name: value})
                self.assertEqual((r['state'], r['cause']), ('NO_DATA', cause))
                self.assertFalse(r['execution_authorized'])

    def test_binding_prevents_inherited_patch_or_base_witness(self):
        original = proposal()
        expected = self.run_check(original)['proposal_ref']
        witness = lambda binding: binding['proposal_ref'] == expected
        for key, value in [('base_sha', 'c' * 40), ('patch_ref', 'd' * 64),
                           ('human_review_ref', '3' * 64), ('recovery_ref', '4' * 64)]:
            changed = copy.deepcopy(original)
            changed[key] = value
            self.assertEqual(self.run_check(changed, source_witness=witness)['state'], 'NO_DATA')

    def test_malformed_and_missing_recovery_ref_fail_closed(self):
        for key, value in [('patch_ref', 'bad'), ('base_sha', 'a' * 39), ('recovery_ref', None),
                           ('budget', {'seconds': True, 'memory_bytes': 1, 'cost_microunits': 0}),
                           ('dependencies', ['bad'])]:
            p = proposal()
            p[key] = value
            self.assertEqual(self.run_check(p)['state'], 'REFUSED')

    def test_witness_failure_and_mutation_cannot_create_authority(self):
        def fail(_):
            raise RuntimeError('private')
        def mutate(binding):
            binding['proposal']['patch_ref'] = '0' * 64
            return True
        self.assertEqual(self.run_check(source_witness=fail)['state'], 'NO_DATA')
        self.assertEqual(self.run_check(source_witness=mutate)['proposal_ref'], self.run_check()['proposal_ref'])

class ProtectedClassesTests(PreflightTests):
    def test_sensitive_classes_refused_even_when_explicitly_allowlisted(self):
        paths = ['.git/config', '.git/hooks/pre-commit', '.gitmodules',
                 'docs/nested/AGENTS.md', 'docs/nested/CLAUDE.md',
                 'meta_harness/self_improvement.py', 'meta_harness/reuse.py',
                 'meta_harness/brain.py', 'meta_harness/hexelion.py',
                 'meta_harness/cli.py', 'setup.py', 'pyproject.toml',
                 'src/feature/test_guard.py', 'tools/deploy.sh',
                 'policies/permission.md', '.github/workflows/check.yml']
        for path in paths:
            p = proposal()
            p['paths'] = [path]
            with self.subTest(path=path):
                self.assertEqual(self.run_check(p, allowed_paths=frozenset({path}))['cause'],
                                 'protected_path')

    def test_feature_and_documentation_are_not_globally_protected(self):
        for path in ('docs/design.md', 'features/new_feature.py'):
            p = proposal()
            p['paths'] = [path]
            self.assertEqual(self.run_check(p, allowed_paths=frozenset({path}))['state'], 'PROPOSE_ONLY')
