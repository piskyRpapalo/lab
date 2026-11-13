# Receipt formatter · bounded public draft

Existing format_receipt interpolated untrusted command, machine, schema and
other free text into a purported counts-only draft. A synthetic private canary
demonstrates the leak. This slice retains the existing formatter and allows
only closed, bounded public fields; unknown values become NO_DATA. No receipt
is posted, signed or rewritten. Hashes prove integrity only; publication still
requires human review. Tests cover malicious fields, unknown schemas, invalid
numbers and normal historical format. Rollback: reviewed revert of this slice.
