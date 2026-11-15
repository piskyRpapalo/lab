"""One bounded composition of retrieval, witnessed selection, dispatch and draft.

This is a consumer prototype for APP/H3 integration, not a scheduler, state bus
or permission service. All authority and persistence adapters belong to the host.
"""
from .context import CAUSES as CONTEXT_CAUSES, ContextError, digest_text, instant
from .delegation import HEX, encode, sha, verify
from .hexelion import capability_evidence, public_prompt

CAUSES = CONTEXT_CAUSES | {'baseline_not_witnessed', 'selection_not_witnessed', 'planner_abstained',
    'execution_not_witnessed', 'memory_adapter_absent', 'memory_not_confirmed', 'host_adapter_failed', 'cancelled'}
STAGES = ('context', 'baseline', 'selection', 'execution', 'memory', 'complete', 'finalization')
RECORD_KEYS = {'schema', 'state', 'cause', 'stage', 'observed_at', 'context_ref', 'receipt_refs',
               'memory_ref', 'summary', 'promotion', 'cycle_ref'}


def summary(state, stage):
    return ('Local task verified; memory draft awaits human review.' if state == 'MEASURED'
            else 'Local cycle stopped at ' + stage + '; evidence is incomplete.')


def _complete(receipt, task, session):
    return (verify(receipt) and session.attests(receipt, task) is True
            and receipt['phase'] == 'complete' and receipt['outcome'] == 'KNOWN'
            and receipt['measurement'] is not None and receipt['measurement']['grade'] == 'PASS')


def cycle(query, snapshot, *, context, session, worker, baseline_tasks, delegated_task,
          planner_factory, now, write_draft=None, cancelled=lambda: False, bindings=()):
    """Run exactly the operator-prepared tasks. Model choice never grants permission.

    planner_factory(capability) -> (adapter, exact task); adapter exposes decision
    and input_sha256. write_draft(receipt, task, cancelled=...) -> sanitized status.
    Callbacks are trusted host wiring; no tool/model names come from source prose.
    Session retries are process-local: restart reconciliation remains a host duty.
    """
    events, receipts = [], []
    stage, cause, memory = 'context', None, None
    def fresh():
        if cancelled():
            raise ContextError('context_unavailable')
        context.validate(snapshot, query, now())
    def event(name, state, ref=None):
        events.append({'stage': name, 'state': state, 'ref': ref})
    try:
        fresh()
        event('context', 'MEASURED', snapshot.record()['context_ref'])
        stage = 'baseline'
        if bindings:
            from .task_binding import BoundWorker
            if (type(bindings) is not tuple or len(bindings) != 3
                    or any(type(b) is not BoundWorker for b in bindings)
                    or len({b.record()['pin_ref'] for b in bindings}) != 1):
                raise ContextError('context_contract_invalid')
            for task in list(baseline_tasks) + [delegated_task]:
                matches = [b for b in bindings if b.task() == task]
                if (len(matches) != 1
                        or matches[0].pin()['selection_ref'] != snapshot.record()['context_ref']):
                    raise ContextError('context_contract_invalid')
                matches[0].original_for(task)
        if len(baseline_tasks) != 2:
            raise ContextError('context_contract_invalid')
        baseline = []
        for task in baseline_tasks:
            fresh()
            receipt = session.execute(task, worker, observed_at=now(), cancelled=cancelled)
            baseline.append(receipt)
            receipts.append(receipt)
        capability = capability_evidence(baseline, baseline_tasks, worker.version, now(),
                                         witness=session.attests, bindings=bindings,
                                         context_ref=snapshot.record()['context_ref'])
        if capability is None:
            cause = 'baseline_not_witnessed'
        else:
            event('baseline', 'MEASURED', sha([r['receipt_ref'] for r in baseline]))
            stage = 'selection'
            fresh()
            planner, planned_task = planner_factory(capability)
            if (planned_task['input_sha256'] != planner.input_sha256
                    or planner.context_ref != snapshot.record()['context_ref']):
                raise ContextError('context_contract_invalid')
            planned = session.execute(planned_task, planner, observed_at=now(), cancelled=cancelled)
            receipts.append(planned)
            # A cached Session receipt need not call this newly-created adapter.
            # Recover the closed choice from its witnessed output digest, not mutable attributes.
            choice = next((action for action in ('DELEGATE_LOCAL', 'NO_DATA')
                           if planned.get('measurement') is not None
                           and planned['measurement']['output_sha256'] == sha({'action': action})), None)
            if not _complete(planned, planned_task, session) or choice is None:
                cause = 'selection_not_witnessed'
            elif choice == 'NO_DATA':
                cause = 'planner_abstained'
            else:
                event('selection', 'MEASURED', planned['receipt_ref'])
                stage = 'execution'
                first = baseline_tasks[0]
                for key in ('task_id', 'specialist', 'input_sha256', 'model_version',
                            'transport', 'max_tokens', 'privacy', 'depth'):
                    if delegated_task[key] != first[key]:
                        raise ContextError('context_contract_invalid')
                if (delegated_task['run_id'] in {t['run_id'] for t in baseline_tasks}
                        or delegated_task['source'] != {'baseline-tool': 'local-tool',
                            'baseline-model': 'local-model'}.get(first['source'])):
                    raise ContextError('context_contract_invalid')
                fresh()
                result = session.execute(delegated_task, worker, observed_at=now(), cancelled=cancelled)
                receipts.append(result)
                if not _complete(result, delegated_task, session):
                    cause = 'execution_not_witnessed'
                else:
                    event('execution', 'MEASURED', result['receipt_ref'])
                    stage = 'memory'
                    fresh()
                    if write_draft is None:
                        cause = 'memory_adapter_absent'
                    else:
                        memory = write_draft(result, delegated_task, cancelled=cancelled)
                        if (type(memory) is not dict or set(memory) != {'schema', 'state', 'cause', 'receipt_ref'}
                                or memory['schema'] != 'preceptoros.meta-memory-draft/1'
                                or memory['state'] != 'PENDING' or memory['cause'] != 'exact_draft_present'
                                or memory.get('receipt_ref') != result['receipt_ref']
                                ):
                            memory = None
                            cause = 'memory_not_confirmed'
                        else:
                            # A draft is contextual evidence pending human review, not an engram.
                            event('memory', 'DRAFT', sha(memory))
                            stage = 'complete'
    except ContextError as exc:
        cause = exc.cause
    except Exception:
        cause = 'host_adapter_failed'
    if cancelled():
        cause = 'cancelled'
        if stage == 'complete':
            stage = 'finalization'
    state = 'MEASURED' if stage == 'complete' and cause is None else 'NO_DATA'
    text = summary(state, stage)
    record = {'schema': 'preceptoros.brain-cycle/1', 'state': state, 'cause': cause,
        'stage': stage, 'observed_at': now(), 'context_ref': snapshot.record()['context_ref'],
        'receipt_refs': [r['receipt_ref'] for r in receipts],
        'memory_ref': sha(memory) if memory is not None else None, 'summary': text,
        'promotion': 'NOT_AUTHORIZED'}
    record['cycle_ref'] = sha(record)
    if len(encode(record)) >= 1024:
        raise ValueError('cycle_receipt_budget')
    return {'record': record, 'events': events, 'receipts': receipts, 'memory': memory,
            'views': projections(record)}


def projections(record):
    if (not valid_record(record)
            or len(encode(record)) >= 1024
            or record.get('cycle_ref') != sha({k: v for k, v in record.items() if k != 'cycle_ref'})
            ):
        raise ValueError('cycle_record_invalid')
    return {'text': {'state_ref': record['cycle_ref'], 'summary': record['summary']},
            'speech': {'state_ref': record['cycle_ref'], 'summary': record['summary']},
            'machine': {'state_ref': record['cycle_ref'], 'record': record}}


def verify_projections(views, record):
    try:
        return views == projections(record)
    except (ValueError, TypeError):
        return False


def valid_record(record):
    try:
        if (type(record) is not dict or set(record) != RECORD_KEYS
                or record['schema'] != 'preceptoros.brain-cycle/1'
                or record['state'] not in ('MEASURED', 'NO_DATA') or record['stage'] not in STAGES
                or record['promotion'] != 'NOT_AUTHORIZED'
                or type(record['summary']) is not str or len(record['summary']) > 100
                or record['summary'] != summary(record['state'], record['stage'])
                or type(record['receipt_refs']) is not list or len(record['receipt_refs']) > 4
                or len(set(record['receipt_refs'])) != len(record['receipt_refs'])):
            return False
        for ref in [record['context_ref'], record['cycle_ref'], *record['receipt_refs']]:
            if type(ref) is not str or not HEX.fullmatch(ref):
                return False
        if record['memory_ref'] is not None and (type(record['memory_ref']) is not str
                or not HEX.fullmatch(record['memory_ref'])):
            return False
        instant(record['observed_at'])
        measured = record['state'] == 'MEASURED'
        return ((record['cause'] is None and record['stage'] == 'complete'
                 and len(record['receipt_refs']) == 4 and record['memory_ref'] is not None)
                if measured else record['cause'] in CAUSES and record['stage'] != 'complete')
    except (ValueError, TypeError, KeyError, ContextError):
        return False


def verify_cycle(result, tasks, *, witness, bindings=()):
    """Host-local chain verification. Serialized hashes alone are not attestation."""
    try:
        record, receipts = result['record'], result['receipts']
        by_hash = {sha(t): t for t in tasks}
        if (not callable(witness) or not verify_projections(result['views'], record)
                or record['receipt_refs'] != [r['receipt_ref'] for r in receipts]
                or any(not verify(r) or witness(r, by_hash[r['task_sha256']]) is not True
                       for r in receipts)
                or record['memory_ref'] != (sha(result['memory']) if result['memory'] is not None else None)):
            return False
        if record['state'] == 'MEASURED':
            bound = [by_hash[r['task_sha256']] for r in receipts]
            first, planned_task, delegated = bound[0], bound[2], bound[3]
            capability = capability_evidence(receipts[:2], bound[:2], first['model_version'],
                receipts[2]['observed_at'], witness=witness, bindings=bindings,
                context_ref=record['context_ref'])
            if (capability is None or planned_task['source'] != 'private-model'
                    or planned_task['specialist'] != 'hexelion' or planned_task['max_tokens'] != 512
                    or planned_task['task_id'] != 'public-sort'
                    or planned_task['transport'] != 'ollama_loopback'
                    or planned_task['input_sha256'] != digest_text(public_prompt(capability,
                                                       context_ref=record['context_ref']))
                    or delegated['source'] != {'baseline-tool': 'local-tool',
                        'baseline-model': 'local-model'}.get(first['source'])
                    or len({t['run_id'] for t in bound}) != 4
                    or any(delegated[k] != first[k] for k in ('task_id', 'specialist', 'input_sha256',
                        'model_version', 'transport', 'max_tokens', 'privacy', 'depth'))):
                return False
            expected_events = [
                {'stage': 'context', 'state': 'MEASURED', 'ref': record['context_ref']},
                {'stage': 'baseline', 'state': 'MEASURED', 'ref': sha(record['receipt_refs'][:2])},
                {'stage': 'selection', 'state': 'MEASURED', 'ref': record['receipt_refs'][2]},
                {'stage': 'execution', 'state': 'MEASURED', 'ref': record['receipt_refs'][3]},
                {'stage': 'memory', 'state': 'DRAFT', 'ref': record['memory_ref']}]
            if (result['events'] != expected_events
                    or any(r['phase'] != 'complete' or r['measurement']['grade'] != 'PASS' for r in receipts)
                    or receipts[2]['measurement']['output_sha256'] != sha({'action': 'DELEGATE_LOCAL'})
                    or set(result['memory']) != {'schema', 'state', 'cause', 'receipt_ref'}
                    or result['memory']['schema'] != 'preceptoros.meta-memory-draft/1'
                    or result['memory']['state'] != 'PENDING'
                    or result['memory']['cause'] != 'exact_draft_present'
                    or result['memory']['receipt_ref'] != receipts[-1]['receipt_ref']):
                return False
        return True
    except (ValueError, TypeError, KeyError, AttributeError):
        return False


def deliver_bound(bound, *, session, receive, attest_ack, witness_execution, now,
                  cancelled=lambda: False):
    """Controlled local receiver bridge; never remote scope or a CLI TTY injector.

    Host callbacks must be bounded and independently attest original sources.
    ACK means received only. Native grant, AdmissionGate, journal and final lease
    checks remain distinct. Callback agreement is not portable authentication.
    """
    import copy
    from datetime import datetime, timedelta
    from .delegation import Session, Failure, check_grant
    from .execution_journal import ExecutionJournal, DurableTokenBudget
    from .resource_admission import AdmissionGate, resources
    from .task_binding import BoundWorker

    row = dict(schema='preceptoros.native-delivery/0', state='NO_DATA', cause='host_contract_missing',
        agent_ref=None, node_ref=None, mission_ref=None, delivery_ref=None, execution_ref=None,
        observed_at=None, stages={k:'NO_DATA' for k in
            ('observed','received','authorized','executed','verified')}, authority='none',
        origin='NO_DATA', source_basis='HOST_SUPPLIED_UNATTESTED', live=False, remote_authorized=False)

    def finish(state, cause):
        row.update(state=state,cause=cause)
        row['receipt_ref']=sha(row)
        if len(encode(row))>=1024:raise ValueError('delivery_receipt_bound')
        return row

    def current():
        t=now()
        if type(t) is not datetime or t.utcoffset()!=timedelta(0):raise Failure('EVIDENCE')
        return t

    def permission(task):
        if cancelled():raise Failure('CANCELLED')
        grant=session.authority(copy.deepcopy(task))
        check_grant(grant,task,session.clock())
        return grant

    try:
        if (type(bound) is not BoundWorker or type(session) is not Session
                or type(session.admission) is not AdmissionGate
                or type(session.journal) is not ExecutionJournal
                or type(session.budget) is not DurableTokenBudget
                or session.budget.journal is not session.journal
                or not all(callable(f) for f in (receive,attest_ack,witness_execution,now,cancelled))):
            return finish('NO_DATA','durable_session_admission_and_host_callbacks_required')
        task=bound.task()
        bound.original_for(task)
        pin=bound.pin()
        row.update(agent_ref=pin['session_ref'],node_ref=pin['node_ref'],
                   mission_ref=pin['constraints_ref'],observed_at=current().strftime('%Y-%m-%dT%H:%M:%SZ'))
        permission(task)
        prior=session.journal.lookup(task['run_id'],sha(task))
        if prior is not None:
            row.update(execution_ref=prior['receipt_ref'],observed_at=prior['observed_at'])
            if resources.age_seconds(prior['observed_at'],current())>120:
                return finish('STALE','prior_receipt_expired_not_live')
            if prior['outcome']=='KNOWN':
                return finish('REPLAY','prior_execution_not_new_delivery')
            return finish('NO_DATA','prior_outcome_unknown' if prior['outcome']=='UNKNOWN'
                          else 'prior_not_started_requires_new_request')
        grant=permission(task)
        if session.admission(task,grant,bound,cancelled) is not True:
            evidence=session.admission.record(task)
            return finish('NO_DATA','pre_delivery_'+(evidence['cause'] if evidence else 'admission_missing'))
        envelope=dict(schema='preceptoros.mission-delivery/0',task_ref=sha(task),
            agent_ref=pin['session_ref'],node_ref=pin['node_ref'],mission_ref=pin['constraints_ref'],
            context_ref=pin['selection_ref'],generation=pin['generation'],issued_at=pin['observed_at'])
        envelope['delivery_ref']=sha(envelope)
        row['delivery_ref']=envelope['delivery_ref']
        permission(task)
        ack=receive(copy.deepcopy(envelope))
        if (type(ack) is not dict or any(type(k) is not str for k in ack)
                or any(type(v) is not str or len(v)>128 for v in ack.values())
                or set(ack)!={'schema','delivery_ref','agent_ref','node_ref','context_ref','state','observed_at'}
                or ack['schema']!='preceptoros.mission-ack/0' or ack['state']!='RECEIVED'
                or ack['delivery_ref']!=envelope['delivery_ref'] or ack['agent_ref']!=pin['session_ref']
                or ack['node_ref']!=pin['node_ref'] or ack['context_ref']!=pin['selection_ref']):
            return finish('NO_DATA','ack_mismatch')
        age=resources.age_seconds(ack['observed_at'],current())
        if (not 0<=age<=120 or age>resources.age_seconds(pin['observed_at'],current())
                or attest_ack(copy.deepcopy(envelope),copy.deepcopy(ack)) is not True):
            return finish('NO_DATA','ack_not_witnessed_or_expired')
        row['stages']['received']='RECEIVED'
        permission(task)
        bound.original_for(task)
        receipt=session.execute(task,bound,observed_at=current().strftime('%Y-%m-%dT%H:%M:%SZ'),cancelled=cancelled)
        row.update(execution_ref=receipt['receipt_ref'],observed_at=receipt['observed_at'])
        if not _complete(receipt,task,session):
            return finish('CANCELLED' if receipt['failure_class']=='CANCELLED' else 'NO_DATA',
                          'native_execution_not_verified_'+receipt['failure_class'].lower())
        admission=session.admission.record(task)
        if admission is None or admission['state']!='VERIFIED' or admission['task_ref']!=sha(task):
            return finish('NO_DATA','resource_admission_not_witnessed')
        # Independent execution observation, not inference from receipt success.
        if witness_execution(copy.deepcopy(receipt),copy.deepcopy(task),copy.deepcopy(admission),bound.pin()) is not True:
            return finish('NO_DATA','execution_witness_missing')
        row['stages']['executed']='EXECUTED'
        permission(task)
        bound.original_for(task)
        choice=admission['choice']
        if (session.admission.route(copy.deepcopy(task),bound,choice['node'],choice['backend']) is not True
                or session.admission.lease(copy.deepcopy(task),choice['node'],choice['backend'])!=admission['lease_ref']):
            return finish('NO_DATA','final_route_or_lease_revoked')
        if resources.age_seconds(receipt['observed_at'],current())>120:
            return finish('STALE','execution_receipt_expired_not_live')
        permission(task)
        row['stages'].update(authorized='AUTHORIZED',verified='VERIFIED')
        return finish('VERIFIED','local_task_ack_admission_execution_and_witness_checked')
    except Failure as error:
        return finish('CANCELLED' if error.category=='CANCELLED' else 'NO_DATA',error.category.lower())
    except Exception:
        return finish('NO_DATA','host_channel_or_clock_unknown')
