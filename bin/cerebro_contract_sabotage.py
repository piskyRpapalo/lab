#!/usr/bin/env python3
"""Reproducible in-memory contract mutations; source files never change."""
import argparse
import subprocess
import sys
import json
import hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--output', type=Path)
args = ap.parse_args()
cases=[
 ('snapshot-ttl','meta_harness.context','if not 0 <= age <= self.max_age:','if False:', 'tests.test_meta_context.ContextTests.test_clock_ttl_unknown_dates_and_documents_are_not_live_measurements'),
 ('observation-ttl','meta_harness.context',"if self.kind == 'observation' and age > self.max_age:",'if False:', 'tests.test_meta_context.ContextTests.test_clock_ttl_unknown_dates_and_documents_are_not_live_measurements'),
 ('source-revalidation','meta_harness.context',"or fresh.record()['sources_sha256'] != record['sources_sha256']",'or False', 'tests.test_meta_context.ContextTests.test_changed_source_even_with_valid_new_hash_invalidates_previous_snapshot'),
 ('source-version','meta_harness.context','if self.version_check() != self.version:','if False:', 'tests.test_meta_context.ContextTests.test_query_snapshot_prompt_and_implementation_mutations_rejected'),
 ('source-digest','meta_harness.context',"or source['sha256'] != digest_text(source['texto'])",'or False', 'tests.test_meta_context.ContextTests.test_duplicate_sources_changed_hash_and_budgets_rejected'),
 ('consent','meta_harness.memory_draft','_require(consent is True, "consent_required")','_require(True, "consent_required")', 'tests.test_memory_draft.DraftTests.test_consent'),
 ('witness','meta_harness.memory_draft','and Session.attests(session, receipt, task) is True','and True', 'tests.test_memory_draft.DraftTests.test_forged_binding'),
 ('dedup','meta_harness.memory_draft','if row:\n        return _present(row, ref)','if False:\n        return _present(row, ref)', 'tests.test_brain.BrainTests.test_reconciliation_never_invokes_a_writer_after_durable_ack'),
 ('same-state','meta_harness.brain',"or record['summary'] != summary(record['state'], record['stage'])",'or False', 'tests.test_brain.BrainTests.test_resealed_live_or_wrong_summary_cannot_launder_a_projection'),
 ('stage-revalidation','meta_harness.brain','context.validate(snapshot, query, now())','pass', 'tests.test_brain.BrainTests.test_source_race_between_selection_and_execution_is_detected'),
 ('planner-context-input','meta_harness.hexelion','or actual_input != self.input_sha256','or False', 'tests.test_brain.BrainTests.test_snapshot_digest_rechecked_before_existing_adapter_dispatch')]
cases.extend([('fresh-prompt', 'meta_harness.context', "or fresh.record()['prompt_sha256'] != record['prompt_sha256']", 'or False', 'tests.test_meta_context.ContextTests.test_changed_producer_prompt_with_same_sources_and_version_is_rejected'), ('chain-context-binding', 'meta_harness.brain', "or planned_task['input_sha256'] != digest_text(public_prompt(capability,\n                                                       context_ref=record['context_ref']))", 'or False', 'tests.test_brain.BrainTests.test_chain_role_and_context_forgery_fail_even_with_resealed_views'), ('durable-outcome', 'meta_harness.brain_demo', "if (report['reconciliation'] != report['cycle']['memory']\n            or report['reconciliation'] is None or report['reconciliation'].get('state') != 'PENDING'):", 'if False:', 'tests.test_brain.BrainTests.test_overall_success_requires_durable_reconciliation_and_database_counts')])
child='''import importlib,io,json,unittest,sys
module,before,after,test=json.loads(sys.argv[1])
m=importlib.import_module(module)
s=open(m.__file__).read()
assert before in s
exec(compile(s.replace(before,after),m.__file__,"exec"),m.__dict__)
r=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromName(test))
print(json.dumps(dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors))))
'''
rows=[]
for rep in (1,2):
 for name,mod,before,after,test in cases:
  p=subprocess.run([sys.executable,'-B','-c',child,json.dumps([mod,before,after,test])],capture_output=True,text=True,cwd=ROOT,timeout=30)
  result=json.loads(p.stdout) if p.returncode==0 else dict(tests=0,failures=0,errors=1)
  rows.append(dict(case=name,repeat=rep,detected=result['tests']>0 and result['failures']>0 and result['errors']==0,**result))
report=dict(schema='cerebro-contract-sabotage/1',scope='in_memory_real_code_mutations_not_fixture_outcomes',mutations=len(cases),rounds=2,results=rows)
report['sha256']=hashlib.sha256(json.dumps(report,sort_keys=True,separators=(',',':')).encode()).hexdigest()
if args.output:
 args.output.write_text(json.dumps(report,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps(report))
sys.exit(0 if all(r['detected'] for r in rows) else 1)
