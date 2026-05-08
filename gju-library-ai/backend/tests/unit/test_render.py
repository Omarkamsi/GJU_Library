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
