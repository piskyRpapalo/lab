"""Offline improvement suggestions from independently witnessed delegation receipts.

The host-supplied witness must verify provenance and freshness for the exact
receipt; a checksum by itself is not a witness. This module only prepares
review suggestions and has no execution, permission or persistence interface.
"""
import copy

from .delegation import NEXT, sha, verify

MAX_RECEIPTS = 64


def propose(receipts, *, verify_source=None):
    """Return bounded, deterministic suggestions or explicit missing evidence.

    verify_source(receipt) is a trusted, local, read-only host capability; it
    must return the literal True only for fresh and independently sourced data.
    Receipt data and witness results do not confer authority to apply a change.
    """
    empty = {'schema': 'preceptoros.self-improvement/1', 'state': 'NO_DATA',
             'cause': 'evidence_unavailable', 'suggestions': [],
             'execution_authorized': False}
    try:
        if type(receipts) is not list or not 1 <= len(receipts) <= MAX_RECEIPTS:
            return empty
        rows = copy.deepcopy(receipts)
        if not callable(verify_source) or any(not verify(r) for r in rows):
            return empty
        refs = [r['receipt_ref'] for r in rows]
        if len(set(refs)) != len(refs):
            return empty
        # Do not let a witness mutate the actual records used to form a proposal.
        for row in rows:
            if verify_source(copy.deepcopy(row)) is not True:
                return empty
        groups = {}
        for row in rows:
            category = row['failure_class']
            if category == 'NONE':
                continue
            groups.setdefault(category, []).append(row['receipt_ref'])
        suggestions = [{'failure_class': category, 'next_action': NEXT[category],
                        'evidence_refs': sorted(groups[category])}
                       for category in sorted(groups)]
        body = {'schema': empty['schema'], 'state': 'PROPOSAL_ONLY',
                'cause': 'human_review_required', 'suggestions': suggestions,
                'execution_authorized': False}
        return dict(body, proposal_ref=sha(body))
    except Exception:
        return empty
