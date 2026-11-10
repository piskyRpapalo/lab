# F-11 · LoRA origin-aware evaluation admission (offline)

**Status:** research proposal, not a trained model. Complements the existing `benchmarks/self-preference-20261025/` which already measures same- and cross-family detections using third-family judges. **Do not rebuild that benchmark.**

Source: `ideas9nov.txt` F-11, [buzon#61](https://github.com/piskyRpapalo/buzon/issues/61), [study#105](https://github.com/piskyRpapalo/study/pull/105). Missing gate: check SHA-256 source provenance and reject common origin groups across training and evaluation, before invoking the existing scorer.

Input: locally generated closed `{"samples":[{"sample_sha256":"64 lowercase hex","origin_sha256":"64 lowercase hex","split":"train|eval","class":"same|cross"}]}`. The pure function fails closed on duplicate sample hashes, invalid fields, and cross-split origin collisions. Evaluation requires at least 6 entries each for same/cross to mark a synthetic fixture ready; the threshold follows the proposal, **not** an estimate of statistical power. Output reveals only counts/NO_DATA, never a digest or sample text.

```sh
python3 bin/f11_origin_admission.py /local/scrubbed-hash-manifest.json
python3 -m unittest discover -s tests -p test_f11_origin_admission.py
```

**NO_DATA:** actual corpus membership/preimages, train/eval data ownership and consent, LoRA run, measured self-preference delta, Fisher test and hardware joules. Admission is not a security signature or a statistical result. Next: join verified manifest with existing benchmark after human-approved data scope.
