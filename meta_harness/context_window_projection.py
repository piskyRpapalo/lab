"""Host-witnessed, bounded context projection to heterogeneous model windows.

Reuses LAB attention_selector. This creates no cache, service, model request,
permission, worker, model KV transfer, or tool execution. Source text stays
inside this call; only hash-bound references and byte counts are exported.
All callbacks and policy values MUST be supplied by a trusted host.
"""
from dataclasses import dataclass

from attention_selector.core import Chunk, SelectionPolicy, select_chunks
from .delegation import HEX, LABEL, encode, sha

SCHEMA = 'preceptoros.context-window-projection/1'


@dataclass(frozen=True)
class ModelWindow:
    model_ref: str
    context_budget_bytes: int
    max_chunks: int
    tool_scope_ref: str
    permission_epoch: int
    base_ref: str
    head_ref: str | None


def _ref(value):
    return type(value) is str and HEX.fullmatch(value) is not None


def _closed(windows, chunks, query, tool_scope_ref, permission_epoch):
    if (type(query) is not str or not 1 <= len(query.encode('utf-8')) <= 512
            or type(windows) is not tuple or not 1 <= len(windows) <= 6
            or type(chunks) is not tuple or not 1 <= len(chunks) <= 32
            or not _ref(tool_scope_ref) or type(permission_epoch) is not int
            or not 0 <= permission_epoch < 2**63):
        return False
    models, chunks_seen = set(), set()
    for w in windows:
        if (type(w) is not ModelWindow or not all(_ref(v) for v in
                (w.model_ref, w.tool_scope_ref, w.base_ref))
                or w.head_ref is not None and not _ref(w.head_ref)
                or type(w.context_budget_bytes) is not int
                or not 64 <= w.context_budget_bytes <= 8192
                or type(w.max_chunks) is not int or not 1 <= w.max_chunks <= 8
                or type(w.permission_epoch) is not int
                or w.model_ref in models):
            return False
        models.add(w.model_ref)
    for c in chunks:
        if (type(c) is not Chunk or type(c.chunk_id) is not str
                or not LABEL.fullmatch(c.chunk_id)
                or c.chunk_id in chunks_seen or not _ref(c.source_id)
                or type(c.text) is not str or not 1 <= c.byte_count <= 3072
                or type(c.start_byte) is not int or type(c.end_byte) is not int
                or not 0 <= c.start_byte < c.end_byte
                or type(c.excluded) is not bool):
            return False
        chunks_seen.add(c.chunk_id)
    return True


def _receipt(state, cause, query, details, tool_scope_ref, epoch):
    record = {
        'schema': SCHEMA, 'state': state, 'cause': cause,
        'query_ref': sha(query), 'details_ref': sha(details),
        'windows': len(details), 'scope_ref': tool_scope_ref,
        'permission_epoch': epoch, 'authority': 'NONE',
        'dispatch_authorized': False, 'kv_reuse_authorized': False,
        'token_context_measured': False, 'promotion': 'NOT_AUTHORIZED',
    }
    record['receipt_ref'] = sha(record)
    if len(encode(record)) >= 1024:
        raise ValueError('projection_receipt_budget')
    return {'receipt': record, 'details': details}


def _none(model, cause):
    return {'model_ref': model, 'state': 'NO_DATA', 'cause': cause,
            'chunk_refs': [], 'selected_bytes': 0, 'selection_ref': None}


def project(query, chunks, windows, *, verify_chunk, verify_window,
            tool_scope_ref, permission_epoch):
    """Return independent per-model references. No source text leaves this API.

    The host must attest exact source bytes/ACL and model scope using independent
    callbacks. The callback is rechecked after selection, but this is not an
    atomic resource lease; every eventual execution still needs S1 and pins.
    The budgets are UTF-8 text bytes, NOT model-token context lengths.
    """
    if not _closed(windows, chunks, query, tool_scope_ref, permission_epoch):
        raise ValueError('projection_input_invalid')
    if not callable(verify_chunk) or not callable(verify_window):
        raise ValueError('host_witness_missing')

    def sources_current():
        try:
            return all(verify_chunk(c) is True for c in chunks)
        except Exception:
            return False

    if not sources_current():
        return _receipt('NO_DATA', 'source_not_witnessed', query,
                        [_none(w.model_ref, 'source_not_witnessed') for w in windows],
                        tool_scope_ref, permission_epoch)
    details = []
    for w in windows:
        if (w.tool_scope_ref != tool_scope_ref or
                w.permission_epoch != permission_epoch):
            details.append(_none(w.model_ref, 'scope_or_epoch_changed'))
            continue
        try:
            granted = verify_window(w) is True
        except Exception:
            granted = False
        if not granted:
            details.append(_none(w.model_ref, 'window_not_witnessed'))
            continue
        policy = SelectionPolicy(max_chunks=w.max_chunks,
            max_chunk_bytes=min(w.context_budget_bytes, 3072),
            max_total_bytes=w.context_budget_bytes)
        result = select_chunks(query, chunks, policy)
        if result.status != 'VERBATIM':
            details.append(_none(w.model_ref, 'no_eligible_context'))
            continue
        chunk_refs = [
            sha({'source_ref': r.chunk.source_id, 'chunk_ref': r.chunk.sha256,
                 'chunk_id': r.chunk.chunk_id, 'range': [r.chunk.start_byte,
                                                        r.chunk.end_byte]})
            for r in result.selected
        ]
        try:
            current = verify_window(w) is True
        except Exception:
            current = False
        if not current:
            details.append(_none(w.model_ref, 'window_changed_after_selection'))
            continue
        details.append({
            'model_ref': w.model_ref, 'state': 'PROJECTED', 'cause': None,
            'chunk_refs': chunk_refs,
            'selected_bytes': sum(r.chunk.byte_count for r in result.selected),
            'selection_ref': sha({
                'query_ref': sha(query), 'model_ref': w.model_ref,
                'base_ref': w.base_ref, 'head_ref': w.head_ref,
                'permission_epoch': w.permission_epoch,
                'tool_scope_ref': w.tool_scope_ref,
                'context_budget_bytes': w.context_budget_bytes,
                'chunk_refs': chunk_refs,
            }),
        })
    if not sources_current():
        return _receipt('NO_DATA', 'source_changed_after_selection', query,
                        [_none(w.model_ref, 'source_changed_after_selection')
                         for w in windows], tool_scope_ref, permission_epoch)
    success = sum(d['state'] == 'PROJECTED' for d in details)
    state = 'PROJECTED' if success == len(details) else (
        'PARTIAL' if success else 'NO_DATA')
    return _receipt(state, None if success == len(details) else 'window_not_ready',
                    query, details, tool_scope_ref, permission_epoch)


def views(packet):
    """Identical status for reading, speech/Acho and machine clients."""
    if (type(packet) is not dict or set(packet) != {'receipt', 'details'}
            or type(packet['receipt']) is not dict
            or packet['receipt'].get('schema') != SCHEMA
            or packet['receipt'].get('details_ref') != sha(packet['details'])
            or packet['receipt'].get('receipt_ref') != sha({
                k: v for k, v in packet['receipt'].items() if k != 'receipt_ref'})):
        raise ValueError('projection_packet_invalid')
    r = packet['receipt']
    summary = ('Context references projected.' if r['state'] == 'PROJECTED'
               else 'Context projection incomplete: '+str(r['cause'])+'.')
    result = {'state_ref': r['receipt_ref'], 'summary': summary}
    return {'text': dict(result), 'speech': dict(result),
            'machine': {'state_ref': r['receipt_ref'],
                        'summary': summary, 'record': dict(r)}}
