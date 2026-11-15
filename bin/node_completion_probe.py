"""Operator-only public completion probe over existing SSH; not APP task authority."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import select
import signal
import shlex
import subprocess
import time

VALUES = [7, -2, 7, 0, 11]
LIMIT = 1024
REMOTE = '''import sys,json,hashlib,datetime
r=json.loads(sys.stdin.buffer.read(1025))
def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
assert set(r)=={'schema','node_ref','nonce','context_ref','issued_at','expires_at','values','request_ref'}
assert r['schema']=='public-sort-probe/1' and r['values']==[7,-2,7,0,11]
assert r['request_ref']==hashlib.sha256(enc({k:v for k,v in r.items() if k!='request_ref'})).hexdigest()
now=datetime.datetime.now(datetime.timezone.utc)
parse=lambda t:datetime.datetime.strptime(t,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)
assert parse(r['issued_at'])<=now<=parse(r['expires_at'])
out={k:r[k] for k in ('node_ref','nonce','context_ref','request_ref')}
out.update(schema='public-sort-completion/1',values=sorted(r['values']),observed_at=now.strftime('%Y-%m-%dT%H:%M:%SZ'))
sys.stdout.buffer.write(enc(out)+b'\\n')
'''


def encoded(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(v):
    return hashlib.sha256(encoded(v)).hexdigest()


def ref(v):
    return type(v) is str and re.fullmatch('[0-9a-f]{64}', v) is not None


def stamp(v):
    if type(v) is not str:
        raise ValueError('clock_invalid')
    return datetime.strptime(v, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def request(node_ref, context_ref, nonce, now):
    if (not ref(node_ref) or not ref(context_ref) or type(nonce) is not str
            or re.fullmatch('[0-9a-f]{32}', nonce) is None
            or type(now) is not datetime or now.utcoffset() != timedelta(0)):
        raise ValueError('request_invalid')
    r=dict(schema='public-sort-probe/1',node_ref=node_ref,nonce=nonce,
           context_ref=context_ref,issued_at=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
           expires_at=(now+timedelta(seconds=30)).strftime('%Y-%m-%dT%H:%M:%SZ'),values=VALUES[:])
    r['request_ref']=digest(r)
    return r


def verify_completion(r, reply, now):
    """Correlation/time/result only; this function never authenticates a channel."""
    try:
        if (type(r) is not dict or type(reply) is not dict
                or type(now) is not datetime or now.utcoffset()!=timedelta(0)
                or any(type(k) is not str for k in r) or any(type(k) is not str for k in reply)
                or set(r)!={'schema','node_ref','nonce','context_ref','issued_at','expires_at','values','request_ref'}
                or r['schema']!='public-sort-probe/1'
                or not all(ref(r[k]) for k in ('node_ref','context_ref','request_ref'))
                or type(r['nonce']) is not str or re.fullmatch('[0-9a-f]{32}',r['nonce']) is None
                or any(type(reply.get(k)) is not str for k in ('schema','node_ref','nonce','context_ref','request_ref','observed_at'))
                or any(type(r.get(k)) is not str for k in ('schema','node_ref','nonce','context_ref','request_ref','issued_at','expires_at'))
                or type(r['values']) is not list or any(type(v) is not int for v in r['values'])
                or stamp(r['expires_at'])-stamp(r['issued_at'])!=timedelta(seconds=30)
                or set(reply)!={'schema','node_ref','nonce','context_ref','request_ref','values','observed_at'}
                or reply['schema']!='public-sort-completion/1'
                or r['request_ref']!=digest({k:v for k,v in r.items() if k!='request_ref'})
                or any(reply[k]!=r[k] for k in ('node_ref','nonce','context_ref','request_ref'))
                or type(reply['values']) is not list
                or any(type(v) is not int for v in reply['values'])
                or reply['values']!=sorted(VALUES) or r['values']!=VALUES
                or not stamp(r['issued_at'])<=stamp(reply['observed_at'])<=now<=stamp(r['expires_at'])):
            return False
        return True
    except (ValueError, KeyError, TypeError, OverflowError):
        return False


def ssh_transport(alias, payload):
    """One owned process, no retry or SSH host-key changes; bounded stdout/deadline."""
    command='python3 -c '+shlex.quote(REMOTE)
    args=['ssh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
          '-o','UpdateHostKeys=no','-o','ControlMaster=no','-o','ControlPath=none',
          '-o','ConnectTimeout=3','-o','ConnectionAttempts=1',alias,command]
    deadline=time.monotonic()+8
    p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True)
    try:
        p.stdin.write(payload);p.stdin.close()
        buf=b''
        while True:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('probe_timeout')
            ready,_,_=select.select([p.stdout],[],[],remaining)
            if not ready:raise TimeoutError('probe_timeout')
            chunk=os.read(p.stdout.fileno(),LIMIT+1-len(buf))
            if not chunk:break
            buf+=chunk
            if len(buf)>LIMIT:raise ValueError('probe_output_bound')
        if p.wait(timeout=max(.001,deadline-time.monotonic()))!=0:
            raise ValueError('probe_transport_failed')
        return buf
    finally:
        if p.poll() is None:
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=.3)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
        p.stdout.close()
        if not p.stdin.closed:p.stdin.close()


def explicit_alias(alias):
    try:
        p=Path.home()/'.ssh/config'
        with p.open('rb') as f:raw=f.read(65537)
        if len(raw)>65536:return False
        for line in raw.decode().splitlines():
            tokens=shlex.split(line,comments=True)
            if tokens and tokens[0].lower()=='host' and alias in tokens[1:]:return True
    except (OSError,ValueError):pass
    return False


def probe(alias, context_ref, *, transport=None, clock=None):
    """Injected transports are ALWAYS SIMULATED. A portable receipt is not signed."""
    if type(alias) is not str or re.fullmatch('[a-z][a-z0-9-]{0,31}',alias) is None:
        raise ValueError('alias_invalid')
    now=clock or (lambda:datetime.now(timezone.utc))
    r=request(digest({'operator_ssh_alias':alias}),context_ref,secrets.token_hex(16),now())
    row=dict(schema='preceptoros.remote-completion-probe/1',state='NO_DATA',cause='unobserved',
        origin='SIMULATED' if transport is not None else 'REAL',node_ref=r['node_ref'],
        request_ref=r['request_ref'],context_ref=context_ref,program_ref=hashlib.sha256(REMOTE.encode()).hexdigest(),
        authority='none',native_dispatch_authorized=False,APP_E2E=False,
        physical_alias_binding='NO_DATA',portable_authentication='NO_DATA',attempts=0)
    try:
        if transport is None and not explicit_alias(alias):
            row['cause']='explicit_existing_ssh_alias_missing'
        else:
            row['attempts']=1
            raw=(transport or ssh_transport)(alias,encoded(r))
            if type(raw) is not bytes or len(raw)>LIMIT:raise ValueError('invalid_reply')
            def unique(pairs):
                d={}
                for k,v in pairs:
                    if k in d:raise ValueError('duplicate_key')
                    d[k]=v
                return d
            reply=json.loads(raw,object_pairs_hook=unique)
            if verify_completion(r,reply,now()):
                row.update(state='PROBE_COMPLETED',cause='correlation_and_result_checked',reply_ref=digest(reply))
            else:row['cause']='completion_mismatch_or_expired'
    except (OSError,ValueError,TypeError,TimeoutError,subprocess.TimeoutExpired,RecursionError):
        row['cause']='transport_or_protocol_unknown_no_retry'
    row['receipt_ref']=digest(row)
    if len(encoded(row))>=LIMIT:raise ValueError('receipt_bound')
    return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ssh-alias',required=True)
    p.add_argument('--context-ref',required=True)
    a=p.parse_args();r=probe(a.ssh_alias,a.context_ref);print(encoded(r).decode())
    return 0 if r['state']=='PROBE_COMPLETED' else 1


if __name__=='__main__':raise SystemExit(main())
