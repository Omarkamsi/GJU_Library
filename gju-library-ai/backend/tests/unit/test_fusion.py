from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.interface import PassageHit


def _h(i: int) -> PassageHit:
    return PassageHit(
        id=i, source="x", source_ref=f"r{i}", lang="en",
        title=None, body="", subjects=[], score=0.0,
    )


def test_rrf_prefers_consensus():
    # id=2 appears in both rankings (top), id=1 appears only in `a`.
    # Consensus must beat a single high rank.
    a = [_h(1), _h(2), _h(3)]
    b = [_h(2), _h(4), _h(5)]
    fused = reciprocal_rank_fusion([a, b], k=60, top=4)
    assert fused[0].id == 2
    assert {h.id for h in fused[:2]} == {1, 2}
