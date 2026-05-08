from app.retrieval.lexical import lexical_search


def test_finds_english_match(seeded_db):
    hits = lexical_search(seeded_db, "library hours", k=5)
    assert "Library hours" in [h.title for h in hits]


def test_finds_arabic_match(seeded_db):
    hits = lexical_search(seeded_db, "ساعات الدوام", k=5)
    assert any("ساعات" in (h.title or "") for h in hits)
