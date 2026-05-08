from app.retrieval.routing import RuleBasedRouter


def test_detects_arabic():
    assert RuleBasedRouter().route("ما هي ساعات الدوام؟").lang == "ar"


def test_detects_german():
    assert (
        RuleBasedRouter()
        .route("Wo finde ich Bücher der Maschinenbau-Fakultät?")
        .lang
        == "de"
    )


def test_extracts_engineering_subject():
    r = RuleBasedRouter().route("I need IEEE papers on robotics")
    assert any(s in r.subjects for s in ("Engineering", "Computer Science"))
