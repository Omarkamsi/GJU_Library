from app.llm.prompts import build_messages
from app.retrieval.interface import DatabaseHit, PassageHit, RetrievalResult


def _r() -> RetrievalResult:
    return RetrievalResult(
        passages=[
            PassageHit(1, "faq", "r1", "en", "Library hours", "Open 8am-5pm.", [], 0.9)
        ],
        databases=[
            DatabaseHit(
                "ieee",
                "IEEE Xplore",
                "https://ieeexplore.ieee.org",
                ["Engineering"],
                "IEEE journals.",
                0.8,
            )
        ],
        debug={"lang": "en"},
    )


def test_arabic_system_prompt_in_arabic():
    msgs = build_messages("ما هي ساعات الدوام؟", _r(), lang="ar")
    assert msgs[0].role == "system"
    assert "العربية" in msgs[0].content


def test_messages_contain_passages_and_db_tokens():
    msgs = build_messages("library hours?", _r(), lang="en")
    user_text = msgs[-1].content
    assert "[P1]" in user_text
    assert "[DB:ieee]" in user_text
    assert "https://" not in user_text
