"""Witnessed multi-window context projections: deterministic contracts only."""
import copy
import json
import unittest
from dataclasses import replace

from attention_selector.core import Chunk
from meta_harness.context_window_projection import ModelWindow, project, views
from meta_harness.delegation import encode, sha

REF = sha('synthetic-source')
SCOPE = sha('synthetic-tool-policy')
MODEL_A = sha('fixture-small-model')
MODEL_B = sha('fixture-large-model')
BASE = sha('fixture-base')
HEAD = sha('fixture-head')
QUERY = 'native tool'


def sample():
    chunks = tuple(Chunk('piece-%s' % chr(97+i),
        ('native tool readable source %d. ' % i) * 3, REF,
        100*i, 100*i + 200) for i in range(6))
    windows = (
        ModelWindow(MODEL_A, 128, 1, SCOPE, 7, BASE, HEAD),
        ModelWindow(MODEL_B, 700, 4, SCOPE, 7, BASE, None),
    )
    return chunks, windows


def run(chunks=None, windows=None, verify_chunk=None, verify_window=None,
        scope_ref=SCOPE, epoch=7, query=QUERY):
    source, models = sample()
    return project(query, source if chunks is None else chunks,
        models if windows is None else windows, tool_scope_ref=scope_ref,
        permission_epoch=epoch, verify_chunk=verify_chunk or (lambda _: True),
        verify_window=verify_window or (lambda _: True))


class ContextWindowProjectionTests(unittest.TestCase):
    def test_different_windows_share_references_without_exporting_text(self):
        p = run()
        self.assertEqual(p['receipt']['state'], 'PROJECTED')
        small, big = p['details']
        self.assertEqual([len(d['chunk_refs']) for d in p['details']], [1, 4])
        self.assertLessEqual(small['selected_bytes'], 128)
        self.assertLessEqual(big['selected_bytes'], 700)
        self.assertEqual(small['chunk_refs'][0], big['chunk_refs'][0])
        self.assertLess(len(encode(p['receipt'])), 1024)
        exported = json.dumps(p)
        self.assertNotIn('native tool readable', exported)
        self.assertNotIn(QUERY, exported)
        self.assertFalse(p['receipt']['dispatch_authorized'])
        self.assertFalse(p['receipt']['kv_reuse_authorized'])
        self.assertFalse(p['receipt']['token_context_measured'])

    def test_replay_deterministic(self):
        self.assertEqual(run(), run())

    def test_text_speech_and_machine_identical_state(self):
        p=run()
        v=views(p)
        self.assertEqual(v['text'], v['speech'])
        self.assertEqual(v['text']['state_ref'], v['machine']['state_ref'])
        self.assertEqual(v['text']['summary'], v['machine']['summary'])
        bad=copy.deepcopy(p)
        bad['receipt']['authority']='GRANTED'
        with self.assertRaisesRegex(ValueError,'projection_packet_invalid'):
            views(bad)

    def test_source_revoked_blocks_all(self):
        p=run(verify_chunk=lambda c: c.chunk_id!='piece-b')
        self.assertEqual(p['receipt']['state'],'NO_DATA')
        self.assertEqual(p['receipt']['cause'],'source_not_witnessed')
        self.assertEqual([d['chunk_refs'] for d in p['details']], [[],[]])

    def test_source_mutation_during_selection_blocks_all(self):
        seen={'n':0}
        def witness(_):
            seen['n']+=1
            return seen['n']<=6
        p=run(verify_chunk=witness)
        self.assertEqual(p['receipt']['state'],'NO_DATA')
        self.assertEqual(p['receipt']['cause'],'source_changed_after_selection')

    def test_scope_or_permission_epoch_change_blocks(self):
        _, ws=sample()
        p=run(windows=(replace(ws[0],permission_epoch=8),ws[1]))
        self.assertEqual(p['receipt']['state'],'PARTIAL')
        self.assertEqual(p['details'][0]['cause'],'scope_or_epoch_changed')
        self.assertEqual(p['details'][1]['state'],'PROJECTED')
        p=run(windows=(replace(ws[0],tool_scope_ref=sha('new-scope')),ws[1]))
        self.assertEqual(p['details'][0]['cause'],'scope_or_epoch_changed')

    def test_window_unwitnessed_and_revoked_during_selection(self):
        p=run(verify_window=lambda w:w.model_ref!=MODEL_A)
        self.assertEqual(p['details'][0]['cause'],'window_not_witnessed')
        self.assertEqual(p['details'][1]['state'],'PROJECTED')
        n={'value':0}
        def changing(w):
            if w.model_ref==MODEL_A:
                n['value']+=1
                return n['value']<2
            return True
        p=run(verify_window=changing)
        self.assertEqual(p['details'][0]['cause'],'window_changed_after_selection')
        self.assertEqual(p['details'][1]['state'],'PROJECTED')

    def test_no_context_and_empty_query_fail_closed(self):
        p=run(query='unmatched terms')
        self.assertEqual(p['receipt']['state'],'NO_DATA')
        self.assertEqual([d['cause'] for d in p['details']],
                         ['no_eligible_context','no_eligible_context'])
        with self.assertRaisesRegex(ValueError,'projection_input_invalid'):
            run(query='')

    def test_untrusted_inputs_cannot_mint_window_or_source(self):
        _,ws=sample()
        for altered in (
            (replace(ws[0],permission_epoch=True),ws[1]),
            (replace(ws[0],max_chunks=100),ws[1]),
            (replace(ws[0],model_ref='not-hash'),ws[1]),
            (ws[0],replace(ws[1],model_ref=MODEL_A))
        ):
            with self.subTest(altered=altered):
                with self.assertRaisesRegex(ValueError,'projection_input_invalid'):
                    run(windows=altered)
        source,_=sample()
        with self.assertRaisesRegex(ValueError,'projection_input_invalid'):
            run(chunks=source+(source[0],))

    def test_head_rotation_invalidates_selection_reference(self):
        _,ws=sample()
        a=run()
        new=run(windows=(replace(ws[0],head_ref=sha('new-head')),ws[1]))
        self.assertNotEqual(a['details'][0]['selection_ref'],new['details'][0]['selection_ref'])
        self.assertEqual(a['details'][1]['selection_ref'],new['details'][1]['selection_ref'])

    def test_model_budget_or_tool_scope_does_not_grant(self):
        _,ws=sample()
        switched=run(windows=(replace(ws[0],context_budget_bytes=300),ws[1]))
        self.assertGreater(switched['details'][0]['selected_bytes'],run()['details'][0]['selected_bytes'])
        self.assertFalse(switched['receipt']['dispatch_authorized'])
        self.assertFalse(switched['receipt']['kv_reuse_authorized'])
        p=run(verify_window=lambda _: False)
        self.assertEqual(p['receipt']['state'],'NO_DATA')

    def test_callback_exceptions_fail_closed(self):
        def fail(*_):
            raise RuntimeError('sensitive path/key never goes to receipt')
        p=run(verify_chunk=fail)
        self.assertNotIn('sensitive path',str(p))
        self.assertEqual(p['receipt']['cause'],'source_not_witnessed')
        p=run(verify_window=fail)
        self.assertEqual(p['receipt']['state'],'NO_DATA')


if __name__ == '__main__':
    unittest.main()
