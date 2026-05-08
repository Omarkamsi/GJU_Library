import datetime as dt

from jose import jwt

from app.config import get_settings

ALG = "HS256"


def mint_session(user_id: str) -> str:
    s = get_settings()
    now = dt.datetime.now(dt.timezone.utc)
    return jwt.encode(
        {
            "sub": user_id,
            "iat": int(now.timestamp()),
            "exp": int((now + dt.timedelta(hours=s.session_ttl_hours)).timestamp()),
        },
        s.session_secret,
        algorithm=ALG,
    )


def verify_session(token: str) -> str | None:
    s = get_settings()
    try:
        return jwt.decode(token, s.session_secret, algorithms=[ALG]).get("sub")
    except Exception:
        return None
