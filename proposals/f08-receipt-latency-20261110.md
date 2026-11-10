# F-08 · Time-to-declared-FIRMO observation

**State: PROPOSAL; no live signature verification.** Source: the F-08 operating flow in `ideas9nov.txt`, [buzon#61](https://github.com/piskyRpapalo/buzon/issues/61), [public Mesa#4](https://github.com/piskyRpapalo/preceptoros-public-mesa/issues/4).

The Python stdlib-only script computes nearest-rank p50/p90/p99 of elapsed seconds for an **offline, locally supplied and already scrubbed** closed JSON object `{"events":[...]}`. Each row has opaque `id`, UTC `opened_at`, either `signed_at` + `receipt_ref` or a `cause` for unsigned. Unknown fields, repeated IDs, naïve times, negative durations, or missing evidence cause fail-closed rejection.

```sh
python3 bin/f08_receipt_latency.py /local/scrubbed-input.json
python3 -m unittest discover -s tests -p test_f08_receipt_latency.py
```

Output contains counts, percentiles and `NO_DATA` causes, no source IDs or input references. `COMPUTED_FROM_DECLARED_INPUT` is NOT `FIRMO_VERIFIED`: a mere timestamp or hash cannot verify Sovereign authorization. The `preceptoros.lab.f08-observation/1` envelope is provisional, not an admitted Babel term.

**Acceptance:** 2 independent synthetic test runs, zero input IDs/refs emitted. **NO_DATA:** actual signature-ledger join, live MTTR, deployed cycles. Next piece only after sign-off: compare against head-specific human FIRMO events. Do not automate merge or claim authority.
