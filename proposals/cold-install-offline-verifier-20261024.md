# Cold-install drill and offline receipt

This package defines a measurable drill for installing the unified product on a
clean rack Android. It does not assert that a release artifact, install route,
same-origin hash, or complete surface inventory exists today: those inputs are
`NO_DATA` until the product owner pins them.

## Operator sequence

1. Pin exact WEB and APP commits, release artifact names, byte sizes, and SHA-256
   values from the signed release record. If either artifact is absent, stop this
   drill as `NO_DATA · release artifact not pinned`.
2. On a clean rack Android profile, clear browser data, installed app data, service
   workers, and site caches. Record the clean-state screen and profile label without
   recording personal identifiers.
3. Enable request capture before opening the installation origin. Record every
   request across the six phases below. Keep URL paths out of the receipt; store the
   SHA-256 of each normalized origin and classify transport as `network`, `cache`,
   or `local`.
4. Install from the pinned same-origin release and record the installed WEB/APP
   artifact hashes and byte sizes. The exact distribution URL is `NO_DATA` until
   pinned by the release owner.
5. Exercise first launch and a fixed task fixture. Enumerate every visible surface
   from the release's `required_surface_ids` manifest for both web and app. Record
   each surface's visibility and complete message result.
6. Disable network at the operating-system boundary. Capture offline launch, all
   surfaces, and a full app restart. Any `network` transport in these phases is RED;
   absence of packet/request capture is `NO_DATA`, not zero.
7. Save a sanitized JSON receipt. Each phase includes its complete request rows,
   exact row count, and SHA-256 of canonical JSON rows. Then run:

   ```sh
   python3 bin/verify_cold_install.py cold-install-receipt.json
   ```

8. A measured GREEN proves only the supplied artifact hashes and captured paths.
   It does not certify accessibility or prove behavior outside the declared surfaces.

## Receipt contract

Use schema `lab.cold-install-receipt/1`. Required fields and accepted values are
illustrated by `tests/test_cold_install.py`. `allowed_origin_sha256` contains only
the normalized same-origin digest. Receipts must never contain raw URLs, private
addresses, profile names, credentials, or audio recordings. The verifier is offline
and reports `GREEN`, `RED`, or `NO_DATA`; incomplete capture is never interpreted as
zero network traffic.

## Yardstick

`python3 -m unittest tests.test_cold_install -v` proves the synthetic complete receipt
is accepted and that missing surfaces, changed artifacts, incomplete capture,
external origins, offline network activity, and forged log hashes are rejected.
Synthetic GREEN is a validator test only. A real cold-install result remains
`NO_DATA` until the Sovereign supplies the pinned release and complete physical
capture.
