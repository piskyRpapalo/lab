# Juez M4 y calibración retirada — 2026-09-27

Fuente resumen `~/p0x/esquemas/artemis-local-1.json:165-167`, SHA-256 `ca32e089ba0355443ab277150f93a08edb216ba7a030a73700ab28160460c167`; informe `~/p0x/preceptor-lora/salida/guardian-edge-caza-nido-2026-09-27/informe.json:1-34`, SHA-256 `b53540f81431a7cb5e22014b8838207a06943a519dcb73610ecefd95952387b6`.

Medida: 12 casos; 5/12 pasan, veredicto ROJO. Por categoría: robustez 3/5, doctrina 1/4, honestidad operativa 1/3. Brier 0,3187 y ECE 0,3153 sobre proxy sigmoide del margen por token. Comparación pareada McNemar: b=0, c=0, p exacto=1,0; ambas variantes coinciden en los 12 casos (5 correctos en ambas, 7 incorrectos en ambas), por tanto el instrumento no discrimina mejora. La tanda 5, decisión 7, retiró esas métricas hasta rediseñar el conjunto; `artemis-local-1.json:167` registra la causa.

Hardware/modelo y hashes de base/adaptador en el informe: NO_DATA en esta copia; no elevar resultados de calibración a evidencia de calidad. La prueba de calibración local `preceptor-lora/pruebas/test_calibracion.py:1-43`, SHA-256 `80d083464e20bc5e81aa38c7d14ff3d40bc97609b71d499602596f633053e19f`, es fixture sintético aritmético n=4, no una segunda medición del juez ni referencia M4.
