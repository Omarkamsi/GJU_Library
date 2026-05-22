import json
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.llm.interface import LLMClient
from app.llm.prompts import build_messages
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.routing import RuleBasedRouter

from .render import PendingClick, RenderInput, render_answer


def stream_chat(db: Session, user_id: str, query: str, llm: LLMClient):
    """Yields SSE-shaped strings ('data: <json>\\n\\n').
    Sequence: meta → token* → done. Persists query_log + click_events on done."""
    import json as _json
    s = get_settings()
    t0 = time.perf_counter()

    router = RuleBasedRouter()
    route = router.route(query)
    res = HybridRetriever(db, router=router).search(
        query, lang=route.lang, k=s.final_topk
    )

    yield f"data: {_json.dumps({'type': 'meta', 'lang': route.lang})}\n\n"

    msgs = build_messages(query, res, lang=route.lang)
    pieces: list[str] = []
    llm_t0 = time.perf_counter()
    for piece in llm.stream(msgs, temperature=0.2, max_tokens=800):
        pieces.append(piece)
        yield f"data: {_json.dumps({'type': 'token', 'text': piece})}\n\n"
    llm_latency = int((time.perf_counter() - llm_t0) * 1000)
    answer_raw = "".join(pieces)

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
    db.commit()

    payload = {
        "type": "done",
        "query_id": qid,
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
    segments: list[dict[str, Any]]
    answer_text: str
    citations: list[dict]
    suggested_databases: list[dict]
    clicks: list[PendingClick]
    lang: str
    latency_ms: int


def run_chat(
    db: Session, user_id: str, query: str, llm: LLMClient
) -> ChatTurnOut:
    s = get_settings()
    t0 = time.perf_counter()

    router = RuleBasedRouter()
    route = router.route(query)
    res = HybridRetriever(db, router=router).search(
        query, lang=route.lang, k=s.final_topk
    )
    msgs = build_messages(query, res, lang=route.lang)
    llm_resp = llm.complete(msgs, temperature=0.2, max_tokens=800)

    rin = RenderInput(
        answer_raw=llm_resp.text,
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
            "model": llm_resp.model,
            "lat": llm_resp.latency_ms,
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
    db.commit()

    return ChatTurnOut(
        query_id=qid,
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
