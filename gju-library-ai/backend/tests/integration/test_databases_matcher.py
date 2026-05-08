from app.retrieval.databases import match_databases


def test_engineering_query_recommends_engineering_db(db):
    hits = match_databases(
        db,
        query_subjects=["Engineering", "Computer Science"],
        passages=[],
        lang="en",
        max_results=3,
    )
    slugs = [h.slug for h in hits]
    assert any(s in slugs for s in ("ieee", "sciencedirect", "scopus", "springer"))
