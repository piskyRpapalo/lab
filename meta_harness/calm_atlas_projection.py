"""FINOS CALM v1.3 Timeline: pure, bounded source-backed review. No authority or I/O.

Host must provide offline schema validation, source witness, observation witness
and exact bytes. A passed document never proves LIVE, OWNER or execution.
"""
from datetime import datetime, timedelta
from hashlib import sha256
import json, re
ARCH="https://calm.finos.org/release/1.3/meta/calm.json"
TIMELINE="https://calm.finos.org/release/1.3/meta/calm-timeline.json"
H1=re.compile(r"[a-f0-9]{40}\Z")
H256=re.compile(r"[a-f0-9]{64}\Z")
PATH=re.compile(r"\./[A-Za-z0-9_./-]{1,140}\Z")
def compact(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
def fail(cause):
    return {"state":"NO_DATA","cause":cause,"runtime_proven":False,"execution_authorized":False,"authority":"NONE"}
def utc(s):
    if type(s) is not str or not s.endswith("Z"):raise ValueError("UTC")
    v=datetime.fromisoformat(s[:-1]+"+00:00")
    if v.utcoffset()!=timedelta(0):raise ValueError("UTC")
    return v
def source(m):
    return (type(m) is dict and type(m.get("source_ref")) is str
            and 0<len(m["source_ref"])<=160 and type(m.get("source_commit")) is str
            and type(m.get("source_blob")) is str and H1.fullmatch(m["source_commit"])
            and H1.fullmatch(m["source_blob"]))
def safe(path):
    return (type(path) is str and PATH.fullmatch(path) is not None
            and not path.startswith("./.") and not path.endswith(("/", "/.."))
            and not any(s in path for s in ("//","/../","/./")))
def parse(raw):
    if type(raw) is not bytes or not 1<=len(raw)<=16384:raise ValueError("bytes")
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise ValueError("duplicate")
            d[k]=v
        return d
    def constant(_):raise ValueError("nonfinite")
    return json.loads(raw.decode("utf8","strict"),object_pairs_hook=pairs,parse_constant=constant)
def graph(g):
    nodes,rels=g.get("nodes"),g.get("relationships")
    if type(nodes) is not list or type(rels) is not list or not 1<=len(nodes)<=64 or len(rels)>128:return "graph_bounds"
    ids=[n["unique-id"] for n in nodes]
    if len(set(ids))!=len(ids):return "duplicate_node"
    pool={n["unique-id"]:n for n in nodes}
    for n in nodes:
        m=n.get("metadata",{}).get("hexelion",{})
        if not source(m):return "component_source_missing"
        if m.get("observed") in ("LIVE","VERIFIED","MEASURED"):return "false_runtime_promotion"
        if m.get("boundary")=="PRIVILEGED_NATIVE":
            try:
                c=n["controls"]["no-public-to-native"]["requirements"][0]["config"]
                if c["remote"]!="DENY" or c["runtime_attested"] is not False:return "boundary_mutated"
            except (KeyError,TypeError,IndexError):return "boundary_missing"
    directed={};names=[]
    for r in rels:
        rid=r["unique-id"];names.append(rid);typ=r["relationship-type"]
        if "connects" in typ:
            a,b=typ["connects"]["source"]["node"],typ["connects"]["destination"]["node"]
            refs=(a,b);directed[rid]=refs
            if a in pool and b in pool:
                x=pool[a]["metadata"]["hexelion"].get("boundary")
                y=pool[b]["metadata"]["hexelion"].get("boundary")
                if x=="PUBLIC_REMOTE" and y=="PRIVILEGED_NATIVE":return "public_native_denied"
        elif "composed-of" in typ:
            d=typ["composed-of"];refs=(d["container"],*d["nodes"])
        else:return "relationship_unsupported"
        if not all(ref in pool for ref in refs):return "dangling_node"
    if len(set(names))!=len(names):return "duplicate_relationship"
    for f in g.get("flows",[]):
        transitions=f["transitions"]
        if [t["sequence-number"] for t in transitions]!=list(range(1,len(transitions)+1)):return "flow_order"
        prev=None
        for t in transitions:
            pair=directed.get(t["relationship-unique-id"])
            if pair is None:return "flow_relation_missing"
            a,b=pair
            if t.get("direction")=="destination-to-source":a,b=b,a
            if prev is not None and prev!=a:return "flow_disconnected"
            prev=b
    return None
def delta(old,new):
    out={}
    for key in ("nodes","relationships"):
        a={n["unique-id"]:sha256(compact(n)).hexdigest() for n in old[key]}
        b={n["unique-id"]:sha256(compact(n)).hexdigest() for n in new[key]}
        out[key]={"added":len(b.keys()-a.keys()),"removed":len(a.keys()-b.keys()),
                  "modified":sum(a[k]!=b[k] for k in a.keys()&b.keys())}
    return out
def age(m,now,verify,ttl):
    t=m.get("observed_at")
    if t is None:return {"state":"NO_DATA","cause":"observation_missing"}
    try:
        stamp=utc(t)
        if stamp<utc(m["event_at"]):return {"state":"NO_DATA","cause":"observation_predates_version"}
    except (ValueError,TypeError,KeyError):return {"state":"NO_DATA","cause":"time_invalid"}
    if stamp>now:return {"state":"NO_DATA","cause":"future_observation"}
    if (now-stamp).total_seconds()>ttl:return {"state":"STALE","cause":"observation_expired"}
    w=m.get("witness_ref")
    if m.get("permission")!="OBSERVE" or type(w) is not str or not w or not callable(verify):
        return {"state":"NO_DATA","cause":"observation_not_authorized"}
    try:valid=verify(m["source_ref"],m["source_commit"],t,w,m.get("state")) is True
    except Exception:valid=False
    return {"state":"OBSERVED","cause":"not_live"} if valid else {"state":"NO_DATA","cause":"witness_rejected"}
def audit(timeline,snapshots,*,validate_schema,verify_source,now,verify_observation=None,ttl_s=120):
    """Success is DOCUMENT_CHECKED, never an operating/privileged state."""
    if type(now) is not datetime or now.utcoffset()!=timedelta(0) or type(ttl_s) is not int or not 1<=ttl_s<=120:return fail("clock_or_ttl_invalid")
    if type(timeline) is not dict or type(snapshots) is not dict:return fail("inputs_invalid")
    if not callable(validate_schema) or not callable(verify_source):return fail("verifier_missing")
    try:
        if len(compact(timeline))>16384 or timeline.get("$schema")!=TIMELINE or validate_schema(TIMELINE,timeline) is not True:return fail("timeline_schema_invalid")
        moments=timeline.get("moments")
        if type(moments) is not list or not 1<=len(moments)<=12:return fail("moment_bounds")
        ids=[m["unique-id"] for m in moments]
        if len(set(ids))!=len(ids) or timeline.get("current-moment") not in ids:return fail("moment_identity")
        used=set();witnessed=set();history=[];changes=[];old=None;last=None
        for m in moments:
            ref=m["details"]["detailed-architecture"]
            if not safe(ref) or ref in used:return fail("unsafe_snapshot_reference")
            used.add(ref);meta=m["metadata"]["hexelion"];digest=meta.get("snapshot_sha256")
            if not source(meta) or type(digest) is not str or not H256.fullmatch(digest):return fail("snapshot_provenance_missing")
            when=utc(meta["event_at"])
            if m.get("valid-from")!=when.date().isoformat() or (last is not None and when<=last):return fail("moment_order")
            last=when;raw=snapshots.get(ref)
            if type(raw) is not bytes or not 1<=len(raw)<=16384:return fail("snapshot_missing")
            if sha256(raw).hexdigest()!=digest:return fail("snapshot_sha_mismatch")
            doc=parse(raw)
            if doc.get("$schema")!=ARCH or validate_schema(ARCH,doc) is not True:return fail("architecture_schema_invalid")
            err=graph(doc)
            if err:return fail(err)
            proofs=[(meta["source_ref"],meta["source_commit"],meta["source_blob"],digest)]
            for node in doc["nodes"]:
                p=node["metadata"]["hexelion"];proofs.append((p["source_ref"],p["source_commit"],p["source_blob"],None))
            for proof in proofs:
                if proof in witnessed:continue
                witnessed.add(proof)
                if verify_source(*proof) is not True:return fail("source_witness_denied")
            history.append({"moment":m["unique-id"],"valid_from":m["valid-from"],
                            "source_sha256":sha256(meta["source_ref"].encode()).hexdigest(),
                            "snapshot_sha256":digest,"observed":age(meta,now,verify_observation,ttl_s)})
            if old is not None:changes.append(delta(old,doc))
            old=doc
        if set(snapshots)!=used:return fail("extra_snapshot_input")
        out={"state":"DOCUMENT_CHECKED","cause":None,"authority":"NONE","runtime_proven":False,
             "execution_authorized":False,"calm_version":"1.3","history":history,"deltas":changes,
             "nodes_current":len(old["nodes"]),"relationships_current":len(old["relationships"])}
        out["receipt_sha256"]=sha256(compact(out)).hexdigest()
        return out
    except (KeyError,TypeError,ValueError,IndexError,OverflowError,UnicodeError):return fail("malformed_document")
    except Exception:return fail("host_verification_failed")
