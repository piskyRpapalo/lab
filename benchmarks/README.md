# Benchmarks recuperados

Índice del material medido disponible, sin inferencia nueva. Cada ficha conserva su yardstick; `NO_DATA` identifica un dato que la fuente no acredita. El inventario local de base se contrastó contra `origin/main` 37cd202 el 2026-10-16; esta recuperación parte de `origin/main` 2cb70d8 el 2026-10-17.

- [Bench publicado 2026-10-11](bench_20261011/README.md): rendimiento de embeddings; raw JSON en la misma carpeta.
- [tg32](tg32/README.md): throughput reportado; metadatos de arnés incompletos.
- [Evaluación G1R](agent-eval-g1r-20260719/README.md) y [G2](agent-eval-g2-20260719/README.md): ejecución operativa, sin puntuación de calidad.
- [Duelo de herramientas](agent-tool-duel-20260718/README.md): códigos de salida y timeouts, sin juez de calidad común.
- [G0](g0/README.md): `llama-bench`, smoke de harnesses y smoke del motor local, en métricas separadas.
- [Qwen 35B-A3B, 2026-10-16](qwen36-35b-20261016/README.md): `llama-bench` directo sobre GGUF existente; CPU y Vulkan separados.
- [Reanudación G0 del Preceptor, 2026-10-16](preceptor-g0-20261016/README.md): una prueba local del rol, rojo de motor ausente y dos respuestas medidas.
- [Registro del motor y smoke unitario, 2026-10-16](motor-registration-smoke-20261016/README.md): estado de disponibilidad heredado, separado del G0 y no usado como yardstick.
- [Comparativa de modelos, 2026-09-14](soberano-model-compare-20260914/README.md): cuatro modelos, latencia/juicio por prompts.
- [Smoke de modelos, 2026-09-13](lab-model-smoke-20260913/README.md): cuatro respuestas sintéticas y métricas de llamada.
- [Serie Vulkan, 2026-09-07](throughput-vulkan-20260907/README.md): siete filas heredadas; identidades locales omitidas y medidas intactas.
- [Serie llama-bench, 2026-10-05](throughput-llama-bench-20261005/README.md): runner y eje separados de la serie Ollama.
- [Candidatos de visión](artemis-candidates-20260927/README.md): medición de salida JSON; no mide visión.
- [Fluency mecánica](bench-fluency/README.md): M1–M4 y todos los recibos Qwen2.5-Coder.
- [Legibilidad H9](h9-readability-20261016/README.md): control/mapa/diccionario y estímulos densos/prosa; artefactos originales adjuntos con hashes.
- [Juez M4](preceptor-lora-m4-20260927/README.md): evaluación ROJA y calibración retirada.
- [Entrenamiento Fase 0](preceptor-lora-training-20260820/README.md): throughput CPU y límites de interpretación.

## FIRMO y límites de recuperación

La orden firmada del Soberano del 2026-10-17 declara amparadas estas series recuperadas: Vulkan 2026-09-07, llama-bench 2026-10-05, candidatos 2026-09-27, Qwen 35B 2026-10-16 (ronda 97), G0 2026-10-16, fluencia M1–M4 y los dos informes históricos de entrenamiento/juez. Se conserva el FIRMO como procedencia declarada; un artefacto de firma por corrida no está incluido en el lab (`NO_DATA`), y una huella SHA-256 de fichero no se presenta como firma humana.

Cinco adaptadores locales quedan registrados solo como cohorte futura de evaluación: nombres, pesos, hashes, licencias y resultados por adaptador se omiten por privacidad; su disponibilidad pública es `NO_DATA`. Las fichas existentes de entrenamiento y juez son experimentos históricos distintos, no sustitutos de una evaluación de esa cohorte.

Hardware sin especificación fuente, hashes de harness ausentes y alcances no medidos quedan declarados `NO_DATA` en cada ficha. Los hashes citados son SHA-256 de la fuente indicada, no una atribución de autoría ni verificación independiente del equipo.
