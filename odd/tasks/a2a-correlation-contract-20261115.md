# A2A correlation · Evidence without authority · 2026-11-15

Status: PURE CONTRACT / SYNTHETIC. Owner: Codex GPT-6 Web. Claim: private Mesa #39 comment 6888191222. Soberano signs exact-head merges.

Reuse LAB agent_presence.py and agent_presence_sources.py for advisory presence, execution_journal.py for host-owned replay, transports.py for transport, F6 #151 for synthetic economic A2A and Sovereign S1 for permissions. This is not another transport, daemon, command runner or registry.

The new a2a_correlation.py accepts a bounded host-issued request and a host-supplied CLI observation, binds agent, trace_id, session, epoch, mission/scope/source through request digest, exit status, timestamps and host-owned witness callback. Response may be CORRELATED_UNVERIFIED, DECLINED_UNVERIFIED or NO_DATA(cause). It NEVER returns authenticated agent identity, authorization, execution power, host attestation, human signoff or durable replay guarantee. Caller supplied witnesses and SHA do not establish original source provenance.

All metadata are strict and closed. Raw prompts, raw outputs, paths, secrets and unknown grants are rejected. The receipt is under 1,024 bytes. Unit fixture is synthetic and is not the actual one-shot Junie CLI ACK. No model inference or process launch occurs in this module.

Reproduce: python3 -m unittest tests.test_a2a_correlation (twice); existing agent_presence and transport tests; full LAB tests x2 on exact PR head.

Next: authenticated host adapter, original process start/exit evidence and source ownership; no changes to active Junie or Codex CLI sessions. NO_DATA(agent_source_authentication,independent_host_witness,durable_replay,Hexelion_116B_A2A_E2E,S1_A2A_authorization).
