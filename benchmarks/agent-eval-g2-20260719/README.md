# G2 operational evaluation — 2026-07-19

Sources: `~/p0x/soberano-bench/eval_g2/prompts.json` SHA-256 `2ae5a713df2786d9a054d9e3df879a19eba1021e9446e7d0e9727863b091f09d`; `run_eval.sh` SHA-256 `e4cdcbb4e0e8aa1257326d6579c3a453a32718dd5ebaea61bfd3140ea3b33070`; ten logs and `.meta` files under `eval_g2/resultados/`. Date in metadata: 2026-07-19 (`resultados/t01_servicios.meta:1`). The ten processes reported rc=0; total wall time 475.3 s (sum of `resultados/t01_servicios.meta:1` … `t10_sindato.meta:1`, where each file records `wall_s`).

Same ten operational areas as G1R, run later. This yardstick only measures process and duration, not the truth of the text or correctness of tool use. The results include calculations incompatible with the source in several tasks and answers asking for more data; without a common blind judge, an accuracy rate would be invented. Hardware/build/model hash: NO_DATA. Do not combine with G1R as a single batch or with speed benchmarks.
