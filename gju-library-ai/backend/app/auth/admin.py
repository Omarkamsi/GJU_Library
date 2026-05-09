from fastapi import Depends, HTTPException

from app.auth.ids import hash_email
from app.config import get_settings
from app.deps import get_current_user_id


def _admin_user_ids() -> set[str]:
    s = get_settings()
    raw = (s.admin_emails or "").strip()
    if not raw:
        return set()
    return {hash_email(e, s.user_id_pepper) for e in raw.split(",") if e.strip()}


def require_admin(uid: str = Depends(get_current_user_id)) -> str:
    if uid not in _admin_user_ids():
        raise HTTPException(status_code=403, detail="admin only")
    return uid
