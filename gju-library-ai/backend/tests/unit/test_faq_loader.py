from ingest.faq_loader import load_faq_xlsx


def test_loads_one_passage_per_language_per_row():
    passages = load_faq_xlsx("tests/fixtures/mini_faq.xlsx", source="faq_general")
    assert len(passages) == 3
    en = [p for p in passages if p.lang == "en"]
    ar = [p for p in passages if p.lang == "ar"]
    assert len(en) == 1 and len(ar) == 2
    assert "library hours" in en[0].title.lower()
    assert "8am–5pm" in en[0].body
    assert "General" in en[0].subjects
