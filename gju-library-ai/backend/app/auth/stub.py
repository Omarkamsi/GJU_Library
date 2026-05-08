from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings

from .ids import email_domain, hash_email


def login_email(db: Session, email: str) -> str:
    s = get_settings()
    dom = email_domain(email)
    if dom not in s.allowed_domains_list:
        raise HTTPException(status_code=403, detail="email domain not allowed")
    uid = hash_email(email, s.user_id_pepper)
    db.execute(
        text(
            """
            INSERT INTO users (id, email_domain, role)
            VALUES (:id, :dom, 'user')
            ON CONFLICT (id) DO UPDATE SET last_seen_at = now()
            """
        ),
        {"id": uid, "dom": dom},
    )
    db.commit()
    return uid
