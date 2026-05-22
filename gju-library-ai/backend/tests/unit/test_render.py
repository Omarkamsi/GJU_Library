from app.chat.render import RenderInput, render_answer


def _dbs():
    return [("ieee", "IEEE Xplore", "https://ieeexplore.ieee.org")]


def test_db_token_becomes_link_segment_and_text_around_stays_text():
    out = render_answer(
        RenderInput(
            answer_raw="Try IEEE Xplore [DB:ieee] for engineering papers.",
            databases=_dbs(),
            passages=[],
            base_url="http://x",
        )
    )
    types = [s["type"] for s in out.segments]
    assert types == ["text", "link", "text"]
    link = out.segments[1]
    assert link["kind"] == "database" and link["ref"] == "ieee"
    assert link["label"] == "IEEE Xplore"
    assert any(
        c.target_type == "database" and c.target_ref == "ieee" for c in out.clicks
    )


def test_passage_ref_becomes_passage_ref_segment():
    out = render_answer(
        RenderInput(
            answer_raw="The library opens at 8am [P12].",
            databases=[],
            passages=[12],
            base_url="http://x",
        )
    )
    pref = next(s for s in out.segments if s["type"] == "passage_ref")
    assert pref["passage_id"] == 12


def test_unknown_db_slug_is_dropped_safely():
    out = render_answer(
        RenderInput(
            answer_raw="See [DB:bogus] for that.",
            databases=_dbs(),
            passages=[],
            base_url="http://x",
        )
    )
    assert all(s["type"] != "link" for s in out.segments)
    assert out.clicks == []


def test_raw_url_in_model_output_gets_tracked_and_replaced():
    out = render_answer(
        RenderInput(
            answer_raw="See https://www.gju.edu.jo/library for more.",
            databases=[],
            passages=[],
            base_url="http://x",
        )
    )
    link = next(s for s in out.segments if s["type"] == "link")
    assert link["kind"] == "external"
    assert any(c.target_type == "external" for c in out.clicks)


def test_segment_text_is_never_html():
    out = render_answer(
        RenderInput(
            answer_raw="<script>alert(1)</script> ok [DB:ieee]",
            databases=_dbs(),
            passages=[],
            base_url="http://x",
        )
    )
    assert any(
        s["type"] == "text" and "<script>" in s["value"] for s in out.segments
    )


CARD_RAW = (
    "Yes, GJU Library holds this book in its physical collection [P139].\n"
    "📖 Title: The seduction of unreason\n"
    "✍️ Author: Wolin, Richard.\n"
    "🏷️ Genre / Subject: Political Science.\n"
    "🔢 Call Number: JC481.W65 2004\n"
    "📅 Publication Year: 2004\n"
    "🔍 Check availability & shelf location: http://hip.jopuls.org.jo/web/gju"
)


def test_book_card_segment_extracted():
    out = render_answer(
        RenderInput(answer_raw=CARD_RAW, databases=[], passages=[139], base_url="http://x")
    )
    cards = [s for s in out.segments if s["type"] == "book_card"]
    assert len(cards) == 1
    c = cards[0]
    assert c["title"] == "The seduction of unreason"
    assert c["author"] == "Wolin, Richard"
    assert c["genre"] == "Political Science"
    assert c["call_number"] == "JC481.W65 2004"
    assert c["year"] == "2004"
    assert c["opac_url"] == "http://hip.jopuls.org.jo/web/gju"
    assert c["passage_ids"] == [139]
    assert "click_id" in c


def test_book_card_opac_click_registered():
    out = render_answer(
        RenderInput(answer_raw=CARD_RAW, databases=[], passages=[139], base_url="http://x")
    )
    cards = [s for s in out.segments if s["type"] == "book_card"]
    cid = cards[0]["click_id"]
    assert any(
        cl.id == cid and cl.target_type == "external"
        and cl.target_url == "http://hip.jopuls.org.jo/web/gju"
        for cl in out.clicks
    )


def test_two_consecutive_book_cards():
    two = CARD_RAW + "\n\n" + CARD_RAW.replace("[P139]", "[P200]").replace(
        "seduction of unreason", "second book"
    )
    out = render_answer(
        RenderInput(answer_raw=two, databases=[], passages=[139, 200], base_url="http://x")
    )
    cards = [s for s in out.segments if s["type"] == "book_card"]
    assert len(cards) == 2
    assert cards[0]["passage_ids"] == [139]
    assert cards[1]["passage_ids"] == [200]


def test_book_card_with_text_before_and_after():
    wrapped = "Here is what I found:\n\n" + CARD_RAW + "\n\nLet me know if you need more."
    out = render_answer(
        RenderInput(answer_raw=wrapped, databases=[], passages=[139], base_url="http://x")
    )
    types = [s["type"] for s in out.segments]
    assert "book_card" in types
    assert types[0] == "text"
    assert types[-1] == "text"


def test_book_card_year_not_listed():
    raw = CARD_RAW.replace("📅 Publication Year: 2004", "📅 Publication Year: Not listed")
    out = render_answer(
        RenderInput(answer_raw=raw, databases=[], passages=[139], base_url="http://x")
    )
    card = next(s for s in out.segments if s["type"] == "book_card")
    assert card["year"] == "Not listed"
