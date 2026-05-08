"""passages with tsvector, trgm, HNSW vector index

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-08

"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # unaccent() is STABLE; generated columns need IMMUTABLE. Wrap it.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text
          LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT AS
          $$ SELECT public.unaccent('public.unaccent', $1) $$;
        """
    )
    op.execute(
        """
        CREATE TABLE passages (
          id              SERIAL PRIMARY KEY,
          source          VARCHAR(64) NOT NULL,
          source_ref      VARCHAR(256) NOT NULL,
          lang            VARCHAR(8) NOT NULL,
          title           TEXT,
          body            TEXT NOT NULL,
          subjects        TEXT[],
          embedding       vector(1024),
          search_vector   tsvector
            GENERATED ALWAYS AS (
              setweight(to_tsvector('simple', f_unaccent(coalesce(title,''))), 'A') ||
              setweight(to_tsvector('simple', f_unaccent(coalesce(body,''))),  'B')
            ) STORED,
          created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute("CREATE INDEX ix_passages_search_vector ON passages USING gin (search_vector);")
    op.execute("CREATE INDEX ix_passages_subjects ON passages USING gin (subjects);")
    op.execute("CREATE INDEX ix_passages_title_trgm ON passages USING gin (title gin_trgm_ops);")
    op.execute(
        """
        CREATE INDEX ix_passages_embedding_hnsw ON passages
          USING hnsw (embedding vector_cosine_ops)
          WITH (m = 16, ef_construction = 64);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_passages_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_passages_title_trgm")
    op.execute("DROP INDEX IF EXISTS ix_passages_subjects")
    op.execute("DROP INDEX IF EXISTS ix_passages_search_vector")
    op.execute("DROP TABLE IF EXISTS passages")
    op.execute("DROP FUNCTION IF EXISTS f_unaccent(text)")
