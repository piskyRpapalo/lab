# CPU training trial, Phase 0 — 2026-08-20
Broadcast receipt: figure=90.8 s · 100 steps | model=NO_DATA (base model not identified) | machine=Ryzen 7 255 · 8C/16T | date=2026-08-20 | sha256=2ba5281da8872e630186d9d0d7fcca39608634a451121df9e0f2c369d489b91d
Benchcard: machine=Ryzen 7 255 · 8C/16T | date=2026-08-20 | runner=PyTorch CPU | quant=NO_DATA (quant absent from card) | sha256=2ba5281da8872e630186d9d0d7fcca39608634a451121df9e0f2c369d489b91d

Source `~/p0x/preceptor-lora/FASE0_VEREDICTO.md:1-56`, SHA-256 `2ba5281da8872e630186d9d0d7fcca39608634a451121df9e0f2c369d489b91d`. Declared machine: Ryzen 7 255, 8C/16T, 57 GiB RAM, torch 2.13 CPU. 100 steps: 90.8 s (0.908 s mean; 0.894 s median); 1.0 s load; peak RAM 9.13 GiB; 11,796,480 trainable parameters out of 4,034,264,576 (0.292%) (`FASE0_VEREDICTO.md:27-35`). Loss listed 5.6994→3.4611, but 3 steps produced NaN and the source corrects its initial claim of convergence (`:16-22`).

Fixed-length sequences: 64 tokens 43 tok/s; 256: 60; 512: 55; 1,024: 51; 2,048: 45 (`FASE0_VEREDICTO.md:42-56`). This is per-sequence training throughput, not generation. The 0.908 s/step figure corresponds to short 13-token samples (`:40-45`). Generalization, independent validation, and GGUF export: NO_DATA (`:80-82,95-98`).
