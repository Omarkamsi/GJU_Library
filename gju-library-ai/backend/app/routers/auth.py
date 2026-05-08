from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth.jwt import mint_session
from app.auth.stub import login_email
from app.config import get_settings
from app.deps import get_current_user_id, get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: EmailStr


@router.post("/login")
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    s = get_settings()
    uid = login_email(db, payload.email)
    response.set_cookie(
        s.session_cookie_name,
        mint_session(uid),
        max_age=s.session_ttl_hours * 3600,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )
    return {"ok": True}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(get_settings().session_cookie_name, path="/")
    return {"ok": True}


@router.get("/me")
def me(uid: str = Depends(get_current_user_id)):
    return {"user_id": uid}
