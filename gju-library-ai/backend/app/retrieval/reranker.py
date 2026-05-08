from .interface import PassageHit

_reranker = None


def get_reranker(model_name: str = "BAAI/bge-reranker-v2-m3"):
    global _reranker
    if _reranker is None:
        from FlagEmbedding import FlagReranker  # lazy; requires `[ml]` extra

        _reranker = FlagReranker(model_name, use_fp16=False)
    return _reranker


def rerank(
    query: str,
    hits: list[PassageHit],
    top: int = 5,
    model_name: str = "BAAI/bge-reranker-v2-m3",
) -> list[PassageHit]:
    if not hits:
        return []
    pairs = [(query, (h.title or "") + "\n" + h.body) for h in hits]
    scores = get_reranker(model_name).compute_score(pairs, normalize=True)
    if isinstance(scores, float):
        scores = [scores]
    scored = list(zip(hits, scores))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [
        PassageHit(
            id=h.id,
            source=h.source,
            source_ref=h.source_ref,
            lang=h.lang,
            title=h.title,
            body=h.body,
            subjects=h.subjects,
            score=float(s),
        )
        for h, s in scored[:top]
    ]
