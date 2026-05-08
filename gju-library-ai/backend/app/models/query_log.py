from sqlalchemy import ARRAY, Column, ForeignKey, Integer, String, TIMESTAMP, Text, func
from sqlalchemy.dialects.postgresql import JSONB

from app.db import Base


class QueryLog(Base):
    __tablename__ = "query_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    raw_query = Column(Text, nullable=False)
    lang = Column(String(8))
    extracted_filters = Column(JSONB)
    retrieved_passage_ids = Column(ARRAY(Integer))
    shown_database_slugs = Column(ARRAY(String))
    answer_text = Column(Text)
    model_name = Column(String(64))
    latency_ms = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
