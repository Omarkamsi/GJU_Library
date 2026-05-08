from sqlalchemy import ARRAY, Boolean, Column, Integer, String, TIMESTAMP, Text, func

from app.db import Base


class SubscriptionDatabase(Base):
    __tablename__ = "subscription_databases"

    id = Column(Integer, primary_key=True)
    slug = Column(String(64), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    vendor = Column(String(200))
    url = Column(Text, nullable=False)
    content_types = Column(ARRAY(String))
    subjects = Column(ARRAY(String))
    languages = Column(ARRAY(String))
    access_method = Column(String(64))
    description_en = Column(Text)
    description_ar = Column(Text)
    description_de = Column(Text)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
