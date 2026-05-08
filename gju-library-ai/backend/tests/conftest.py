import pytest
from sqlalchemy import text

from app.db import SessionLocal


@pytest.fixture
def db():
    s = SessionLocal()
    s.execute(text("BEGIN"))
    try:
        yield s
    finally:
        s.rollback()
        s.close()


@pytest.fixture
def seeded_db(db):
    db.execute(
        text(
            """
            INSERT INTO passages (source, source_ref, lang, title, body, subjects)
            VALUES
              ('faq', 'r1', 'en', 'Library hours',
               'The library opens at 8am and closes at 5pm.', ARRAY['general']),
              ('faq', 'r2', 'en', 'Remote access',
               'Use the VPN to access databases from home.', ARRAY['databases']),
              ('faq', 'r3', 'ar', 'ساعات الدوام',
               'المكتبة مفتوحة من الثامنة صباحًا حتى الخامسة مساءً.', ARRAY['general'])
            """
        )
    )
    db.flush()
    return db
