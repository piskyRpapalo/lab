# Candidatos con salida estructurada — 2026-09-27

Fuente primaria `~/p0x/esquemas/artemis-local-1.json:6-27`, SHA-256 `ca32e089ba0355443ab277150f93a08edb216ba7a030a73700ab28160460c167`. Arnés `~/p0x/hexelion/laboratorio/medir_modelo.py`, SHA-256 `98c43fe09e6603a35bc793c4256c8f8232542007fb447ba1f352e04d88a40b1f`; log `~/p0x/mente/logs/delegacion_medir_vision_2026-09-27.log:1-49`, SHA-256 `b4cf42415fa7986f3004711b2a46de672d89461b830b08e4bf37a8073c70109b`. Hardware exact **NO_DATA**; carga base reportada 1,42/16 hilos.

| Candidato | tok/s | tiempo | salida | condición | Fuente
|---|---:|---:|---:|
| Qwen3-VL 4B instruct Q4_K_M | 26.56 | 7.7 s | 78 tokens | juez JSON: vacío, fuga y esquema
| MiniCPM5 2B Q4_K_M | 45.09 | 4.2 s | 83 tokens | segundo modelo medido con el primero residente y GPU al 100% según API

La fuente declara explícitamente que este experimento **no mide visión**: no hay evaluación con capturas reales. Estado de instalación de Artemis: no instalado, según `artemis-local-1.json:6-9`; exactitud visual y comportamiento de lectura de pantalla **NO_DATA**.
