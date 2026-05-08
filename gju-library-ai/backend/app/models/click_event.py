from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, Text, func

from app.db import Base


class ClickEvent(Base):
    __tablename__ = "click_events"

    id = Column(String(32), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    query_id = Column(Integer, ForeignKey("query_log.id"))
    target_type = Column(String(32), nullable=False)
    target_ref = Column(String(256))
    target_url = Column(Text, nullable=False)
    rendered_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    clicked_at = Column(TIMESTAMP(timezone=True))
