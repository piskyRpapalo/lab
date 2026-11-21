"""Excluded sources must not influence authorized lexical ranking."""
import hashlib
import unittest
from attention_selector.core import Chunk, SelectionPolicy, select_chunks

class SelectorPolicyIsolation(unittest.TestCase):
    def setUp(self):
        self.base=[Chunk("allowed-a","alpha","source-a",0,5),
                   Chunk("allowed-b","beta","source-b",0,4)]
        self.policy=SelectionPolicy(max_chunks=1,max_chunk_bytes=24,max_total_bytes=24)
    def selected(self,others=(),policy=None):
        r=select_chunks("alpha beta",[*self.base,*others],policy or self.policy)
        return r.status,[x.chunk.chunk_id for x in r.selected]
    def test_excluded_boolean_cannot_change_allowed_choice(self):
        base=self.selected()
        poisons=[Chunk("out-%02d"%i,"alpha","private",0,5,excluded=True) for i in range(14)]
        self.assertEqual(base,("VERBATIM",["allowed-a"]))
        self.assertEqual(self.selected(poisons),base)
    def test_explicit_exclude_source_id_cannot_change_choice(self):
        private=hashlib.sha256(b"private-source").hexdigest()
        pol=SelectionPolicy(max_chunks=1,max_chunk_bytes=24,max_total_bytes=24,exclude_source_ids=(private,))
        base=self.selected(policy=pol)
        poisons=[Chunk("out-%02d"%i,"alpha",private,0,5) for i in range(14)]
        self.assertEqual(self.selected(poisons,pol),base)
    def test_oversize_chunk_cannot_change_choice(self):
        base=self.selected()
        poisons=[Chunk("out-%02d"%i,"alpha "*30,"private",0,180) for i in range(14)]
        self.assertEqual(self.selected(poisons),base)
    def test_private_only_terms_dont_authorize_output(self):
        r=select_chunks("secret",[Chunk("secret-id","secret secret","private",0,13,excluded=True)],self.policy)
        self.assertEqual((r.status,len(r.selected)),("NO_DATA",0))
    def test_private_permutations_have_identical_selection(self):
        poisons=[Chunk("out-%02d"%i,"alpha","private",0,5,excluded=True) for i in range(14)]
        self.assertEqual(self.selected(poisons),self.selected(reversed(poisons)))
        self.assertEqual(self.selected(poisons),self.selected())
