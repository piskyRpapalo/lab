# Benchmark status · 2026-11-10 · GitHub verification 2026-11-11

**Agent:** Codex · GPT-6. **Mode:** DOCUMENTATION / PROPOSE-ONLY. **Commission:** Sovereign asked to publish yesterday's benchmark states; [canonical acta and checked references](https://github.com/piskyRpapalo/buzon/issues/61#issuecomment-6790565281). This file is an evidence ledger, not a new mission, benchmark run, live energy source or operational deployment.

## Yardstick and state

Method: read each PR's exact head SHA, created/merged timestamps and GitHub Actions `pruebas` workflow conclusion. All labels below were checked 2026-11-11 UTC. Local Beelink ×2 gate claims are from the cited PRs/previous acta; **not rerun during this documentation update**.

| PR | Head SHA prefix | Created UTC | Integrated UTC | GitHub `pruebas` on exact head |
| --- | --- | --- | --- | --- |
| [#144 F-08](https://github.com/piskyRpapalo/lab/pull/144) | 45cdf295 | Nov 10 01:31 | Nov 10 10:11 | [SUCCESS](https://github.com/piskyRpapalo/lab/actions/runs/42794184315) |
| [#145 F-09](https://github.com/piskyRpapalo/lab/pull/145) | 00b07131 | Nov 10 01:33 | Nov 10 10:11 | [SUCCESS](https://github.com/piskyRpapalo/lab/actions/runs/42794193432) |
| [#146 F-01](https://github.com/piskyRpapalo/lab/pull/146) | 0d84fc74 | Nov 10 01:35 | Nov 10 10:11 | [SUCCESS](https://github.com/piskyRpapalo/lab/actions/runs/42794201383) |
| [#147 INDEX](https://github.com/piskyRpapalo/lab/pull/147) | 1c251190 | Nov 10 01:38 | Nov 10 06:46 | [SUCCESS](https://github.com/piskyRpapalo/lab/actions/runs/42737193154) |
| [#148 F6 economic](https://github.com/piskyRpapalo/lab/pull/148) | 5c3e6e95 | Nov 10 01:40 | Nov 10 10:12 | [SUCCESS](https://github.com/piskyRpapalo/lab/actions/runs/42794212833) |
| [#149 F-11](https://github.com/piskyRpapalo/lab/pull/149) | b73fe298 | Nov 10 01:42 | Nov 10 10:12 | [SUCCESS](https://github.com/piskyRpapalo/lab/actions/runs/42794219316) |
| [#150 DFA-06](https://github.com/piskyRpapalo/lab/pull/150) | 8b57eb12 | Nov 10 23:49 | Nov 11 07:41 | [SUCCESS](https://github.com/piskyRpapalo/lab/actions/runs/42926529618) |
| [#151 F6-01](https://github.com/piskyRpapalo/lab/pull/151) | a4801b9e | Nov 10 23:49 | Nov 11 07:43 | [SUCCESS](https://github.com/piskyRpapalo/lab/actions/runs/42926536652) |
| [#152 DFA-B3](https://github.com/piskyRpapalo/lab/pull/152) | d989142b | Nov 10 23:49 | Nov 11 07:43 | [SUCCESS](https://github.com/piskyRpapalo/lab/actions/runs/42926542397) |
| [#153 DFA-B4](https://github.com/piskyRpapalo/lab/pull/153) | 6444df89 | Nov 10 23:52 | Nov 11 07:41 | [SUCCESS](https://github.com/piskyRpapalo/lab/actions/runs/42926913087) |
| [#154 DFA-B7](https://github.com/piskyRpapalo/lab/pull/154) | 0f4de471 | Nov 10 23:55 | Nov 11 07:43 | [SUCCESS](https://github.com/piskyRpapalo/lab/actions/runs/42927308286) |

The initial #144–#146, #148–#149 failures belonged to the pre-#147 INDEX budget condition; their subsequently checked **exact-head** workflows are SUCCESS. #147's fix reduced the index from 12,521 to 11,522 bytes against a 12,109-byte limit. This is not a model benchmark.

## Continuation · work created November 11

PRs [#155](https://github.com/piskyRpapalo/lab/pull/155) through [#160](https://github.com/piskyRpapalo/lab/pull/160) were created Nov 11 00:01–00:30 UTC, all merged Nov 11 07:43–07:45 UTC, with exact-head `pruebas` SUCCESS. Highlights based on their archived device receipts:
- [#158 Gemma2 DFA-B5](https://github.com/piskyRpapalo/lab/pull/158): **EXPERIMENT RED**, 4/8 correct ×2; one malformed prediction per pass. CI success only checks the code and provenance guard; no calibrated independent judge.
- [#159 Gemma2 CPU/GPU](https://github.com/piskyRpapalo/lab/pull/159): GPU 40.11 / 40.26 generated tok/s; CPU 27.47 / 27.68 generated tok/s. Four cold runs, two per lane; model/device specificity.
- [#160 Qwen3 two endpoints](https://github.com/piskyRpapalo/lab/pull/160): same model digest, rack 56.08 / 55.25 tok/s; tunnel 124.99 / 129.77 tok/s. No cryptographic remote-host attestation.
- [#161 SWARM-01](https://github.com/piskyRpapalo/lab/pull/161) and [#162 synthetic 24-case matrix](https://github.com/piskyRpapalo/lab/pull/162) are **OPEN DRAFT**, both exact-head `pruebas` SUCCESS; no merge. #162: 30B station 23/24 ×2; Nemo 12B rack 22/24 ×2; Qwen3 1.7B default JSON 24/24 MALFORMED per pass, as a negative control. These are 24 author-labeled synthetic cases, not a human gold standard.

## Cross-repository evidence

- [APP #235](https://github.com/piskyRpapalo/preceptoros-app/pull/235): merged Nov 10; exact-head workflow `pruebas` SUCCESS.
- [WEB #799](https://github.com/piskyRpapalo/preceptoros-web/pull/799): merged Nov 10; exact-head workflows `phase`, `gate`, `hitl` SUCCESS after a cancelled earlier `hitl` attempt. Deployment is not asserted.

## Scope, limits and next piece

**Problem:** historical [STATE.md](../../STATE.md) is a dated 2026-10-22 snapshot, not a live statement of November results. **Adaptation:** append a pointer to this dated, reproducible receipt instead of replacing historical measurements. **Benefit:** one canonical status table, zero stale claims misread as current, and visible negative experimental outcomes. **Limits:** human-gold classification, ≥60 cases/class calibration, end-to-end autonomous orchestration, screen-reader physical parity, watts/J per token, solar battery autonomy and live web/app deployment are **NO_DATA**: no verified measurement in this audit. **Next piece:** independent benchmark review and device-energy sensor before any solar-cadence claim.

This report **does not** authorize a merge or a new experiment. Sovereign FIRMO per exact head and repository rules apply.
