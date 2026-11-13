# READINESS-A11Y-CAUSE-01

A candidate HEAD mismatch combined with a P2 UNKNOWN outcome was present in
the machine record but omitted from its text/speech summary. A directed test
reproduced the failure before the fix. The shared summary now states both facts;
when there is no UNKNOWN it still reports a mismatch. The canonical record and
shared projection reference remain unchanged in structure and under 1024 bytes.
No readiness, authority, rollback or actual host status is inferred.
