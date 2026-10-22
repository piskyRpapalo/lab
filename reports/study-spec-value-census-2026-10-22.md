# Study specification values · 2026-10-22

Base `fcbfb8c`; `study_spec.json` is 461 B. The five proposed values remain `NO_DATA`: no approved source was present for any field, so no hash or fleet assignment was inferred.

| Field | Value and measured cause |
|---|---|
| `TREND_VECTOR` | `NO_DATA`: no approved study input hash |
| `BASE_MODELS` | `NO_DATA`: no approved model receipt hashes |
| `RAG_CORPUS` | `NO_DATA`: no approved corpus hash |
| `LORA_ADAPTER` | `NO_DATA`: no approved adapter hash |
| `HARDWARE_MATRIX` | `NO_DATA`: 0/3 public ring assignments; runner reports each ring `NO_DATA` |

Two runner dry runs returned `NO_DATA` for all three rings. The two directed suites passed 9/9 twice; clearing one cause was RED twice. The template remains <1,024 B.

Source SHA-256: `study_spec.json` `4ef57960a2f3e195f66e8afa963733b65f7f819369b15c25f58c90b0997194bc`; `data/study_spec.schema.json` `ff5f42792ff1682428a83c21047d3d462ca1217e4309c84c584bfc5dd8cdbe65`; `bin/study_spec_runner.py` `3030433718cf4a55b9dd407f33d46cd2cec015bf3494fdac6be46e49882fb946`.

Open question: 1. Which approved source receipts should populate the five fields? Until supplied, these values stay `NO_DATA`.
