from sqlalchemy import Column, String, TIMESTAMP, func

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)  # HMAC(email, pepper) hex
    email_domain = Column(String(128), nullable=False)
    department = Column(String(128))
    role = Column(String(16), nullable=False, default="user")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(TIMESTAMP(timezone=True))
