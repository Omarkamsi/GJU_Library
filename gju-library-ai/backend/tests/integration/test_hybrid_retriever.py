import pytest

from app.retrieval.hybrid import HybridRetriever


@pytest.mark.slow
def test_arabic_hours_query(db):
    res = HybridRetriever(db).search("ما هي ساعات الدوام؟")
    assert res.passages
    blob = " ".join((h.title or "") + " " + h.body for h in res.passages[:3])
    assert "ساعات" in blob or "8" in blob


@pytest.mark.slow
def test_engineering_recommends_dbs(db):
    res = HybridRetriever(db).search("I need recent IEEE papers on robotics")
    slugs = [d.slug for d in res.databases]
    assert any(s in slugs for s in ("ieee", "sciencedirect", "scopus"))
