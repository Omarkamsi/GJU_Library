from ingest.docx_loader import load_docx_prose


def test_splits_by_heading_and_detects_lang():
    passages = load_docx_prose("tests/fixtures/mini_services.docx", source="services")
    assert len(passages) >= 2
    en = [p for p in passages if "About" in (p.title or "")][0]
    ar = [p for p in passages if "الخدمات" in (p.title or "")][0]
    assert en.lang == "en" and ar.lang == "ar"
