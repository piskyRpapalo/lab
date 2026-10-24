# Local voice pipeline MVP contract

## Existing app pieces (read-only source alignment)

Source was read from PreceptorOS `main` at `7885afe88ad8a456d6af91aa08a62998818b5c9c` through the GitHub read API; no clone, fetch, runtime or audio device was used.

- `voz.py`, blob `a84ffc2485f564a8217f17a723b799670215fd70`: local Piper synthesis, silence guard, and `hablar()` returning generated WAV or `None`. Synthesis availability is not proof that a speaker emitted sound.
- `voz_creacion.py`, blob `57461dcf6ae2ec9d3f792ff6c25d569357f7557c`: reuses `voz.hablar`, pins profile/model/config/processor identity and WAV hashes, limits output size, and returns explicit causes on unavailable generation.
- `audio_feedback.py`, blob `303acc6896e7b432d2c49fd90aa0b47b2b46491d`: deterministic projection of supported event/state pairs into text and a fixed FM motif descriptor; sound is inactive by default with a cause.
- `tono.py`, blob `55d813a240ac78e03cc2da9fde470a96064111da`: cadence renderer includes sleeps. The new queue does not call it to choose order; time never decides priority.
- `silencio.py`, blob `9d82f21ca48f6f07aec2a4e53f648011d953381f`: global hardware-off setting gates microphone and synthesis doors. This prototype does not open either door.
- `creation_voice.js`, blob `6639e55cbbaa5d642e0f7310b8134cdad367f1e6`: local UI flow consumes catalog, declaration and WAV and exposes playback. Physical playback is not established by code presence.
- `bin/preceptoros-pwa` on the same app head includes the local `/api/creaciones/voz` route (merged voice-route card). It uses same-origin checks, the local generator and size/profile validation. This judge does not call it.

## Input and naming invariant

Input schema `preceptoros.app.voice-window/1` carries `visible_count`, `inventory_complete`, a nonempty `inventory_source`, and a list of every simultaneously visible item, each with unique `id`, one of `state`, `seal`, `narration`, `label`, and exact nonempty display text. The count must equal the list length. The plan preserves all item text in `visual_fallback` in the original visible order. `inventory_sha256` fingerprints this declared inventory. The adapter must attest that its registry contains every visible item; without that attestation/source, completeness is `NO_DATA` and nothing is queued. The prototype cannot independently inspect a screen.

The adapter supplies the user setting as `sound_enabled` and derives `hardware_sound_available` from the existing `silencio.apagado()` hardware-off guard. Both must be exactly true to create a queue. False or unknown values produce `NO_DATA` with the corresponding cause; neither setting can be inferred as enabled.

## Deterministic queue

Priority is fixed: state, seal, narration, label. Within a priority class, original visual order wins. No timestamps, timers, random values or wall-clock policy are read. Queue advancement is one explicit step: only the next expected ID can advance. A dropped/failed item cannot be marked delivered and does not silently disappear.

## Receipts and sound-off behavior

Each accepted step records window ID, sequence, utterance ID, exact text, text hash, sink acknowledgment and receipt hash over canonical JSON. The receipt chain validator checks order and every field against the plan. Hashes establish content integrity within the supplied record; they are not signatures or proof of who heard it. The prototype always marks `acoustic_output=NOT_MEASURED` and `spoken_claim=false`. The downstream speaker must provide an acknowledgment before the pipeline records a delivery event; the test sink is logical only.

When sound is disabled, hardware is unavailable, or the visible inventory is unverified, the queue is empty, status is `NO_DATA` with a specific cause, and step advancement is rejected. Unknown sound/hardware values remain unknown instead of claiming the user disabled sound. The full text remains in the visible fallback. Reduced motion changes only `motion_mode` to `static`; if that preference is unknown, the mode is `NO_DATA`. Neither condition removes or shortens text, so the visible window remains the complete message when motion or sound is unavailable.

## Judge

Run `python3 -m unittest tests.test_voice_pipeline`. On 2026-10-24, Python 3.14.4 in the LAB checkout produced 15/15 focused tests GREEN. Before the fix, the previous prototype produced RED with 3/15 failures: sound hardware disabled was still queued, an absent inventory source still queued content, and an unattested inventory still queued content. The corrected planner returns cause-bearing `NO_DATA` for all three. Sabotages assert red for a missing/dropped utterance, wrong priority order, altered/fake receipt, and a sound-off spoken claim. Additional checks cover inventory count and reduced-motion text preservation. No local synthesis, playback, microphone, network, clock, or audio hardware is used. Acoustic output remains `NO_DATA` until measured by a real downstream playback and human listening receipt.


## Current source anchors re-measured read-only

APP `origin/main` is `7885afe88ad8a456d6af91aa08a62998818b5c9c`. Blob ids: `voz.py` `a84ffc2485f564a8217f17a723b799670215fd70`; `voz_creacion.py` `57461dcf6ae2ec9d3f792ff6c25d569357f7557c`; `audio_feedback.py` `303acc6896e7b432d2c49fd90aa0b47b2b46491d`; `tono.py` `55d813a240ac78e03cc2da9fde470a96064111da`; `silencio.py` `9d82f21ca48f6f07aec2a4e53f648011d953381f`; `interface/creation_voice.js` `6639e55cbbaa5d642e0f7310b8134cdad367f1e6`; PWA dispatcher `bin/preceptoros-pwa` `a00ce07567f9789a357de07682f398d5e8b8c952`. The pipeline remains a LAB judge/prototype; it is not wired into the app UI.
