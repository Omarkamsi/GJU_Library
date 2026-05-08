from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Column, Integer, String, TIMESTAMP, Text, func
from sqlalchemy.dialects.postgresql import TSVECTOR

from app.db import Base


class Passage(Base):
    __tablename__ = "passages"

    id = Column(Integer, primary_key=True)
    source = Column(String(64), nullable=False)
    source_ref = Column(String(256), nullable=False)
    lang = Column(String(8), nullable=False)
    title = Column(Text)
    body = Column(Text, nullable=False)
    subjects = Column(ARRAY(String))
    embedding = Column(Vector(1024))
    search_vector = Column(TSVECTOR)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
