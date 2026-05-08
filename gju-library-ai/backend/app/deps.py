from typing import Iterator

from fastapi import Cookie, HTTPException
from sqlalchemy.orm import Session

from app.auth.jwt import verify_session
from app.config import get_settings
from app.db import SessionLocal


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
