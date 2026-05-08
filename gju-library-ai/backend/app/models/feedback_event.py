from sqlalchemy import Column, ForeignKey, Integer, SmallInteger, String, TIMESTAMP, Text, func

from app.db import Base


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    scope = Column(String(16), nullable=False)
    query_id = Column(Integer, ForeignKey("query_log.id"))
    click_id = Column(String(32), ForeignKey("click_events.id"))
    rating = Column(SmallInteger)
    comment = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
