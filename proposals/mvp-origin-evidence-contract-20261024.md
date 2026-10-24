# MVP origin evidence contract · 2026-10-24

The origin gate runner reads the pushed WEB and APP refs with `git archive` into a temporary read-only measurement area. It does not change either branch or connect to preview services. Static source checks are reported separately from browser, export, and task-output evidence; a clean source tree is not a substitute for those measurements.

## Files and source pins

- WEB: `docs/rebuild/mvp-origin-evidence.json`; `source_tree_oid` must equal `git rev-parse <origin-ref>:docs/rebuild/examples`.
- APP: `interface/mvp-origin-evidence.json`; `source_tree_oid` must equal `git rev-parse <origin-ref>:interface/face`.
- Both documents use top-level `schema: "preceptoros.mvp-regression-evidence/1"`. The pin binds measurements to the exact pushed source subtree. Rebase or edit invalidates the pin.
- The WEB file carries `narration`, `zoom`, `contrast`, and `export`. The APP file carries `task_parity`. A missing or malformed document is `NO_DATA` with its path and cause; it is not replaced by synthetic baseline values.

## Required data

`narration.cases` is a list with exactly 48 unique rows: 3 themes (`basic`, `atlantis`, `zombie`) × 2 orientations (`portrait`, `landscape`) × 8 heights (256, 320, 375, 430, 512, 600, 720, 800 px). Each row has `theme`, `orientation`, integer `height_px`, integer `page_scroll_px` (must be 0), boolean `narration_visible` (must be true), and boolean `message_complete` (must be true). Capture measured browser viewport results, not CSS declarations alone.

`zoom` has numeric `minimum: 0.6`, `maximum: 3.0`, unique `interactive_objects`, and one case per theme × object × zoom value (0.6, 1.0, 3.0). Each case gives `theme`, `object_id`, `map_zoom`, and positive two-number `screen_size_px`; each object/theme pair must retain the same screen size at all three zooms.

`contrast.pairs` has exactly the fixture IDs `primary` and `secondary` for each theme, each with numeric `ratio`. Compare within 0.01 against the pinned regression values in `bin/mvp_regression.py`. Include `status_note` clarifying that these regression measurements are not standards certification.

`export` has unique `states`, `state_inventory_sha256`, `stage: "post-export"`, and one `frames` row for every theme × state. Each row carries `theme`, `state`, `export_stage: "post-export"`, base64 `payload_base64` of the exact exported UTF-8 frame bytes, and lowercase SHA-256 of those decoded bytes. The validator decodes, hashes, parses, and applies the 1,024-byte ceiling to the exported bytes. The inventory hash is SHA-256 over compact UTF-8 JSON for the state list (`ensure_ascii=false`, sorted keys, no separator spaces).

`task_parity` has exact `fields: ["state", "messages", "errors", "controls", "contract"]`, one lowercase 64-hex `shared_fixture_sha256`, and a non-empty `tasks` list. Each unique task row carries `task_id`, the same fixture SHA, and `web` and `app` objects with all five fields. Values must match field by field. Fixtures are shared inputs; web and app assets need not be shared.

## Measurement receipt

The gate receipt records both origin ref names and resolved commit IDs, both source tree IDs, manifest digests, per-gate verdicts/counts, and caused `NO_DATA`. No report may label static source parity as task-level parity, pre-export model frames as post-export bytes, or source zoom constants as screen-size invariance.
