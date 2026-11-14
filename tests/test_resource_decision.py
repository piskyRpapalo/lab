import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).parents[1]
# Reuse the same module/class identity as other LAB suites: reloading
# resource_decision under its canonical name invalidates Host isinstance().
sys.path.insert(0, str(ROOT / 'bin'))
import resource_decision as r
import resource_decision_probe as p


class ResourceDecision(unittest.TestCase):
    def run_case(self, edit=lambda *_: None, change_host=lambda h: h):
        task, packets, profiles, policy = p.fixture()
        edit(task, packets, profiles, policy)
        host = change_host(p.host_for(task, packets, profiles))
        result = r.decide(task, packets, profiles, policy, host=host, now=p.NOW)
        self.assertFalse(result['dispatch_authorized'])
        self.assertFalse(result['memory_promotion_authorized'])
        self.assertLess(len(r.encode(result)), 1024)
        return result

    def test_eight_required_cases_pass_and_are_explicit_synthetic(self):
        report = p.report()
        self.assertEqual((report['tests'], report['passed'], report['model_calls']), (8, 8, 0))
        self.assertIn('SYNTHETIC', report['evidence_basis'])
        for row in report['cases']:
            decision = row['actual']
            if decision['choice']:
                self.assertEqual(decision['state'], 'SIMULATED_ELIGIBLE')
        alias = next(row for row in report['cases'] if row['case'] == 'same_alias_distinct_digests')
        self.assertEqual(alias['actual']['choice']['node'], 'node-b')

    def test_report_is_byte_identical_and_source_inputs_not_changed(self):
        self.assertEqual(r.encode(p.report()), r.encode(p.report()))
        t, nodes, evidence, policy = p.fixture()
        original = copy.deepcopy((t, nodes, evidence, policy))
        r.decide(t, nodes, evidence, policy, host=p.host_for(t, nodes, evidence), now=p.NOW)
        self.assertEqual((t, nodes, evidence, policy), original)

    def test_permission_denied_before_any_evidence_callback(self):
        calls = []
        def host(h):
            return r.Host(h.validate_task, lambda _: None,
                          lambda _: calls.append('projection'), lambda *_: calls.append('witness'))
        self.assertEqual(self.run_case(change_host=host)['cause'], 'PERMISSION_DENIED')
        self.assertEqual(calls, [])

    def test_model_label_or_self_verified_flag_cannot_replace_witness(self):
        def host(h):
            return r.Host(h.validate_task, h.authorize, h.verify_projection, lambda *_: False)
        self.assertEqual(self.run_case(change_host=host)['cause'], 'PROFILE_NOT_WITNESSED')

    def test_forged_human_reference_alone_is_not_signature(self):
        result = self.run_case(lambda t, n, e, policy: policy.update(requires_human=True, human_ref='a'*64))
        self.assertEqual(result['cause'], 'HUMAN_SIGNATURE_REQUIRED')

    def test_measured_label_does_not_activate_unintegrated_production_gate(self):
        def edit(t, n, e, policy):
            e[0]['origin'] = 'MEASURED'
            e[0].pop('profile_ref');e[0]['profile_ref'] = r.sha(e[0])
        result = self.run_case(edit)
        self.assertEqual(result['state'], 'ABSTAIN')
        self.assertEqual(result['cause'], 'PRODUCTION_ADMISSION_NOT_CONNECTED')

    def test_memory_latency_pressure_and_concurrency_rejections_are_separate(self):
        for field, value, expected in [('peak_ram_bytes', 1000, 'RESOURCE_SHORTFALL'),
                                      ('latency_ms', 1100, 'LATENCY_ENVELOPE_EXCEEDS_BUDGET'),
                                      ('pressure_limit_pct', -1, 'RESOURCE_TELEMETRY_MISSING')]:
            def edit(t, n, e, policy):
                e[0][field] = value;e[0].pop('profile_ref');e[0]['profile_ref'] = r.sha(e[0])
            self.assertEqual(self.run_case(edit)['cause'], expected)
        self.assertEqual(self.run_case(lambda t,n,e,policy: policy.update(active_jobs=1))['cause'], 'NODE_SATURATION')
        self.assertEqual(self.run_case(lambda t,n,e,policy: n[0]['record']['resources'].update(pressure={'state':'NO_DATA'}))['cause'], 'RESOURCE_TELEMETRY_MISSING')

    def test_profile_cannot_cross_source_context_or_digest(self):
        for key in ('source_ref', 'model_version', 'task_profile_ref'):
            def edit(t,n,e,policy):
                e[0][key] = '0'*64;e[0].pop('profile_ref');e[0]['profile_ref'] = r.sha(e[0])
            self.assertEqual(self.run_case(edit)['cause'], 'TASK_RESOURCE_EVIDENCE_MISSING')

    def test_quality_and_independent_case_minimum_come_from_host_policy(self):
        def edit(t,n,e,policy):
            e[0]['independent_cases'] = 1;e[0].pop('profile_ref');e[0]['profile_ref'] = r.sha(e[0])
        self.assertEqual(self.run_case(edit)['cause'], 'QUALITY_OR_CALIBRATION_INSUFFICIENT')

    def test_future_profile_and_stale_profile_fail_closed(self):
        for time, expected in [('2026-11-13T12:00:01Z','EVIDENCE_FUTURE'),
                               ('2026-11-13T11:00:00Z','PROFILE_STALE')]:
            def edit(t,n,e,policy):
                e[0]['observed_at'] = time;e[0].pop('profile_ref');e[0]['profile_ref'] = r.sha(e[0])
            self.assertEqual(self.run_case(edit)['cause'], expected)

    def test_witnessed_model_failure_is_not_a_resource_or_transport_failure(self):
        def edit(t,n,e,policy):
            e[0]['quality_pass'] = False;e[0].pop('profile_ref');e[0]['profile_ref'] = r.sha(e[0])
        self.assertEqual(self.run_case(edit)['cause'], 'MODEL_TASK_FAILURE')

    def test_duplicate_or_multiple_eligible_backends_are_not_arbitrarily_ranked(self):
        self.assertEqual(self.run_case(lambda t,n,e,policy: n.append(copy.deepcopy(n[0])))['cause'], 'DUPLICATE_BACKEND')
        def edit(t,n,e,policy):
            other = copy.deepcopy(n[0]);other['record']['node'] = 'node-e';n.append(other)
            profile = copy.deepcopy(e[0]);profile['node'] = 'node-e';profile.pop('profile_ref')
            profile['profile_ref'] = r.sha(profile);e.append(profile)
        self.assertEqual(self.run_case(edit)['cause'], 'MULTIPLE_ELIGIBLE_REQUIRES_HOST_CHOICE')

    def test_final_recheck_detects_revocation_and_cancellation(self):
        def host(h):
            calls = []
            def authorize(task):
                calls.append(1)
                return h.authorize(task) if len(calls) == 1 else None
            return r.Host(h.validate_task, authorize, h.verify_projection, h.witness)
        self.assertEqual(self.run_case(change_host=host)['cause'], 'FINAL_HOST_RECHECK_FAILED')
        t,n,e,policy = p.fixture()
        result = r.decide(t,n,e,policy,host=p.host_for(t,n,e),now=p.NOW,cancelled=lambda: True)
        self.assertEqual(result['cause'], 'CANCELLED')

    def test_callback_errors_do_not_escape_or_cause_fallback(self):
        def host(h):
            def fail(_): raise RuntimeError('/private/CANARY')
            return r.Host(h.validate_task, fail, h.verify_projection, h.witness)
        result = self.run_case(change_host=host)
        self.assertEqual(result['cause'], 'HOST_OR_EVIDENCE_ERROR')
        self.assertNotIn('CANARY', r.encode(result).decode())


if __name__ == '__main__':
    unittest.main()
