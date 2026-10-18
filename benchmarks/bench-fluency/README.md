# Mechanical fluency M1–M4

Scope and results source: `~/p0x/estudios/bench-fluency/MECANICO.md:1-40`, SHA-256 `514886157f2328c480f555ff06b8f1f048fc2f42774d803f728ee8ad8c7053b2`. Runner `mecanico_runner.py`, SHA-256 `b9648863911c74655d7cea206d05db17c4728e99c6803ca010a2daf460f6c7de`. Judges M1–M4: `mecanico_m1.py` `afc0b46c20586a911ef5da6cce128714def44c2604893c79e0fb1a94f1d5091a`; M2 `15d5b74264cd416d29cbff9e547f43a70575907747ed66df85471d1695336edc`; M3 `d2ce68c6220a36d65df4cf04cf85d33edb1320eec6eaefa13830a38f226d2fda`; M4 `fab34e1420c3d5b45c106a7191bd3286ccb1b9d643b4f5349e09071b0dc8348a`. Models Qwen2.5-Coder 1.5B/3B, llama.cpp b10068; model blob SHA, host hardware, and date of each variant: **NO_DATA** (the receipts fix date 2026-10-15, not hardware/model digest). Output tokens: NO_DATA, the CLI exposed no verifiable count.

| Piece | Measured contract | Latest result |
|---|---|---|
| M1 | isolated edit; normal case and sabotage | FAIL: both tests fail in prompt-v4 (1/1); earlier variants invalid/timeout; see [M1](M1/README.md) |
| M2 | exact replacements, structure, and syntax | FAIL: delivers invalid JSON in the registered variants; see [M2](M2/README.md) |
| M3 | exact line-quote retrieval | PASSES 2/2 with retrieval-v3; baseline/format and list-v2 failed; see [M3](M3/README.md) |
| M4 | add a single line within the 16,384-byte UTF-8 limit | PASSES: 16,370→16,378 (+8 bytes) with v3; see [M4](M4/README.md) |

Scope: response contract and local task judge. It does not measure agent adoption or the quality of an applied patch; the runner declares it does not apply the answers to the checkout. Do not mix task latency with harness tests: `MECANICO.md:27-40` also collects unit suites, not inference. The 19 source receipts are attached byte for byte in `evidence/`; `SHA256SUMS` seals the recovered copies.
