# First LAB cards for WEB maintenance

Status: proposal only. This document does not activate LAB as WEB maintainer,
change WEB, contact a deployed site, or create a release receipt.

## Measured anchors

- LAB source: `origin/main` at `068052eb53df6cf09c2a660724ba27cd89f43b47`.
- STUDY source: `origin/main` at `ee9b398106cd104ccf09a8c85b972a0360c47d8c`.
- `study/proposals/ROSETTA_HARVEST2_20261023.md` records “the LAB becomes
  maintainer of the WEB” as PROPUESTA and says the role activates only after a
  frontend-v1 receipt. These cards prepare that work; they do not claim that
  prerequisite is met.
- STUDY `14-bench-families.md` separates creative and utilitarian measurements
  and requires declared axes, owners, commands, and honest NO_DATA states.
- WEB was not read or changed for this proposal. Its current source ref and
  Claude's in-flight examples are not pinned here; each card must pin its exact
  input revision when commissioned.

## Card WM-1 · Offline WEB artifact contract

**Question.** Can a checked-out WEB release be served offline without missing
declared resources, hidden external dependencies, or broken size contracts?

- **Input:** an operator-supplied, immutable WEB checkout or export and its
  revision identifier. No network fetch by the validator.
- **Measure:** compare declared service-worker shell/content paths with files;
  inspect local HTML/CSS/JS references for undeclared remote origins; validate
  route-counter documentation and the package/frame limits supplied by the
  pinned WEB contracts. Do not hard-code current counts before re-anchoring.
- **Output:** a counts-and-hashes receipt containing input revision, path
  inventory hash, checked counts, missing/extra counts, external-reference
  count, and each contract verdict. Never copy page contents or user data.
- **Judge:** fixture set with one valid tree and sabotages for a missing
  precache file, an undeclared external URL, route-count drift, an oversized
  Bubble frame, and an oversized creation package. Every sabotage must fail
  for its named cause; valid fixture passes.
- **NO_DATA:** missing source revision, unavailable contract, dynamic reference
  that cannot be resolved statically, or deployment state not supplied.
- **Cost:** one stdlib-only validator, fixture tree, and tests; exact time and
  runtime are NO_DATA until measured.
- **Dependency:** frontend-v1 contract and a pinned WEB source snapshot.

## Card WM-2 · WEB release freshness receipt

**Question.** Does a human-authorized deployment match the WEB revision that
was approved, and can the evidence be read later without credentials?

- **Input:** the approved WEB commit, deployment version, and a scrubbed FARO
  receipt supplied by the operator after the existing manual deployment.
- **Measure:** compare the declared source/deployment identifiers and the
  FARO totals for compared, identical, changed, missing, and network-error
  resources. Keep “queued” or deployment success separate from content parity.
- **Output:** a local, append-only, privacy-safe LAB record with hashes and
  counts only. It must label the human who performed deployment, the supplied
  source revision, observation time, and whether parity is measured.
- **Judge:** fixture pairs for exact parity, changed resource, missing
  resource, source-revision mismatch, and incomplete FARO output. The last
  four cases cannot be GREEN; missing evidence returns NO_DATA with cause.
- **NO_DATA:** no operator-supplied deployment receipt, no source revision, or
  incomplete resource totals. This card does not poll the public site.
- **Cost:** one receipt schema, validator, fixtures, and tests; runtime and
  storage cost remain NO_DATA until implemented and measured.
- **Dependency:** WM-1's stable artifact identity and an accepted frontend-v1
  receipt. Deployment remains a human action.

## Card WM-3 · Three-theme Bubble parity judge

**Question.** Do basic, atlantis, and zombie examples preserve one product
face and one mathematical fixture while changing only permitted palette bands?

- **Input:** the three examples after Claude's branch is landed and the Mesa
  pins the exact revisions. This proposal does not inspect or alter his
  in-flight files.
- **Measure:** compile the same fixture with the pinned Bubble language;
  compare geometry fields and normalized object topology; require declared
  palette values to differ; compare chat-panel and joystick structure; scan
  local resource references for external requests. The judge reports data,
  not aesthetic approval.
- **Output:** per-theme frame SHA-256, geometry/topology equality result,
  palette difference result, interface-structure result, and external-request
  count.
- **Judge:** equal geometry and interface structure with distinct allowed
  palette bands passes. Geometry edits, extra objects, missing controls, or an
  external reference each fail with a cause.
- **NO_DATA:** examples not merged or not pinned, Bubble compiler unavailable,
  or fixture schema unresolved. The Sovereign's rack review remains a human
  acceptance step and cannot be replaced by this judge.
- **Cost:** one fixture-driven validator and sabotage tests; runtime remains
  NO_DATA until measured on landed examples.
- **Dependency:** Claude's three examples, frontend-v1 receipt, and the exact
  Bubble contract pinned by the Mesa.

## Order and receipt

1. Keep the LAB remote-CI statement aligned with its checked-in workflow
   (separate gate-truth card).
2. Commission WM-1 against a pinned frontend-v1 snapshot.
3. Commission WM-2 after the operator and Mesa approve its receipt shape.
4. Commission WM-3 only after Claude's examples land and are pinned.

- **What:** three independently commissionable proposals for offline artifact
  integrity, release freshness, and theme parity.
- **Cost:** proposal document only; implementation effort is not measured.
- **Yardstick:** each card declares inputs, outputs, sabotages, NO_DATA causes,
  privacy bounds, and dependencies; no live source or in-flight Claude file is
  modified or claimed as measured.
- **Status:** PROPUESTA; LAB's WEB-maintainer role remains conditional on the
  frontend-v1 receipt and Sovereign approval.
