# G0 · lectura local de autoridad del Preceptor · 2026-10-16

Prueba de rol del Preceptor con `qwen3-coder:30b`, ejecutada por el endpoint local de Ollama. Digest del modelo `5e8c8157b1b50f092e9c488360bcb63ffa53726cf732d71fc9c9401c43bc78d7`; tamaño 18,556,689,759 bytes; contexto solicitado y observado 16,384. Máquina AMD Ryzen 7 255, 16 CPU lógicas, Radeon 780M. Durante la llamada `ollama ps` informó `100% GPU`, contexto 16,384, runner `llamacpp`.

La tarea fija mide una orden de navegación por voz, la elección y firma humanas, y el rol del modelo como proponente. El lab conserva el hash del prompt y de las respuestas, el esquema, las opciones y los timings; los textos crudos no se archivan. Temperatura 0, semilla 20261016, `num_ctx=16384`, dos llamadas secuenciales en proceso servidor persistente.

## Rojo antes de verde

Rojo: llamada a `127.0.0.1:9/api/generate` sin motor disponible, `curl` exit 7, conexión rechazada. Esto verifica que el harness no inventa una respuesta ante motor ausente.

Verde: dos llamadas al modelo local devolvieron el mismo JSON, 75 tokens de prompt evaluados y 33 tokens de salida en cada una. La primera tomó 14.698 s total, incluidos 13.209 s de carga; la segunda tomó 1.037 s, con carga de 0.002 s. Hash de respuesta idéntico en ambas. Este caso mide una decisión estrecha de frontera de autoridad, no capacidad general de codificación, reconocimiento de voz ni calidad del modelo.

## Límite

El identificador de modelo está medido por digest. No se midieron temperaturas físicas, energía, ni calidad sobre una batería de tareas: NO_DATA con esas causas. Los resultados previos de G0 de julio siguen separados en [g0](../g0/README.md); no se combinan con esta reanudación.
