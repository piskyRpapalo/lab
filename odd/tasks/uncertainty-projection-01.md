# Uncertain execution · APP consumption contract

The LAB host may project an existing uncertain journal claim as an additive
`preceptoros.lab.uncertainty-ack/1` record with `kind=projection`. Text, speech
and machine views carry the same projection_ref and the same state. UNKNOWN is
never rewritten as success/failure; reservation is RETAINED with bounded token
count or NO_DATA with cause. Acknowledgement is HITL_REQUIRED,
HUMAN_ACKNOWLEDGED or AUTHORITY_NOT_VERIFIED; memory promotion is not authorized.

`meta_harness.uncertainty_views.project(journal, task, observed_at=host_time)`
reads a trusted host journal and rechecks the host's human/fence witness.
`views(record)` builds the three representations; `verify(packet, journal,
task, observed_at=host_time)` recomputes them against the host. The record
self-hash alone is not authority. TTL=0: do not cache an acknowledgement as
currently valid; re-read/reverify with a host clock before every use. A change,
revocation, missing journal or absent witness must not be displayed as approved.

Reproducible synthetic examples: `python3 -B -m unittest tests.test_uncertainty_views`.
The fixtures use only temporary SQLite files and fake human/fence witnesses;
they do not sign, invoke a model, touch APP, or activate a service. The human
acknowledgement record remains a decision, not proof of an execution outcome.
Claude owns rendering and must consume the same record/ref for all modalities.
Real host authority/fence adapters, APP wiring and live E2E remain NO_DATA.
