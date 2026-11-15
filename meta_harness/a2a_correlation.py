"""Host-supplied A2A correlation, NOT authentication, authorization or transport."""
from datetime import datetime, timedelta, timezone
from copy import deepcopy
from .delegation import HEX, LABEL, encode, sha

REQUEST = 'preceptoros.lab.a2a-request/1'
OBSERVATION = 'preceptoros.lab.a2a-observation/1'
RESULT = 'preceptoros.lab.a2a-correlation/1'
REQ = {'schema','trace_id','agent','session_ref','generation','mission_ref',
       'scope_ref','source_ref','issued_at','expires_at','mode','human_signoff'}
OBS = {'schema','trace_id','request_ref','agent','session_ref','generation',
       'source_ref','observed_at','kind','exit_code','reply_ref'}

def _hex(x):
    return type(x) is str and HEX.fullmatch(x) is not None

def _date(x):
    if type(x) is not str or len(x)!=20 or not x.endswith('Z'):
        raise ValueError('invalid_clock')
    result=datetime.strptime(x,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    if result.strftime('%Y-%m-%dT%H:%M:%SZ')!=x:
        raise ValueError('invalid_clock')
    return result

def _done(out,state,cause):
    out.update(state=state,cause=cause)
    out['receipt_ref']=sha(out)
    if len(encode(out))>=1024:
        raise ValueError('receipt_bound')
    return out

def correlate(request, observation, *, now, witness, seen_request_refs=()):
    """No process invocation. Witness is caller-owned and not authenticated here.

    ACK only proves an associated host-supplied observation, not the replying
    agent's true identity, safe behavior, provenance, signer or grant.
    """
    out=dict(schema=RESULT,state='NO_DATA',cause='unobserved',
             agent=None,request_ref=None,observation_ref=None,
             authority='none',permissions='none',human_signoff=False,
             authentication='NO_DATA(original_agent_unattested)',
             replay='NO_DATA(durable_replay_store_not_bound)',
             evidence='HOST_SUPPLIED_UNVERIFIED')
    try:
        # Freeze caller-owned metadata before validation: witness callbacks must not
        # mutate the object whose digest and binding were already checked.
        if type(request) is not dict or type(observation) is not dict:
            return _done(out,'NO_DATA','invalid_schema_or_size')
        # Keys must also be exact strings: hostile key __deepcopy__ hooks
        # must not run before the closed-schema validation.
        if (any(type(k) is not str for k in request)
                or any(type(k) is not str for k in observation)):
            return _done(out,'NO_DATA','invalid_schema_or_size')
        # Reject non-JSON value types before deepcopy: hostile __deepcopy__ hooks
        # must never execute while inspecting untrusted envelope metadata.
        safe=(type(None),bool,int,float,str)
        if (any(type(v) not in safe for v in request.values())
                or any(type(v) not in safe for v in observation.values())):
            return _done(out,'NO_DATA','invalid_schema_or_size')
        request, observation = deepcopy(request), deepcopy(observation)
        if (type(request) is not dict or set(request)!=REQ
                or type(observation) is not dict or set(observation)!=OBS
                or len(encode(request))>1024 or len(encode(observation))>1024):
            return _done(out,'NO_DATA','invalid_schema_or_size')
        if (request['schema']!=REQUEST or observation['schema']!=OBSERVATION
                or type(request['trace_id']) is not str
                or LABEL.fullmatch(request['trace_id']) is None
                or request['agent'] not in ('junie','hexelion')
                or type(request['generation']) is not int
                or not 1<=request['generation']<2**63
                or any(not _hex(request[k]) for k in
                       ('session_ref','mission_ref','scope_ref','source_ref'))
                or request['mode']!='READ_ONLY' or request['human_signoff'] is not False):
            return _done(out,'NO_DATA','invalid_or_unauthorized_request')
        ref=sha(request)
        out.update(agent=request['agent'],request_ref=ref)
        if (type(seen_request_refs) not in (tuple,list)
                or len(seen_request_refs)>256
                or any(not _hex(x) for x in seen_request_refs)):
            return _done(out,'NO_DATA','invalid_replay_evidence')
        if ref in seen_request_refs:
            return _done(out,'NO_DATA','replay_observed')
        if (observation['trace_id']!=request['trace_id']
                or observation['request_ref']!=ref
                or observation['agent']!=request['agent']
                or observation['session_ref']!=request['session_ref']
                or type(observation['generation']) is not int
                or observation['generation']!=request['generation']
                or observation['source_ref']!=request['source_ref']
                or observation['kind'] not in ('ACK','NACK','ERROR')
                or type(observation['exit_code']) is not int
                or not 0<=observation['exit_code']<=255
                or not _hex(observation['reply_ref'])):
            return _done(out,'NO_DATA','response_binding_mismatch')
        out['observation_ref']=sha(observation)
        issued,expires,observed,checked=(
            _date(request['issued_at']),_date(request['expires_at']),
            _date(observation['observed_at']),_date(now))
        if not timedelta(0)<expires-issued<=timedelta(seconds=120):
            return _done(out,'NO_DATA','invalid_lifetime')
        if observed<issued or checked<observed:
            return _done(out,'NO_DATA','invalid_chronology')
        if observed>expires or checked>expires:
            return _done(out,'NO_DATA','expired')
        if not callable(witness):
            return _done(out,'NO_DATA','host_capture_missing')
        try:
            accepted=witness(deepcopy(request),deepcopy(observation))
        except Exception:
            return _done(out,'NO_DATA','host_capture_error')
        if accepted is not True:
            return _done(out,'NO_DATA','host_capture_unavailable')
        if observation['kind']=='ACK' and observation['exit_code']==0:
            return _done(out,'CORRELATED_UNVERIFIED','ack_correlated_not_authenticated')
        if observation['kind']=='NACK' and observation['exit_code']==0:
            return _done(out,'DECLINED_UNVERIFIED','nack_correlated_not_authenticated')
        return _done(out,'NO_DATA','unresolved_agent_error')
    except Exception:
        return _done(out,'NO_DATA','invalid_untrusted_evidence')

def synthetic_fixture():
    """Not the actual Junie handshake or proof of an agent's identity."""
    req=dict(schema=REQUEST,trace_id='synthetic-a2a',agent='junie',
             session_ref='a'*64,generation=1,mission_ref='b'*64,
             scope_ref='c'*64,source_ref='d'*64,
             issued_at='2026-11-15T02:50:00Z',expires_at='2026-11-15T02:51:00Z',
             mode='READ_ONLY',human_signoff=False)
    obs=dict(schema=OBSERVATION,trace_id=req['trace_id'],request_ref=sha(req),
             agent='junie',session_ref=req['session_ref'],generation=1,
             source_ref=req['source_ref'],observed_at='2026-11-15T02:50:07Z',
             kind='ACK',exit_code=0,reply_ref='e'*64)
    return req,obs
