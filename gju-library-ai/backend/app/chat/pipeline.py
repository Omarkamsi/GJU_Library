import json
import time
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.llm.interface import LLMClient
from app.llm.prompts import build_book_card, build_messages, build_react_system, _fetch_book_info, _opac_url
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.routing import RuleBasedRouter

_react_available = False
try:
    from app.chat.react_agent import run_react as _run_react
    _react_available = True
except ImportError:
    pass

_groq_react_available = False
try:
    from app.chat.groq_react_agent import run_react as _run_react_groq
    from app.llm.groq_client import GroqClient as _GroqClient
    _groq_react_available = True
except ImportError:
    pass

from .render import PendingClick, RenderInput, render_answer

HISTORY_TURNS = 6  # max messages (3 user+assistant pairs) injected into context

import re as _re


MAX_BOOK_CARDS = 3  # show at most this many book cards per response


def _build_book_cards(passages, lang: str) -> list[str]:
    """
    For each unique-title catalog passage (top MAX_BOOK_CARDS only), fetch web
    info and build a formatted book card string.
    """
    cards: list[str] = []
    seen_titles: set[str] = set()
    for p in passages:
        if p.source != "catalog" or not p.title or p.title in seen_titles:
            continue
        if len(cards) >= MAX_BOOK_CARDS:
            break
        seen_titles.add(p.title)

        raw_author = ""
        if "Author:" in p.body:
            raw_author = p.body.split("Author:")[1].split("Call Number:")[0].strip().rstrip(".")
        clean_author = _re.sub(r",?\s*\d{4}[-–]?\d{0,4}\.?\s*$", "", raw_author).strip(" ,.")

        info = _fetch_book_info(p.title, clean_author)
        isbn = info.get("isbn", "") if info else ""
        opac_link = _opac_url(p.title, isbn=isbn, author=clean_author)

        cards.append(build_book_card(p, info, opac_link, lang))
    return cards


def _get_or_create_conversation(db: Session, user_id: str, conversation_id: str | None) -> str:
    """Return existing conversation_id or create a new one."""
    if conversation_id:
        exists = db.execute(
            text("SELECT id FROM chat_conversations WHERE id = :cid AND user_id = :uid"),
            {"cid": conversation_id, "uid": user_id},
        ).fetchone()
        if exists:
            db.execute(
                text("UPDATE chat_conversations SET last_active_at = NOW() WHERE id = :cid"),
                {"cid": conversation_id},
            )
            return conversation_id

    new_id = str(uuid.uuid4())
    db.execute(
        text("INSERT INTO chat_conversations (id, user_id) VALUES (:id, :uid)"),
        {"id": new_id, "uid": user_id},
    )
    return new_id


def _load_history(db: Session, conversation_id: str) -> list[tuple[str, str]]:
    """Return the last HISTORY_TURNS messages as (role, content) pairs."""
    rows = db.execute(
        text(
            "SELECT role, content FROM conversation_messages "
            "WHERE conversation_id = :cid "
            "ORDER BY created_at DESC LIMIT :n"
        ),
        {"cid": conversation_id, "n": HISTORY_TURNS},
    ).fetchall()
    return [(r.role, r.content) for r in reversed(rows)]


def _save_messages(db: Session, conversation_id: str, user_msg: str, assistant_msg: str) -> None:
    db.execute(
        text(
            "INSERT INTO conversation_messages (conversation_id, role, content) VALUES "
            "(:cid, 'user', :content)"
        ),
        {"cid": conversation_id, "content": user_msg},
    )
    db.execute(
        text(
            "INSERT INTO conversation_messages (conversation_id, role, content) VALUES "
            "(:cid, 'assistant', :content)"
        ),
        {"cid": conversation_id, "content": assistant_msg},
    )


def stream_chat(db: Session, user_id: str, query: str, llm: LLMClient, conversation_id: str | None = None):
    """Yields SSE-shaped strings ('data: <json>\\n\\n').
    Sequence: meta → token* → done. Persists query_log + click_events on done."""
    import json as _json
    s = get_settings()
    t0 = time.perf_counter()

    conv_id = _get_or_create_conversation(db, user_id, conversation_id)

    router = RuleBasedRouter()
    route = router.route(query)
    res = HybridRetriever(db, router=router).search(
        query, lang=route.lang, k=s.final_topk
    )

    # Build book cards in Python before LLM call (avoids asking the LLM to format them)
    book_cards = _build_book_cards(res.passages, route.lang)

    yield f"data: {_json.dumps({'type': 'meta', 'lang': route.lang, 'conversation_id': conv_id})}\n\n"

    history = _load_history(db, conv_id)
    msgs = build_messages(query, res, lang=route.lang, history=history)
    pieces: list[str] = []
    llm_t0 = time.perf_counter()

    if _groq_react_available and s.enable_web_search and isinstance(llm, _GroqClient):
        from app.llm.interface import ChatMessage as _CM
        msgs = [_CM("system", build_react_system(route.lang)) if m.role == "system" else m for m in msgs]
        answer_raw = _run_react_groq(llm, msgs)
        yield f"data: {_json.dumps({'type': 'token', 'text': answer_raw})}\n\n"
    elif _react_available and s.enable_web_search and hasattr(llm, "generate_raw"):
        from app.llm.interface import ChatMessage as _CM
        msgs = [_CM("system", build_react_system(route.lang)) if m.role == "system" else m for m in msgs]
        answer_raw = _run_react(llm, msgs)
        yield f"data: {_json.dumps({'type': 'token', 'text': answer_raw})}\n\n"
    else:
        for piece in llm.stream(msgs, temperature=0.2, max_tokens=350):
            pieces.append(piece)
            yield f"data: {_json.dumps({'type': 'token', 'text': piece})}\n\n"
        answer_raw = "".join(pieces)

    llm_latency = int((time.perf_counter() - llm_t0) * 1000)

    # Prepend Python-generated book cards so the done payload has the full answer
    if book_cards:
        answer_raw = "\n\n".join(book_cards) + "\n\n" + answer_raw

    rin = RenderInput(
        answer_raw=answer_raw,
        databases=[(d.slug, d.name, d.url) for d in res.databases],
        passages=[p.id for p in res.passages],
        base_url=s.app_base_url,
    )
    rout = render_answer(rin)

    qid = db.execute(
        text(
            """
            INSERT INTO query_log
              (user_id, raw_query, lang, extracted_filters, retrieved_passage_ids,
               shown_database_slugs, answer_text, model_name, latency_ms)
            VALUES (:uid,:q,:lang,CAST(:filters AS jsonb),:pids,:dbs,:atext,:model,:lat)
            RETURNING id
            """
        ),
        {
            "uid": user_id,
            "q": query,
            "lang": route.lang,
            "filters": _json.dumps({"subjects": route.subjects}),
            "pids": [p.id for p in res.passages],
            "dbs": [d.slug for d in res.databases],
            "atext": rout.answer_text,
            "model": getattr(llm, "_model", "unknown"),
            "lat": llm_latency,
        },
    ).scalar_one()
    for c in rout.clicks:
        db.execute(
            text(
                """
                INSERT INTO click_events
                  (id, user_id, query_id, target_type, target_ref, target_url)
                VALUES (:id, :uid, :qid, :tt, :tr, :url)
                """
            ),
            {"id": c.id, "uid": user_id, "qid": qid, "tt": c.target_type, "tr": c.target_ref, "url": c.target_url},
        )
    _save_messages(db, conv_id, query, rout.answer_text)
    db.commit()

    payload = {
        "type": "done",
        "query_id": qid,
        "conversation_id": conv_id,
        "segments": rout.segments,
        "answer_text": rout.answer_text,
        "citations": [
            {"id": p.id, "title": p.title, "source": p.source} for p in res.passages
        ],
        "suggested_databases": [
            {"slug": d.slug, "name": d.name} for d in res.databases
        ],
        "lang": route.lang,
        "latency_ms": int((time.perf_counter() - t0) * 1000),
    }
    yield f"data: {_json.dumps(payload)}\n\n"


@dataclass
class ChatTurnOut:
    query_id: int
    conversation_id: str
    segments: list[dict[str, Any]]
    answer_text: str
    citations: list[dict]
    suggested_databases: list[dict]
    clicks: list[PendingClick]
    lang: str
    latency_ms: int


def run_chat(
    db: Session, user_id: str, query: str, llm: LLMClient, conversation_id: str | None = None
) -> ChatTurnOut:
    s = get_settings()
    t0 = time.perf_counter()

    conv_id = _get_or_create_conversation(db, user_id, conversation_id)

    router = RuleBasedRouter()
    route = router.route(query)
    res = HybridRetriever(db, router=router).search(
        query, lang=route.lang, k=s.final_topk
    )
    # Build book cards in Python before LLM call (avoids asking the LLM to format them)
    book_cards = _build_book_cards(res.passages, route.lang)

    history = _load_history(db, conv_id)
    msgs = build_messages(query, res, lang=route.lang, history=history)

    if _groq_react_available and s.enable_web_search and isinstance(llm, _GroqClient):
        from app.llm.interface import ChatMessage as _CM
        msgs = [_CM("system", build_react_system(route.lang)) if m.role == "system" else m for m in msgs]
        answer_raw = _run_react_groq(llm, msgs)
        llm_latency_ms = 0
        llm_model = getattr(llm, "_model", "unknown")
    elif _react_available and s.enable_web_search and hasattr(llm, "generate_raw"):
        from app.llm.interface import ChatMessage as _CM
        msgs = [_CM("system", build_react_system(route.lang)) if m.role == "system" else m for m in msgs]
        answer_raw = _run_react(llm, msgs)
        llm_latency_ms = 0
        llm_model = getattr(llm, "_model", "unknown")
    else:
        llm_resp = llm.complete(msgs, temperature=0.2, max_tokens=350)
        answer_raw = llm_resp.text
        llm_latency_ms = llm_resp.latency_ms
        llm_model = llm_resp.model
    if book_cards:
        answer_raw = "\n\n".join(book_cards) + "\n\n" + answer_raw

    rin = RenderInput(
        answer_raw=answer_raw,
        databases=[(d.slug, d.name, d.url) for d in res.databases],
        passages=[p.id for p in res.passages],
        base_url=s.app_base_url,
    )
    rout = render_answer(rin)

    qid = db.execute(
        text(
            """
            INSERT INTO query_log
              (user_id, raw_query, lang, extracted_filters, retrieved_passage_ids,
               shown_database_slugs, answer_text, model_name, latency_ms)
            VALUES (:uid,:q,:lang,CAST(:filters AS jsonb),:pids,:dbs,:atext,:model,:lat)
            RETURNING id
            """
        ),
        {
            "uid": user_id,
            "q": query,
            "lang": route.lang,
            "filters": json.dumps({"subjects": route.subjects}),
            "pids": [p.id for p in res.passages],
            "dbs": [d.slug for d in res.databases],
            "atext": rout.answer_text,
            "model": llm_model,
            "lat": llm_latency_ms,
        },
    ).scalar_one()

    for c in rout.clicks:
        db.execute(
            text(
                """
                INSERT INTO click_events
                  (id, user_id, query_id, target_type, target_ref, target_url)
                VALUES (:id, :uid, :qid, :tt, :tr, :url)
                """
            ),
            {
                "id": c.id,
                "uid": user_id,
                "qid": qid,
                "tt": c.target_type,
                "tr": c.target_ref,
                "url": c.target_url,
            },
        )
    _save_messages(db, conv_id, query, rout.answer_text)
    db.commit()

    return ChatTurnOut(
        query_id=qid,
        conversation_id=conv_id,
        segments=rout.segments,
        answer_text=rout.answer_text,
        citations=[
            {"id": p.id, "title": p.title, "source": p.source}
            for p in res.passages
        ],
        suggested_databases=[
            {"slug": d.slug, "name": d.name} for d in res.databases
        ],
        clicks=rout.clicks,
        lang=route.lang,
        latency_ms=int((time.perf_counter() - t0) * 1000),
    )
