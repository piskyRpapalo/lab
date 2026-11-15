# Distributed V1 P1: fleet display projection

Technical contract under the existing private Mesa #39 Distributed V1 commission;
assignment/CLAIM stays in Mesa #3. Base 13186eea14e9fe4a24f0b8472923b73d6324d6db.

`fleet_projection.project(nodes, observations, *, now, verify_source)` is pure.
Inputs are up to six inventory-owned opaque SHA256 references and 256 selected
Observation records (node_ref, field, value, source_ref, observed_at, basis).
No registry, collector, network, resource Host, grant or lease is implemented.
Host adapters select fields from MH-01/Nexo NodeCard/rack-map; raw private
manifests must not be passed or published. Unselected fields are never echoed.

Allowed fields: OS, architecture, total/available memory bytes, available storage
bytes, catalog model digests, loaded model digests and a reachability observation.
Model digests denote source reports, not complete or executable weights.
Scalar byte counts exclude booleans and are bounded to signed 64-bit range.
No RAM/UMA/VRAM summation or GPU availability inference is performed.

The trusted host verifies each original source binding through verify_source.
A self-hash is not authentication. Missing/failed verifier => NO_DATA; duplicate
node/field observations => NO_DATA even if identical. Future/invalid timestamps
=> NO_DATA. Age >120 seconds => STALE, preserving original time and basis through
source record; current observations remain OBSERVED or DECLARED as supplied.
Inputs and verifier arguments are defensively copied. Unknown fields fail closed.

Output: bounded local details plus <1024-byte summary, schema
preceptoros.fleet-projection/1, details_ref and receipt_ref. PROJECTED means only
projection completed. authority=none, dispatch_authorized=false,
physical_presence_verified=false. Every node's admission remains
NO_DATA(task_host_route_and_lease_not_bound). This is not a resource packet;
resource_decision/AdmissionGate still require exact task profiles, host route,
independent witness, permission and live lease. No eligibility relabeling.

Tests use synthetic source callbacks only. NO_DATA(real_fleet_source_binding;
cross_cli_live_presence_E2E;authenticated_agent_source_binding;
exclusive_writer_ownership;device_resource_lease). Next: source adapters and
versioned task binding after owner review, retaining all existing LOCAL_ONLY gates.
