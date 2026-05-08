# GJU Library AI — M0

Trilingual (EN / AR / DE) library-information chatbot grounded in the
FAQ, services, and subscription-database corpus, with click-tracking
and feedback logging for renewal-decision analytics.

## Quickstart

```bash
cp .env.example .env

docker compose up -d postgres ollama
docker compose exec ollama ollama pull qwen2.5:7b-instruct

docker compose up -d backend
docker compose exec backend alembic upgrade head
docker compose exec backend pip install -e ".[ml]"   # one-time, ~5 GB
docker compose exec backend python -m ingest.run

docker compose up -d frontend
```

Open <http://localhost:3000> and sign in with any `@gju.edu.jo` email.

## What's in M0

- 5-file source corpus: 2 FAQ xlsx + services / library-info / databases-links docx.
- 15-entry subscription-database registry (EN/AR/DE descriptions, subject tags).
- Hybrid retrieval: tsvector lexical + pgvector semantic → Reciprocal
  Rank Fusion (k=60) → bge-reranker-v2-m3 cross-encoder → top-5.
- BAAI/bge-m3 multilingual 1024-dim embeddings, HNSW index.
- Trilingual prompting; answers cite passages as `[P<id>]` and
  databases as `[DB:<slug>]` tokens — never raw URLs.
- `/go/<click_id>` proxy stamps `clicked_at` so the renewal study can
  compute shown-vs-clicked CTR per database.
- Per-answer and per-click feedback (`-1` / `0` / `1` + optional comment).
- Email-domain dev login (Entra ID OIDC arrives in a later milestone).
- **Frontend never uses `dangerouslySetInnerHTML`** — answers are
  rendered from typed segments (`text` / `passage_ref` / `link`).

## What's NOT in M0

- Entra ID SSO (the M0 stub is the seam where it'll plug in).
- Admin dashboard, CSV / PDF export.
- MARC catalog + DSpace ingestion.
- Retention purge cron, off-site backups.

See `docs/superpowers/specs/2026-04-28-gju-library-ai-design.md` for
the full design and `docs/superpowers/plans/2026-05-05-gju-library-ai-m0.md`
for the implementation plan.
