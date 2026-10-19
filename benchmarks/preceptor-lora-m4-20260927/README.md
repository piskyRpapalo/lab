# M4 judge and retired calibration — 2026-09-27

Summary source `~/p0x/esquemas/artemis-local-1.json:165-167`, SHA-256 `ca32e089ba0355443ab277150f93a08edb216ba7a030a73700ab28160460c167`; report `~/p0x/preceptor-lora/salida/guardian-edge-caza-nido-2026-09-27/informe.json:1-34`, SHA-256 `b53540f81431a7cb5e22014b8838207a06943a519dcb73610ecefd95952387b6`.

Measurement: 12 cases; 5/12 pass, RED verdict. By category: robustness 3/5, doctrine 1/4, operational honesty 1/3. Brier 0.3187 and ECE 0.3153 over a sigmoid proxy of the per-token margin. Paired McNemar comparison: b=0, c=0, exact p=1.0; both variants agree on the 12 cases (5 correct in both, 7 incorrect in both), so the instrument does not discriminate improvement. Batch 5, decision 7, retired those metrics until the set is redesigned; `artemis-local-1.json:167` records the cause.

Hardware/model and base/adapter hashes in the report: NO_DATA in this copy; do not elevate calibration results to quality evidence. The local calibration test `preceptor-lora/pruebas/test_calibracion.py:1-43`, SHA-256 `80d083464e20bc5e81aa38c7d14ff3d40bc97609b71d499602596f633053e19f`, is an arithmetic synthetic fixture n=4, not a second measurement of the judge nor an M4 reference.
