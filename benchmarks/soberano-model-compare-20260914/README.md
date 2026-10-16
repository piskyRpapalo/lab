# Comparativa de modelos y juicio — 2026-09-14

Fuentes: `~/p0x/soberano-bench/minicpm5_veredicto.md:1-35` (SHA-256 `1fcf95e4933071bffa8a9ba4d7975fbdce8071f7eba63e474838cc23084a3089`) y `minicpm5_resultados.json` (SHA-256 `955721a3e11e599be024b92168788222a6e87033b1262ba20bad45b1d9bd305f`); arnés `minicpm5_bench.py` SHA-256 `8a261efb0d2bdc6b92d141aa28e4e521cf8e3a1bf8f9560e3c4598a2f34e615e`, prompts SHA-256 `eaafecf001f2004cee838c3951be1613e1e3debdbc9dc590bab8ceed099b614a`.

Hardware declarado: Ryzen 7 255, Radeon 780M, 16 hilos; 100% GPU, contexto 8192, 40 prompts/modelo (20 orquestación +20 usuario), tres tandas completas; ficha informa última tanda y que las tres quedaron dentro de 3%. El hash de binario/runtime exacto es **NO_DATA**. Resultados medidos (tok/s mediana; TTFT mediana; juicio sobre 38 respuestas clasificables):

| Modelo | tok/s | TTFT ms | juicio | orquestación | usuario | Fuente |
|---|---:|---:|---:|---:|---:|
| Qwen3 4B | 25.28 | 180.3 | 10/38 | 2/20 | 8/20 | `minicpm5_resultados.json:20-56` |
| MiniCPM5 2B Q4_K_M | 57.17 | 86.3 | 23/38 | 14/20 | 9/20 | `minicpm5_resultados.json:310-351` |
| Llama 3.2 3B | 35.32 | 101.8 | 13/38 | 9/20 | 4/20 | `minicpm5_resultados.json:605-651` |
| Qwen2.5-Coder 3B | 48.56 | 106.0 | 23/38 | 15/20 | 8/20 | `minicpm5_resultados.json:905-951` |

Criterios numéricos adicionales para MiniCPM5: 66.74 vueltas/minuto en familia de orquestación; RSS 2.704 GB es agregado de procesos simultáneos y no atribuye memoria de pesos alojados en GPU; el contexto medido fue 8192, por lo que RSS de modelo y contexto 16384 son **NO_DATA**. Juicio: 38 casos puntúan, aunque se lanzaron 40/modelo; causa del denominador: el arnés deja fuera dos casos para acierto. No usar este set como benchmark de visión ni de hechos abiertos: mide velocidad, pacing y criterios humanos sobre prompts fijados.
