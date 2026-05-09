from typing import Iterator

from fastapi import Cookie, HTTPException
from sqlalchemy.orm import Session

from app.auth.jwt import verify_session
from app.config import get_settings
from app.db import SessionLocal
from app.llm.interface import LLMClient
from app.llm.ollama_client import OllamaClient


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_COOKIE_NAME = get_settings().session_cookie_name


def get_current_user_id(
    token: str | None = Cookie(default=None, alias=_COOKIE_NAME),
) -> str:
    if not token:
        raise HTTPException(status_code=401, detail="not authenticated")
    uid = verify_session(token)
    if not uid:
        raise HTTPException(status_code=401, detail="invalid or expired session")
    return uid


def get_llm() -> LLMClient:
    s = get_settings()
    if s.llm_provider == "ollama":
        return OllamaClient(host=s.ollama_host, model=s.ollama_model, keep_alive=s.ollama_keep_alive)
    raise RuntimeError(f"Unknown LLM_PROVIDER: {s.llm_provider}")
