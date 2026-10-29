# LoRA header shape audit · 2026-10-28
Broadcast receipt: figure=8 adapters · 128/128 matching tensor pairs each | model=Mistral 7B Instruct v0.3 (declared by local configurations) | machine=Linux x86_64 · 16 logical CPUs | date=2026-10-28 | sha256=594f84ffa1848b7a2447530264e237ea80821141949324e564e785ff972ada45
Benchcard: machine=Linux x86_64 · 16 logical CPUs | date=2026-10-28 | runner=Python stdlib safetensors header audit | quant=NO_DATA (tensor values and formats not assessed) | sha256=bf7c5b992f0b4c6b52e545a78918057a89594d4b36b9f63660ec019f5faec54d

At 2026-10-28 23:55:49 UTC, three locally supplied base shard headers described 291 tensors. In the scoped adapter tree, each of eight weight files contained 128 A/B pairs: all 128 per file matched the corresponding base header's two dimensions and shared rank, with zero missing target tensors, malformed pairs, dimensional mismatches or unrecognized adapter tensor names. [Receipt](receipt.json) contains each measured adapter file digest and each base header digest, not paths or names.

Method: `python3 benchmarks/lora-shapes-20261028/shape_audit.py --base-root <local snapshot> --adapters-root <local adapter directory>`. It reads header JSON and hashes adapter files; it does not load tensors. The base is a local snapshot associated by its directory label with the configurations' declared base; no trusted source or signed expected digest was checked. Base weight digests, tensor offsets and values, functional load, inference, promotion, training data and quality are NO_DATA. Matching dimensions alone do not prove compatibility or authority. This is not an inventory of all adapters on the rack.

The initial script filename shadowed a Python standard-library module and failed before measurement; the renamed runner produced the receipt above. Tests use synthetic headers and detect an altered dimension, an incomplete pair and malformed length. The rack had effectively no free swap before this audit; the audit did not load the base weights or start training.

Agent: Codex · Model: GPT-6.1 Terra · Run: MEASURED (header shapes only)

## F32 payload finiteness · 2026-10-29

At 00:07:33 UTC, a second read-only pass examined eight scoped adapter files: 2,048 F32 tensors and 109,051,904 values, with zero NaN and zero infinite values. The multiset of measured file SHA-256 values matches the earlier header receipt. [Finite receipt](finite-receipt.json) SHA-256: `5a0d92d4498b157c2428142f06d831aa7358d917d1aca1c21a6d9c7f97d508f1`; [runner](finite_audit.py) SHA-256: `7d3e6dac7ba86837a903b0733ce792aad0444d1d05269c0f6f60920522e639a8`. Method: supply the local adapter tree to `python3 benchmarks/lora-shapes-20261028/finite_audit.py --adapters-root <local directory>`. It accepts only F32 with contiguous, dimension-consistent byte ranges and reports NO_DATA for unreadable or unsupported files. It scans in chunks; it does not load a base model. Synthetic tests detect NaN, infinity, invalid offsets and unsupported dtype.

This is a payload sanity check, not validation of tensor meaning, authenticity, base compatibility, model loading, training data or quality. Files were not locked while scanned; concurrent mutation protection is NO_DATA. The count covers only the supplied tree.

Agent: Codex · Model: GPT-6.1 Terra · Run: MEASURED (F32 finiteness only)
