import pytest

from app.retrieval.semantic import semantic_search


@pytest.mark.slow
def test_paraphrase_finds_hours(db):
    hits = semantic_search(db, "what time does the library close?", k=3)
    blob = " ".join((h.title or "") + " " + h.body for h in hits)
    assert "8" in blob and "5" in blob
