# MVP objective map reconciliation · proposal

Status: proposal only. Read-only comparison of WEB `origin/main=8c4eeed840757a02bf5b6cc85b67f40fdbced78a`, APP `origin/main=7885afe88ad8a456d6af91aa08a62998818b5c9c`, and STUDY `origin/main=4fbcf7e3dc142499cc6d1bcfeb30046d148dba4d`. Source of product direction: NORTE 5; current objective registry: STUDY `13-objectives.md` (updated 2026-10-26). No product code, deployment, or live-site request is part of this proposal.

## Drift inventory

WEB `docs/MVP.md` is explicitly a proposal dated 2026-10-19, based on `eac293d` / `9a72d4d`. Its 17-function map (13 WEB + 4 APP), seals, byte/load figures, F1–F3 sign-offs, and app rows are historical. It predates the E8 V2 seal, Lane F, Week E, NORTE 5 and the new face. Keep it as historical evidence; do not use its old GREEN/LIVE counts as current acceptance.

| Old row / assertion | New evidence | Reconciled status |
|---|---|---|
| W1 initial-load weight `71,277 B gzip` | Figure was measured for the dated 2026-10-19 tree. Current head and new face need a fresh build measurement. | `NO_DATA`: current artifact weight not measured on WEB 8c4eeed. |
| W2 `state_vector.js`, packet `466 B` | The schema and judge are historical WEB features; creation frame and MCP contracts have separate 1,024 B limits. | Retain as a distinct contract; current packet bytes need the current command/head receipt. |
| W3 seal palette / W4 Descent | Old game routes remain in the WEB tree while NORTE 5 declares a single rebuilt product face. | Legacy routes are not new-face acceptance; record their retirement or an explicit compatibility route before landing. |
| W5 four-channel accessibility `NO_DATA` | New example log reports narration visible without page scroll in 24/24 cases, zoom 0.60–3.00 and high contrast pairs. Physical screen-reader and complete task parity are not established by those samples. | `PARTIAL_MEASURED`; no WCAG/EN 301 549 certification claim. Keep physical assistive-technology acceptance open. |
| W6 nine portal languages | The old site has nine portals. The new face's language coverage and translated voice catalog are not measured. | Old portals remain measured separately; new-face localization `NO_DATA`. |
| W7 end-rift “Questions???” | NORTE 5 changes the face to a chat panel + joystick. The local chat response route is not wired in Claude's latest report. | Old trigger is superseded; new chat completion `NO_DATA` until local response integration. |
| W8 browser model / W9 Hexelion node | Current direction is local-first; no new-face local model route is proven. Aduana's cédula gateway is still provisional and not deployed. | Model `NO_DATA` with cause: new-face adapter not measured. Node `NO_DATA` with cause: gateway deployment and receiver absent. |
| W10 zero requests | Claude's report says 0 external requests for the three local examples. | Measured for those example runs only; repeat on accepted WEB and APP builds, including cold start. |
| W11 16,384 B piece ceiling / old max `16,365 B` | That max belongs to the dated tree; current gates need remeasurement. New Bubble frame report: worst 1,017/1,024 B, only 7 B remaining. | Keep both limits distinct; current per-piece and post-export frame evidence must be attached to release. |
| W12 static AI/MCP material; W13 D1 guard | Existing manifests, app MCP tools and D1 guard are separate surfaces. | Not a user-facing launch claim until the new face uses them and a current receipt names the exact path. |
| A1–A4 app rows from another tree | WEB doc says these were read from APP commit `88aedec`; APP now has its own voice route and creation API. | Replace old cross-repo snapshot with pinned APP evidence; do not call old A1–A4 rows current. |

## Reconciled launch objective (draft)

One product, one recognizable face on WEB and APP: chat panel plus joystick, with the same user-visible task, names, states and error meanings. Claude owns the Bubble shapes and palette. A user can start without external services; any missing local model, voice engine, or node route is shown as `NO_DATA` with cause. The complete task message remains visible when speech or motion is unavailable. Basic, Atlantis and zombie are proposal skins; layout differences follow the current decree, while shared scene geometry and task contracts are compared separately.

**Acceptance requires receipts for each surface and the exact source heads.** “In code” means implemented; it does not mean installed, heard, accessible, deployed, or LIVE.

| Gate | Evidence required before launch | Current status |
|---|---|---|
| Product identity and route | Same chat/joystick identity on accepted WEB and APP builds; no unintended old-generation landing page. | `NO_DATA`: latest Claude outputs are in isolated worktrees; Sovereign visual approval is pending. |
| Local task completion | Same shared task fixtures produce equal state, messages, errors, controls and contract on both surfaces; local answer route; zero external requests. | `NO_DATA`: model/chat route not connected in the latest face report. |
| Bubble output | Deterministic Bubble frames, semantic palette channel, complete reachable-state matrix, exact post-export UTF-8 counts ≤1,024 B. | Partial: 93 states/skin and 1,017 B worst frame are Claude-reported; only 7 B headroom. Verify after accepted integration. |
| Accessible narration | All visible items named; visible complete message; keyboard and touch task parity; no color-only meaning; reduced-motion and sound-off fallbacks. | Partial: 24/24 viewport cases and zoom bounds logged; physical screen-reader, complete task parity, speech and haptic perception remain open. |
| Contrast | Recompute exact foreground/background pairs on the accepted skin assets and compare with fixtures 15.80/9.91, 18.27/9.61 and 15.11/11.93. | Regression values exist; changed palettes must be remeasured. They are not compliance certification. |
| Offline install | Clean install, first launch, refresh, restart and offline-after-install on both surfaces; asset/cache integrity and no network escape. | `NO_DATA`: zero external requests was reported for local examples; clean installation sequence not measured. |
| Voice | Local app voice route with pinned model/profile and explicit engine-missing cause; fallback text complete; independent audible listening receipt if speech is claimed. | Route exists in APP main; new-face integration and physical hearing are not measured. |
| Publication and identity | Signed package verified, same-origin import/publication, independent GET, byte comparison and persistence after restart. | Old-generation E8 is LIVE; it does not certify this rebuilt face. New-generation journey `NO_DATA`. |
| Node cédula | Gateway route deployed, signed cédula delivered, receiver schema and persistence measured, then independent read. | `NO_DATA`: export 502×2, cédula route 404/provisional; no gateway deployment or receiver receipt. |
| Deployment freshness | Human-approved manual Worker deploy from exact WEB main; FARO exact-byte receipt for all expected artifacts. | Workflow is manual; fresh FARO for the accepted new face is pending. Historical 244/244 must not be reused. |

## Launch boundaries and commands

The former W1/W2 numeric values are not current-head evidence. Before launch, build and run the exact gates from the accepting PRs on a clean worktree; run the WEB artifact and accessibility judges against the accepted fixture set; run APP tests from its pinned main; attach results to the same source heads. Deploy only through the protected manual Worker path under the Sovereign's authority. After deployment, run FARO from the exact same main and preserve counts, hashes, missing files and errors. Physical sound, touch, screen-reader perception and Sovereign visual approval require human measurement; no synthetic test can substitute.

## Explicitly outside this MVP unless promised

STUDY `13-objectives.md` keeps context-lock, preceptor-cell, sanctuary/forge tiers, self-regulation, wave ceiling/combat mode, fog push/NPC occupancy, the study registration of quaternary verdict and LoRA, evolutionary harness and Crab Account naming/phases as proposed or `NO_DATA`. STUDY `14-bench-families.md` is post-MVP: seven benchmark families and live per-agent/thermodynamic measurements remain unclosed. Do not block a single-device local MVP on these, and do not claim they are complete.

## Provenance and limits

WEB `docs/MVP.md` itself supplies its old date/base and old counts. Week E status and remaining F3 physical reading are taken from STUDY `13-objectives.md` at `4fbcf7e3`; the local-first direction is NORTE 5 / p0x canon v1.2. APP voice source is pinned separately at `7885afe8`. Claude's viewport, zoom, contrast, Bubble-size and external-request figures are reports in its append-only session log, not independently repeated measurements in this LAB package. The current live-site state is not queried here.
