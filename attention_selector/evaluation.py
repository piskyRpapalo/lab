"""NDCG evaluator requiring explicit, externally supplied relevance labels."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import Mapping, Sequence


def ndcg_at_k(ranked_ids: Sequence[str], gold: Mapping[str, int] | None, k: int | None = None) -> dict:
    if gold is None or not isinstance(gold, Mapping) or not gold:
        return {"status": "NO_DATA", "cause": "gold labels are absent"}
    if (any(not isinstance(chunk_id, str) or not chunk_id for chunk_id in gold) or
            any(type(relevance) is not int or relevance < 0 or relevance > 10 for relevance in gold.values())):
        return {"status": "NO_DATA", "cause": "gold labels contain invalid relevance values"}
    if (isinstance(ranked_ids, (str, bytes)) or not isinstance(ranked_ids, Sequence) or
            any(not isinstance(item, str) for item in ranked_ids) or len(set(ranked_ids)) != len(ranked_ids)):
        return {"status": "NO_DATA", "cause": "ranked ids are invalid or duplicated"}
    limit = len(ranked_ids) if k is None else max(0, min(k, len(ranked_ids)))
    def dcg(values: Sequence[int]) -> Decimal:
        with localcontext() as context:
            context.prec = 50
            total = Decimal(0)
            for index, rel in enumerate(values):
                denominator = Decimal(index + 2).ln() / Decimal(2).ln()
                total += Decimal(2 ** rel - 1) / denominator
            return +total
    actual = [gold.get(item, 0) for item in ranked_ids[:limit]]
    ideal = sorted(gold.values(), reverse=True)[:limit]
    denominator = dcg(ideal)
    if denominator == 0:
        return {"status": "NO_DATA", "cause": "gold labels have no positive relevance"}
    with localcontext() as context:
        context.prec = 50
        score = dcg(actual) / denominator
        milli = int((score * Decimal(1000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return {"status": "MEASURED", "ndcg_milli": milli, "k": limit,
            "queries": 1, "labeled_chunks": len(gold)}
