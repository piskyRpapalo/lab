"""Read-only, non-authorizing recovery readiness projection over the P2 mirror.

A declared rollback plan is not a tested recovery. Existing host witnesses
cannot yet verify human authority or durable fencing, so readiness is NO_DATA.
"""
import re

from .delegation import HEX, LABEL, sha
from .readonly_mirror import ReadOnlyMirror
from .reuse import instrument
from .uncertainty_views import views

SHA1 = re.compile(r'[0-9a-f]{40}\Z')


class RecoveryReadiness:
    """All configuration, including mirror, source and refs, is host-owned."""
    def __init__(self, mirror, source_id, *, previous_sha, candidate_sha, plan_ref, approval_ref):
        if (type(mirror) is not ReadOnlyMirror or type(source_id) is not str or not LABEL.fullmatch(source_id)
                or any(type(x) is not str or not SHA1.fullmatch(x) for x in (previous_sha, candidate_sha))
                or any(type(x) is not str or not HEX.fullmatch(x) for x in (plan_ref, approval_ref))):
            raise ValueError('invalid_host_configuration')
        self._mirror, self._source = mirror, source_id
        self._previous, self._candidate = previous_sha, candidate_sha
        self._plan, self._approval = plan_ref, approval_ref

    def read(self, *, current_head, observed_at):
        """Host clock and current HEAD are observations, not signed authority."""
        try:
            instrument('evidence').valid_time(observed_at)
        except Exception:
            observed_at = None
        evidence = 'NO_DATA'
        reservation = 'NO_DATA'
        head = 'DECLARED_MATCH' if current_head == self._candidate else 'NO_DATA'
        cause = 'independent_recovery_evidence_missing' if head == 'DECLARED_MATCH' else 'candidate_head_mismatch'
        try:
            packet = self._mirror.read(self._source, observed_at=observed_at)
            if self._mirror.verify(packet, self._source, observed_at=observed_at):
                prior = packet['machine']['record']
                if prior['state'] == 'UNKNOWN':
                    evidence = 'UNKNOWN'
                    reservation = 'RETAINED' if prior['reservation']['state'] == 'RETAINED' else 'NO_DATA'
        except Exception:
            pass
        if head != 'DECLARED_MATCH':
            summary = ('Candidate HEAD mismatch; prior outcome unknown; recovery remains unverified.'
                       if evidence == 'UNKNOWN' else
                       'Candidate HEAD mismatch; recovery and authority remain unverified.')
        else:
            summary = ('Prior outcome unknown; recovery and authority remain unverified.' if evidence == 'UNKNOWN'
                       else 'Recovery readiness is unverified; human authority and host evidence are required.')
        record = {'schema': 'preceptoros.lab.recovery-readiness/1', 'kind': 'projection',
                  'state': 'NO_DATA', 'cause': cause, 'observed_at': observed_at,
                  'head': head, 'candidate_sha': self._candidate, 'previous_sha': self._previous,
                  'plan_ref': self._plan, 'approval_ref': self._approval,
                  'plan': 'DECLARED', 'previous_version': 'DECLARED',
                  'previous_provenance': 'NO_DATA', 'isolated_recovery_test': 'NO_DATA',
                  'worker_fence': 'NO_DATA', 'human_approval': 'NO_DATA',
                  'journal_scope': 'ONE_CONFIGURED_TASK', 'journal_outcome': evidence,
                  'reservation': reservation, 'no_retry': True, 'execution_authorized': False,
                  'ttl_seconds': 0,
                  'summary': summary}
        record['projection_ref'] = sha(record)
        return views(record)

    def verify(self, packet, *, current_head, observed_at):
        """Re-read the journal and recompute; self-hashes alone are not witnesses."""
        try:
            return packet == self.read(current_head=current_head, observed_at=observed_at)
        except Exception:
            return False
