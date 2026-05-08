from collections import defaultdict

from .interface import PassageHit


def reciprocal_rank_fusion(
    rankings: list[list[PassageHit]], k: int = 60, top: int = 20
) -> list[PassageHit]:
    scores: dict[int, float] = defaultdict(float)
    by_id: dict[int, PassageHit] = {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, start=1):
            scores[hit.id] += 1.0 / (k + rank)
            by_id.setdefault(hit.id, hit)
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top]
    out: list[PassageHit] = []
    for hid, sc in ordered:
        h = by_id[hid]
        out.append(
            PassageHit(
                id=h.id,
                source=h.source,
                source_ref=h.source_ref,
                lang=h.lang,
                title=h.title,
                body=h.body,
                subjects=h.subjects,
                score=sc,
            )
        )
    return out
