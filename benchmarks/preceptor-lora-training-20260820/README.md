# Ensayo de entrenamiento CPU, Fase 0 — 2026-08-20

Fuente `~/p0x/preceptor-lora/FASE0_VEREDICTO.md:1-56`, SHA-256 `2ba5281da8872e630186d9d0d7fcca39608634a451121df9e0f2c369d489b91d`. Máquina declarada: Ryzen 7 255, 8C/16T, 57 GiB RAM, torch 2.13 CPU. 100 pasos: 90,8 s (0,908 s media; 0,894 s mediana); carga 1,0 s; RAM pico 9,13 GiB; 11.796.480 parámetros entrenables de 4.034.264.576 (0,292%) (`FASE0_VEREDICTO.md:27-35`). Pérdida listada 5,6994→3,4611, pero 3 pasos produjeron NaN y la fuente corrige su afirmación inicial de convergencia (`:16-22`).

Secuencias de longitud fija: 64 tokens 43 tok/s; 256: 60; 512: 55; 1.024: 51; 2.048: 45 (`FASE0_VEREDICTO.md:42-56`). Esto es throughput del entrenamiento por secuencias, no generación. La cifra 0,908 s/paso corresponde a muestras cortas de 13 tokens (`:40-45`). Generalización, validación independiente y exportación a GGUF: NO_DATA (`:80-82,95-98`).
