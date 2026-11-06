# Comparing declared benchmark receipts

`python3 bin/compare_receipts.py comparison.json` reads an object containing
`left` and `right` receipt objects. Each receipt needs `state: MEASURED`,
`device`, `observed_at`, `source`, numeric `value`, and these matching strings:
`workload`, `workload_version`, `parameters_digest`, `metric`, `unit`, `method`.
The digest is the lowercase SHA-256 of the benchmark parameters, supplied by
the operator; this tool checks its shape but does not recompute it.

The result is `COMPARABLE` with right-minus-left only if the declared fields
match and the values and difference are finite. Otherwise it is `NO_DATA`
with a cause. Exit status is 0 for comparable, 1 otherwise.

This is a metadata check, not evidence that either source is genuine, that
the parameters digest corresponds to the actual run, or that the measurements
are scientifically equivalent. Sources must be reviewed independently. Do not
commit private identifiers, prompts, or responses as receipts.
