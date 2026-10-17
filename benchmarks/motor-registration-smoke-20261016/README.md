# Comprobación de registro del motor · 2026-10-16

Esta ficha separa el alta y el smoke de una sola llamada del benchmark G0; no se usa como yardstick ni como estimación de rendimiento sostenido.

- Estado heredado del encargo firmado del Soberano: registro local creado; digest completo y tamaño constan en [G0](../preceptor-g0-20261016/README.md#rojo-antes-de-verde). Contexto 16.384 y temperatura 0,2 constan en `deploy/soberano/Modelfile:13,16` del sistema local.
- Fecha: 2026-10-16. Eje: una carga fría + una respuesta; 16,97 s declarados. Causa de permisos registrada por el Soberano: `chown` del usuario de servicio.
- Máquina exacta, versión del runner y recibo crudo de esa llamada: `NO_DATA` en el artefacto fuente consultado. `deploy/soberano/MOTOR_LOCAL.md:41-44` registra otra prueba fría de 19,45 s con salida de 24,9 tok/s en CPU; es una lectura distinta y no reemplaza los 16,97 s declarados aquí.
- FIRMO: la orden firmada de recuperación de 2026-10-17 declara el registro resuelto. No se revalidó ni se reejecutó Ollama en esta recuperación.

El resultado de G0, con dos respuestas medidas y su rojo de motor ausente, permanece en su ficha propia; este smoke unitario no aporta evidencia de calidad o estabilidad.
