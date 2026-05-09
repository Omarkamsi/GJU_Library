from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.chat.pipeline import run_chat, stream_chat
from app.deps import get_current_user_id, get_db, get_llm
from app.llm.interface import LLMClient

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatIn(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


@router.post("")
def chat(
    payload: ChatIn,
    uid: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
):
    out = run_chat(db, user_id=uid, query=payload.query, llm=llm)
    return {
        "query_id": out.query_id,
        "segments": out.segments,
        "answer_text": out.answer_text,
        "citations": out.citations,
        "suggested_databases": out.suggested_databases,
        "lang": out.lang,
        "latency_ms": out.latency_ms,
    }


@router.post("/stream")
def chat_stream(
    payload: ChatIn,
    uid: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
):
    return StreamingResponse(
        stream_chat(db, user_id=uid, query=payload.query, llm=llm),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
