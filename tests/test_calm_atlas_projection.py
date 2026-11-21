"""CALM Atlas provenance and temporal refusal gates; all witnesses synthetic."""
import copy, hashlib, json, unittest
from datetime import datetime, timezone
from meta_harness.calm_atlas_projection import ARCH,TIMELINE,audit
NOW=datetime(2026,11,21,2,0,tzinfo=timezone.utc)
HEAD,BLOB="a"*40,"b"*40
def enc(x):return json.dumps(x,sort_keys=True,separators=(",",":")).encode()
def node(name,boundary="DECLARED"):
 x={"unique-id":name,"node-type":"service","name":name,"description":"source-level only",
    "metadata":{"hexelion":{"source_ref":"repo/"+name,"source_commit":HEAD,
                            "source_blob":BLOB,"boundary":boundary,"observed":"NO_DATA"}}}
 if boundary=="PRIVILEGED_NATIVE":
  x["controls"]={"no-public-to-native":{"description":"deny",
    "requirements":[{"requirement-url":"https://example.org/control",
                     "config":{"remote":"DENY","runtime_attested":False}}]}}
 return x
def edge(name,a,b):
 return {"unique-id":name,"description":"code only",
         "relationship-type":{"connects":{"source":{"node":a},"destination":{"node":b}}}}
def architecture(extra=False):
 d={"$schema":ARCH,"nodes":[node("android"),node("bridge","PRIVILEGED_NATIVE"),
                             node("gguf"),node("web","PUBLIC_REMOTE")],
    "relationships":[edge("call-bridge","android","bridge"),edge("call-model","bridge","gguf")],
    "flows":[{"unique-id":"local","name":"local","description":"code only",
      "transitions":[{"relationship-unique-id":"call-bridge","sequence-number":1,"description":"local"},
                     {"relationship-unique-id":"call-model","sequence-number":2,"description":"local"}]}]}
 if extra:d["nodes"].append(node("lab"))
 return d
def moment(date,path,data):
 return {"unique-id":"moment"+date[11:13]+date[14:16],"node-type":"moment",
         "name":"version","description":"versioned source",
         "valid-from":date[:10],"details":{"detailed-architecture":path},
         "metadata":{"hexelion":{"source_ref":"lab/commit","source_commit":HEAD,
              "source_blob":BLOB,"snapshot_sha256":hashlib.sha256(data).hexdigest(),
              "event_at":date,"observed_at":None,"permission":"READ_ONLY",
              "witness_ref":"synthetic","state":"DECLARED"}}}
class CalmAtlasGate(unittest.TestCase):
 def setUp(self):
  a,b=enc(architecture()),enc(architecture(True))
  self.p1,self.p2="./snapshots/a.json","./snapshots/b.json"
  self.snap={self.p1:a,self.p2:b}
  m1=moment("2026-11-21T00:51:15Z",self.p1,a)
  m2=moment("2026-11-21T01:01:15Z",self.p2,b)
  self.timeline={"$schema":TIMELINE,"moments":[m1,m2],"current-moment":m2["unique-id"]}
  self.calls=[]
 def schema(self,ref,obj):return obj.get("$schema")==ref
 def witness(self,ref,*other):
  self.calls.append(ref);return True
 def observed(self,ref,commit,date,refw,state):return refw=="synthetic" and state=="OBSERVED"
 def run_case(self,t=None,s=None,**kwargs):
  return audit(copy.deepcopy(self.timeline if t is None else t),
               dict(self.snap if s is None else s),
               validate_schema=self.schema,verify_source=self.witness,
               verify_observation=self.observed,now=NOW,**kwargs)
 def mutate(self,operation,cause):
  d=architecture();operation(d);raw=enc(d)
  t=copy.deepcopy(self.timeline)
  t["moments"][0]["metadata"]["hexelion"]["snapshot_sha256"]=hashlib.sha256(raw).hexdigest()
  s=dict(self.snap);s[self.p1]=raw
  self.assertEqual(self.run_case(t,s)["cause"],cause)
 def test_valid_history_not_live(self):
  r=self.run_case()
  self.assertEqual(r["state"],"DOCUMENT_CHECKED")
  self.assertFalse(r["runtime_proven"])
  self.assertFalse(r["execution_authorized"])
  self.assertEqual(r["deltas"][0]["nodes"]["added"],1)
  self.assertEqual(len(self.calls),7)
  self.assertNotIn("lab/commit",str(r))
 def test_deterministic_sha(self):
  self.assertEqual(self.run_case()["receipt_sha256"],self.run_case()["receipt_sha256"])
 def test_no_schema_checker(self):
  r=audit(self.timeline,self.snap,validate_schema=None,verify_source=self.witness,now=NOW)
  self.assertEqual(r["cause"],"verifier_missing")
 def test_no_source_checker(self):
  r=audit(self.timeline,self.snap,validate_schema=self.schema,verify_source=None,now=NOW)
  self.assertEqual(r["cause"],"verifier_missing")
 def test_component_witness_denied(self):
  r=audit(self.timeline,self.snap,validate_schema=self.schema,
          verify_source=lambda ref,*a:not ref.endswith("gguf"),now=NOW)
  self.assertEqual(r["cause"],"source_witness_denied")
 def test_extend_ttl_denied(self):
  self.assertEqual(self.run_case(ttl_s=600)["cause"],"clock_or_ttl_invalid")
 def test_path_traversal_denied(self):
  t=copy.deepcopy(self.timeline);t["moments"][0]["details"]["detailed-architecture"]="./../private"
  self.assertEqual(self.run_case(t)["cause"],"unsafe_snapshot_reference")
 def test_external_url_denied(self):
  t=copy.deepcopy(self.timeline);t["moments"][0]["details"]["detailed-architecture"]="https://example.org/file"
  self.assertEqual(self.run_case(t)["cause"],"unsafe_snapshot_reference")
 def test_sha_mismatch_denied(self):
  t=copy.deepcopy(self.timeline);t["moments"][0]["metadata"]["hexelion"]["snapshot_sha256"]="f"*64
  self.assertEqual(self.run_case(t)["cause"],"snapshot_sha_mismatch")
 def test_duplicate_json_key_denied(self):
  data=b'{"$schema":"'+ARCH.encode()+b'","nodes":[],"nodes":[],"relationships":[]}'
  t=copy.deepcopy(self.timeline);t["moments"][0]["metadata"]["hexelion"]["snapshot_sha256"]=hashlib.sha256(data).hexdigest()
  s=dict(self.snap);s[self.p1]=data
  self.assertEqual(self.run_case(t,s)["cause"],"malformed_document")
 def test_dangling_node(self):
  self.mutate(lambda g:g["relationships"][1]["relationship-type"]["connects"]["destination"].update(node="ghost"),"dangling_node")
 def test_public_native_relation(self):
  self.mutate(lambda g:g["relationships"].append(edge("bad","web","bridge")),"public_native_denied")
 def test_mutated_owner_boundary(self):
  self.mutate(lambda g:g["nodes"][1]["controls"]["no-public-to-native"]["requirements"][0]["config"].update(remote="ALLOW"),"boundary_mutated")
 def test_false_live(self):
  self.mutate(lambda g:g["nodes"][2]["metadata"]["hexelion"].update(observed="LIVE"),"false_runtime_promotion")
 def test_node_without_source(self):
  self.mutate(lambda g:g["nodes"][2]["metadata"]["hexelion"].pop("source_ref"),"component_source_missing")
 def test_flow_missing_edge(self):
  self.mutate(lambda g:g["flows"][0]["transitions"][1].update(**{"relationship-unique-id":"ghost"}),"flow_relation_missing")
 def test_flow_duplicate_seq(self):
  self.mutate(lambda g:g["flows"][0]["transitions"][1].update(**{"sequence-number":1}),"flow_order")
 def test_reversed_timeline(self):
  t=copy.deepcopy(self.timeline);t["moments"].reverse()
  self.assertEqual(self.run_case(t)["cause"],"moment_order")
 def test_unrequested_private_snapshot(self):
  s=dict(self.snap);s["./private"]=b"password"
  self.assertEqual(self.run_case(s=s)["cause"],"extra_snapshot_input")
 def test_predates_version_no_data(self):
  t=copy.deepcopy(self.timeline);t["moments"][1]["metadata"]["hexelion"].update(
       observed_at="2026-11-20T00:00:00Z",state="LIVE")
  self.assertEqual(self.run_case(t)["history"][1]["observed"]["cause"],"observation_predates_version")
 def test_stale_after_version(self):
  t=copy.deepcopy(self.timeline);t["moments"][1]["metadata"]["hexelion"].update(
       observed_at="2026-11-21T01:02:00Z",state="LIVE")
  self.assertEqual(self.run_case(t)["history"][1]["observed"]["state"],"STALE")
 def test_recent_without_grant_no_data(self):
  t=copy.deepcopy(self.timeline);t["moments"][1]["metadata"]["hexelion"].update(
       observed_at="2026-11-21T01:59:40Z",state="OBSERVED")
  self.assertEqual(self.run_case(t)["history"][1]["observed"]["cause"],"observation_not_authorized")
 def test_recent_attested_only_observed(self):
  t=copy.deepcopy(self.timeline);t["moments"][1]["metadata"]["hexelion"].update(
       observed_at="2026-11-21T01:59:40Z",state="OBSERVED",permission="OBSERVE")
  r=self.run_case(t)
  self.assertEqual(r["history"][1]["observed"]["state"],"OBSERVED")
  self.assertFalse(r["runtime_proven"])
 def test_future_no_data(self):
  t=copy.deepcopy(self.timeline);t["moments"][1]["metadata"]["hexelion"].update(
       observed_at="2026-11-22T00:00:00Z")
  self.assertEqual(self.run_case(t)["history"][1]["observed"]["cause"],"future_observation")
 def test_large_snapshot(self):
  s=dict(self.snap);s[self.p1]=b"x"*16385
  self.assertEqual(self.run_case(s=s)["cause"],"snapshot_missing")
 def test_reused_path(self):
  t=copy.deepcopy(self.timeline);t["moments"][1]["details"]["detailed-architecture"]=self.p1
  self.assertEqual(self.run_case(t)["cause"],"unsafe_snapshot_reference")

 def test_indirect_public_to_native_bridge(self):
  self.mutate(lambda g:(g["nodes"].append(node("relay")),
                        g["relationships"].append(edge("public-relay","web","relay")),
                        g["relationships"].append(edge("relay-native","relay","bridge"))),"public_native_denied")
 def test_two_relays_to_native_bridge(self):
  self.mutate(lambda g:(g["nodes"].extend([node("relay-a"),node("relay-b")]),
                        g["relationships"].extend([edge("web-a","web","relay-a"),
                            edge("a-b","relay-a","relay-b"),
                            edge("b-native","relay-b","bridge")])),"public_native_denied")
 def test_reversed_flow_from_public_to_native(self):
  self.mutate(lambda g:(g["relationships"].append(edge("native-to-public","bridge","web")),
       g["flows"].append({"unique-id":"reverse-access","name":"reverse","description":"test",
       "transitions":[{"relationship-unique-id":"native-to-public","sequence-number":1,
                       "description":"reverse","direction":"destination-to-source"}]})),"public_native_denied")
 def test_native_outbound_without_reverse_is_allowed(self):
  g=architecture();g["relationships"].append(edge("native-to-web","bridge","web"))
  raw=enc(g);t=copy.deepcopy(self.timeline)
  t["moments"][0]["metadata"]["hexelion"]["snapshot_sha256"]=hashlib.sha256(raw).hexdigest()
  snapshots=dict(self.snap);snapshots[self.p1]=raw
  self.assertEqual(self.run_case(t,snapshots)["state"],"DOCUMENT_CHECKED")
