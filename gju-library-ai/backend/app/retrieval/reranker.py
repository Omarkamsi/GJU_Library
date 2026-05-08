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
    try:
        scores = get_reranker(model_name).compute_score(pairs, normalize=True)
    except (AttributeError, TypeError, RuntimeError) as e:
        # FlagEmbedding/transformers version skew can break the cross-encoder.
        # Fall back to fused-rank order so the chat pipeline still answers.
        import logging

        logging.getLogger(__name__).warning(
            "reranker unavailable (%s); using fused order", e.__class__.__name__
        )
        return hits[:top]
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
