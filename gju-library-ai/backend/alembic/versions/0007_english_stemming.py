"""Switch search_vector from simple to english dictionary for proper stemming

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-01

"""
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop and recreate the generated column with english stemming.
    # English dictionary handles student/students, borrow/borrowing, book/books correctly.
    # Arabic and German text passes through english stemming unchanged (words not recognised
    # as English are kept as-is), so this is safe for multilingual passages.
    op.execute("ALTER TABLE passages DROP COLUMN search_vector")
    op.execute("""
        ALTER TABLE passages
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', f_unaccent(coalesce(title,''))), 'A') ||
            setweight(to_tsvector('english', f_unaccent(coalesce(body,''))),  'B')
        ) STORED
    """)
    op.execute("CREATE INDEX ix_passages_search_vector ON passages USING gin (search_vector)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_passages_search_vector")
    op.execute("ALTER TABLE passages DROP COLUMN search_vector")
    op.execute("""
        ALTER TABLE passages
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('simple', f_unaccent(coalesce(title,''))), 'A') ||
            setweight(to_tsvector('simple', f_unaccent(coalesce(body,''))),  'B')
        ) STORED
    """)
    op.execute("CREATE INDEX ix_passages_search_vector ON passages USING gin (search_vector)")
