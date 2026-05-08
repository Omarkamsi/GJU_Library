from ingest.canonical import Passage


def test_passage_to_embedding_text_includes_title_and_body():
    p = Passage(
        source="faq",
        source_ref="row:3",
        lang="en",
        title="Library hours?",
        body="Open 8am–5pm.",
        subjects=["general"],
    )
    text = p.embedding_text()
    assert "Library hours?" in text
    assert "Open 8am–5pm." in text
    assert "general" in text


def test_passage_embedding_text_omits_missing_title():
    p = Passage(
        source="services",
        source_ref="para:7",
        lang="ar",
        title=None,
        body="حجز قاعات الاجتماعات.",
        subjects=[],
    )
    assert p.embedding_text().startswith("حجز")
