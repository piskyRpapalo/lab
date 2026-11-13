# SELF-IMPROVEMENT-NO-CHANGE-01

A verified receipt set with no failure previously returned PROPOSAL_ONLY with
no suggestions and demanded human review. Schema version 2 returns NO_CHANGE
with cause no_failure_in_supplied_receipts, or REVIEW_REQUIRED when failure
suggestions exist. Both remain non-authorizing. This claim is limited to the
supplied independently witnessed receipts; it does not claim system health or
completeness. Missing or invalid witness remains NO_DATA. Version 2 makes the
state change explicit to consumers; migration of external consumers is NO_DATA.
Tests use synthetic witnesses. Roll back by reverting the versioned change.
