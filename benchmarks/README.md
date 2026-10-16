# Benchmarks recuperados

Índice del material medido disponible, sin inferencia nueva. Cada ficha conserva su yardstick; `NO_DATA` identifica un dato que la fuente no acredita. El inventario local de base se contrastó contra `origin/main` 37cd202 el 2026-10-16.

- [Bench publicado 2026-10-11](bench_20261011/README.md): rendimiento de embeddings; raw JSON en la misma carpeta.
- [tg32](tg32/README.md): throughput reportado; metadatos de arnés incompletos.
- [Evaluación G1R](agent-eval-g1r-20260719/README.md) y [G2](agent-eval-g2-20260719/README.md): ejecución operativa, sin puntuación de calidad.
- [Duelo de herramientas](agent-tool-duel-20260718/README.md): códigos de salida y timeouts, sin juez de calidad común.
- [G0](g0/README.md): `llama-bench`, smoke de harnesses y smoke del motor local, en métricas separadas.
- [Comparativa de modelos, 2026-09-14](soberano-model-compare-20260914/README.md): cuatro modelos, latencia/juicio por prompts.
- [Smoke de modelos, 2026-09-13](lab-model-smoke-20260913/README.md): cuatro respuestas sintéticas y métricas de llamada.
- [Candidatos de visión](artemis-candidates-20260927/README.md): medición de salida JSON; no mide visión.
- [Fluency mecánica](bench-fluency/README.md): M1–M4 y todos los recibos Qwen2.5-Coder.
- [Legibilidad H9](h9-readability-20261016/README.md): control/mapa/diccionario y estímulos densos/prosa; artefactos originales adjuntos con hashes.
- [Juez M4](preceptor-lora-m4-20260927/README.md): evaluación ROJA y calibración retirada.
- [Entrenamiento Fase 0](preceptor-lora-training-20260820/README.md): throughput CPU y límites de interpretación.

Hardware sin especificación fuente, hashes de harness ausentes y alcances no medidos quedan declarados `NO_DATA` en cada ficha. Los hashes citados son SHA-256 de la fuente indicada, no una atribución de autoría ni verificación independiente del equipo.
