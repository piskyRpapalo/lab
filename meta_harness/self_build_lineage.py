"""Bind existing Git and sealed patch evidence; no provenance or grant is forged.

The optional sealed snapshot implementation is owned by LAB #196. This module
can be installed independently; it abstains when that component is unavailable.
"""
import copy
import hashlib
import re

from .improvement import _digest, _hex
from .self_build_git_witness import GitWitness

SHA1 = re.compile(r'[0-9a-f]{40}\Z')


def binding_ref(proposal_ref, candidate_sha, operation_ref):
    """Seal this ref into the snapshot; operation is exact and host-owned."""
    if not _hex(proposal_ref) or not _hex(operation_ref) or type(candidate_sha) is not str or not SHA1.fullmatch(candidate_sha):
        raise ValueError('invalid_binding')
    return _digest({'schema': 'preceptoros.self-build-lineage-binding/1',
                    'proposal_ref': proposal_ref, 'candidate_sha': candidate_sha,
                    'operation_ref': operation_ref})


def _snapshot_type():
    from .sealed_patch_snapshot import SealedPatch
    return SealedPatch


class Lineage:
    """Host supplies the existing Git witness and an exact operation identity.

    No model may choose the host witness or operation identity. Matching Git
    callbacks are not enough to certify the required host stability: source
    remains NO_DATA until a real, independent stability mechanism is integrated.
    """
    def __init__(self, git_witness, operation_ref):
        if type(git_witness) is not GitWitness or not _hex(operation_ref):
            raise ValueError('invalid_host_configuration')
        self._git, self._operation_ref = git_witness, operation_ref

    def assess(self, proposal, proposal_ref, candidate_sha, operation_ref, snapshot):
        result = {'schema': 'preceptoros.self-build-lineage/1', 'state': 'NO_DATA',
                  'cause': 'real_host_stability', 'integrity': 'NO_DATA',
                  'source': 'NO_DATA', 'execution_authorized': False}
        try:
            p = copy.deepcopy(proposal)
            if (type(p) is not dict or _digest(p) != proposal_ref
                    or operation_ref != self._operation_ref
                    or candidate_sha != self._git.candidate_sha
                    or p['repo_ref'] != self._git.repo_ref or not _hex(p['patch_ref'])):
                result['cause'] = 'identity_mismatch'
                return result
            expected = binding_ref(proposal_ref, candidate_sha, operation_ref)
            try:
                snapshot_type = _snapshot_type()
            except ImportError:
                result['cause'] = 'snapshot_component_unavailable'
                return result
            if type(snapshot) is not snapshot_type:
                result['cause'] = 'snapshot_type_unverified'
                return result
            payload, status = snapshot.read(expected)
            if (type(payload) is not bytes or type(status) is not dict
                    or status.get('snapshot_integrity') != 'VERIFIED'
                    or hashlib.sha256(payload).hexdigest() != p['patch_ref']):
                result['cause'] = 'snapshot_unavailable_or_mismatch'
                return result
            result['integrity'] = 'INTEGRITY_VERIFIED'
            # This observation may use a synthetic stable_source. It can reject
            # discrepancies but cannot establish independent host provenance.
            observation = self._git.inspect({'proposal': p, 'proposal_ref': proposal_ref})
            if type(observation) is not dict or observation.get('state') != 'VERIFIED':
                result['cause'] = ('real_host_stability' if type(observation) is dict
                                   and observation.get('cause') == 'stable_source_unavailable'
                                   else 'git_source_unverified')
            return result
        except Exception:
            result['cause'] = 'lineage_unavailable'
            return result
