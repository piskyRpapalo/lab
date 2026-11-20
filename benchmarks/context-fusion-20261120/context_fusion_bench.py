#!/usr/bin/env python3
"""Synthetic evidence-window fusion. NOT LLM KV-cache transfer.

Two context-slot budgets, a fitted 2D orthogonal alignment and independent
math/source judges. Stdlib only; no model, network, tool dispatch or training.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import dataclass, replace

SCHEMA = "preceptoros.lab.context-fusion-synthetic/1"
SEED = 20261120
N = 64


def digest(obj):
    b = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(b).hexdigest()


def rotate(v, theta):
    c, s = math.cos(theta), math.sin(theta)
    return c*v[0]-s*v[1], s*v[0]+c*v[1]


def cosine(a, b):
    den = math.hypot(*a)*math.hypot(*b)
    return (a[0]*b[0]+a[1]*b[1])/den if den else -1.


def angle_fit(anchors):
    """Closed-form 2D orthogonal Procrustes from B to A."""
    if len(anchors) < 3:
        raise ValueError("insufficient_anchors")
    dot = sum(a[0]*b[0]+a[1]*b[1] for a,b in anchors)
    cross = sum(b[0]*a[1]-b[1]*a[0] for a,b in anchors)
    if math.hypot(dot, cross) < 1e-7:
        raise ValueError("ambiguous_alignment")
    return math.atan2(cross, dot)


@dataclass(frozen=True)
class Evidence:
    concept: int
    payload: str
    vector: tuple[float, float]
    scope: str
    generation: str
    fresh: bool
    permitted: bool
    witness: bool
    sha256: str

    @classmethod
    def make(cls, key, value, vec):
        e = cls(key, value, vec, "public-lab", "g1", True, True, True, "")
        return replace(e, sha256=digest([e.concept, e.payload, list(e.vector),
                                         e.scope, e.generation]))


def source_judge(e):
    # Synthetic host fields are trusted only within this fixture; hash != auth.
    return (e.fresh and e.permitted and e.witness and
            e.scope == "public-lab" and e.generation == "g1" and
            e.sha256 == digest([e.concept, e.payload, list(e.vector),
                                e.scope, e.generation]))


def math_judge(angle, holdout):
    return len(holdout) >= 2 and all(
        cosine(a, rotate(b, angle)) >= .995 for a,b in holdout
    )


def retrieve(query, records, angle=0.):
    ranked = sorted(((cosine(query, rotate(e.vector, angle)), e)
                     for e in records), key=lambda p: (-p[0], p[1].concept))
    if not ranked or ranked[0][0] < .975:
        return None
    if len(ranked) > 1 and ranked[0][0]-ranked[1][0] < .05:
        return None
    return ranked[0][1]


def concept(i):
    phi = 2*math.pi*i/29 + .013
    return math.cos(phi), math.sin(phi)


def case(i, rng):
    ka = i % 29
    kb = (i*7+11) % 29
    if ka == kb:
        kb = (kb+1) % 29
    theta = .06 + .90*((i % 7)/6)
    source_a = Evidence.make(ka, "a-value-%03d" % i, concept(ka))
    source_b = Evidence.make(kb, "b-value-%03d" % i, rotate(concept(kb), theta))
    distractors = [
        Evidence.make(j, "decoy-%03d-%d" % (i,j), rotate(concept(j), theta))
        for j in ((kb+8)%29, (kb+17)%29)
    ]
    rng.shuffle(distractors)
    b_window = [source_b]+distractors
    rng.shuffle(b_window)
    anchors = [(concept(j), rotate(concept(j), theta))
               for j in ((kb+d)%29 for d in (1,3,5,7,9,11,13))]
    return source_a, source_b, b_window, anchors


def judge_case(c, arm, attack="none"):
    source_a, source_b, evidence, anchors = c
    if arm == "short-only":
        return "missing_second_source"
    evidence = list(evidence)
    train, check = anchors[:4], anchors[4:]
    if attack == "poisoned-anchors":
        train = [(a, rotate(b,1.7)) for a,b in train]
    if attack == "anisotropic-space":
        deform = lambda v: (1.5*v[0], .55*v[1])
        evidence = [Evidence.make(e.concept,e.payload,deform(e.vector)) for e in evidence]
        train = [(a,deform(b)) for a,b in train]
        check = [(a,deform(b)) for a,b in check]
    for name, changes in {
        "revoked":{"permitted":False}, "stale":{"fresh":False},
        "wrong-generation":{"generation":"g2"},
        "wrong-scope":{"scope":"foreign-app"},
        "missing-witness":{"witness":False},
        "tampered-bytes":{"payload":"changed"},
    }.items():
        if attack == name:
            evidence = [replace(e, **changes) for e in evidence]
    if not all(source_judge(e) for e in [source_a]+evidence):
        return "refused_source"
    if arm == "raw-concat":
        theta = 0.
    elif arm == "aligned":
        try:
            theta = angle_fit(train)
        except ValueError:
            return "refused_alignment"
        if not math_judge(theta, check):
            return "refused_alignment"
    else:
        raise ValueError("unknown_arm")
    chosen = retrieve(concept(source_b.concept), evidence, theta)
    return "correct" if chosen and chosen.payload == source_b.payload else "unresolved"


def run(seed=SEED, count=N):
    if not 1 <= count <= 10000:
        raise ValueError("case_count_out_of_bounds")
    rng = random.Random(seed)
    samples = [case(i,rng) for i in range(count)]
    variants = {
        "short_only":("short-only","none"),
        "raw_concat":("raw-concat","none"),
        "aligned_gated":("aligned","none"),
        "poisoned_anchors":("aligned","poisoned-anchors"),
        "anisotropic_space":("aligned","anisotropic-space"),
        "revoked":("aligned","revoked"),
        "stale":("aligned","stale"),
        "wrong_generation":("aligned","wrong-generation"),
        "wrong_scope":("aligned","wrong-scope"),
        "missing_witness":("aligned","missing-witness"),
        "tampered_bytes":("aligned","tampered-bytes"),
    }
    results={}
    for name,(arm,attack) in variants.items():
        verdicts = [judge_case(c, arm,attack) for c in samples]
        results[name] = {label:verdicts.count(label) for label in
            ("correct","unresolved","missing_second_source","refused_source","refused_alignment")
            if verdicts.count(label)}
    return {"schema":SCHEMA,"seed":seed,"cases":count,
            "short_window_evidence_slots":1,"long_window_evidence_slots":3,
            "context_units":"evidence_slots_not_LLM_tokens",
            "fit_anchor_pairs":4,"heldout_anchor_pairs":3,
            "math":"synthetic_2d_orthogonal_Procrustes_not_KV",
            "judges":["heldout_math_alignment","synthetic_host_provenance"],
            "results":results,"model_inference":False,"tools_executed":0,
            "promotion_authorized":False,
            "NO_DATA":["real_KV_transfer","real_token_windows","real_host_attestation",
                       "real_model_judge_calibration","cross_model_generalization"]}


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed",type=int,default=SEED)
    p.add_argument("--cases",type=int,default=N)
    args=p.parse_args()
    print(json.dumps(run(args.seed,args.cases),sort_keys=True,separators=(",",":")))
