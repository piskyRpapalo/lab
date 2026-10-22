# Candidates with structured output — 2026-09-27
Benchcard: machine=NO_DATA (exact hardware absent) | date=2026-09-27 | runner=NO_DATA (runner absent or not singular) | quant=NO_DATA (quant absent from card) | sha256=ca32e089ba0355443ab277150f93a08edb216ba7a030a73700ab28160460c167

Primary source `~/p0x/esquemas/artemis-local-1.json:6-27`, SHA-256 `ca32e089ba0355443ab277150f93a08edb216ba7a030a73700ab28160460c167`. Harness `~/p0x/hexelion/laboratorio/medir_modelo.py`, SHA-256 `98c43fe09e6603a35bc793c4256c8f8232542007fb447ba1f352e04d88a40b1f`; log `~/p0x/mente/logs/delegacion_medir_vision_2026-09-27.log:1-49`, SHA-256 `b4cf42415fa7986f3004711b2a46de672d89461b830b08e4bf37a8073c70109b`. Exact hardware **NO_DATA**; base load reported 1.42/16 threads.

| Candidate | tok/s | time | output | condition |
|---|---:|---:|---:|---|
| Qwen3-VL 4B instruct Q4_K_M | 26.56 | 7.7 s | 78 tokens | JSON judge: empty, leakage, and schema |
| MiniCPM5 2B Q4_K_M | 45.09 | 4.2 s | 83 tokens | second model measured with the first one resident and GPU at 100% per the API |

The source explicitly declares that this experiment **does not measure vision**: there is no evaluation with real captures. Artemis installation status: not installed, per `artemis-local-1.json:6-9`; visual accuracy and screen-reading behavior **NO_DATA**.
