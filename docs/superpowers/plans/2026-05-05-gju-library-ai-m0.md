# GJU Library AI Assistant — M0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a trilingual (EN/AR/DE) library-information chatbot grounded in the GJU library's FAQs, services document, and the 15-database subscription registry, with click-tracked external links, query logging, and per-click feedback — runnable end-to-end on `docker compose up`.

**Architecture:** FastAPI backend + Next.js 14 frontend + PostgreSQL 16 with `pgvector`/`pg_trgm`. Hybrid retrieval (Postgres `tsvector` lexical + `pgvector` HNSW semantic) fused with Reciprocal Rank Fusion, then reranked with `bge-reranker-v2-m3`. Embeddings from `BAAI/bge-m3` (1024-dim, multilingual). LLM is local Ollama running `qwen2.5:7b-instruct`, abstracted behind an `LLMClient` interface so Azure OpenAI / vLLM swap in by config. External links are wrapped through a `/go/<click_id>` proxy; rows are pre-allocated at render and stamped on click. Auth is a dev-mode email-domain stub for M0; Entra ID OIDC slots in at the same `current_user` dependency in a later milestone.

**XSS posture:** the backend NEVER returns raw HTML. The chat response is a list of typed segments (`{type:"text"}`, `{type:"link", href, label, click_id}`) and the frontend renders them as React elements. No `dangerouslySetInnerHTML` anywhere.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 + Alembic, pgvector, sentence-transformers, FlagEmbedding, Ollama, Next.js 14 (App Router), Tailwind, Docker Compose.

**Source spec:** `docs/superpowers/specs/2026-04-28-gju-library-ai-design.md`

**Out of M0 (re-confirmed):** Entra ID SSO (stub used), admin dashboard + PDF export, MARC/DSpace ingestion, retention purge cron, off-site backups. All of these slot into the same schema/interfaces in later milestones.

---

## File Structure

```
gju-library-ai/
├── README.md
├── docker-compose.yml
├── .env.example
├── pyproject.toml
├── data/
│   ├── source/                    # raw inputs (committed for reproducibility)
│   │   ├── faq_general.xlsx       # was 1.xlsx
│   │   ├── faq_databases.xlsx     # was 2.xlsx
│   │   ├── services.docx          # was الخدمات.docx
│   │   ├── library_info.docx      # was المكتبة.docx
│   │   └── databases_links.docx   # was قواعد البيانات والروابط.docx
│   └── seeds/
│       └── subscription_databases.yaml   # hand-curated metadata
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI app factory
│   │   ├── config.py              # pydantic-settings
│   │   ├── deps.py                # DI: db session, current_user, llm
│   │   ├── db.py                  # SQLAlchemy engine/session
│   │   ├── models/                # one file per table
│   │   ├── auth/                  # ids, jwt, stub login
│   │   ├── routers/               # auth, chat, go, feedback
│   │   ├── retrieval/             # interface, lexical, semantic, fusion, reranker, databases, routing, hybrid
│   │   ├── llm/                   # interface, ollama_client, prompts
│   │   └── chat/                  # pipeline, render (segments)
│   ├── ingest/
│   │   ├── canonical.py           # Passage dataclass
│   │   ├── faq_loader.py          # xlsx → Passage[]
│   │   ├── docx_loader.py         # docx prose → Passage[]
│   │   ├── databases_loader.py    # YAML → records + Passage[]
│   │   ├── embed_index.py         # BGE-M3 → DB
│   │   └── run.py                 # entry point
│   ├── alembic/
│   ├── alembic.ini
│   └── tests/                     # unit/, integration/, fixtures/
└── frontend/
    ├── package.json, tsconfig.json, next.config.mjs
    ├── tailwind.config.ts, postcss.config.mjs
    ├── app/
    │   ├── layout.tsx, globals.css, page.tsx
    │   ├── login/page.tsx
    │   ├── chat/
    │   │   ├── page.tsx
    │   │   └── components/        # ChatMessage, ChatInput, FeedbackPrompt, AnswerSegments, TrackedLink
    │   └── api/[...path]/route.ts # backend proxy
    └── lib/api.ts, i18n.ts, types.ts
```

**Key boundaries:**
- `ingest/` cannot import `app/`. Ingestion runs as a separate process.
- `llm/interface.py` is the single swap-point between Ollama and Azure OpenAI.
- `auth/stub.py` is replaced wholesale by `auth/oidc.py` later — `deps.get_current_user_id` is the stable seam.
- Frontend never sees the LLM, the DB, or raw HTML; only `/api/*` JSON.

---

# Phase 0 — Repository scaffold

### Task 0.1: Create directory tree, `pyproject.toml`, env files

**Files:**
- Create: `gju-library-ai/pyproject.toml`
- Create: `gju-library-ai/.gitignore`
- Create: `gju-library-ai/.env.example`

- [ ] **Step 1: Create directory tree and copy source files**

```bash
mkdir -p gju-library-ai/{data/source,data/seeds,backend/app/{models,auth,routers,retrieval,llm,chat},backend/ingest,backend/alembic/versions,backend/tests/{unit,integration,fixtures},frontend/app/{login,chat/components,api/[...path]},frontend/lib,scripts,docs}
cd gju-library-ai
cp /root/1.xlsx data/source/faq_general.xlsx
cp /root/2.xlsx data/source/faq_databases.xlsx
cp /root/الخدمات.docx data/source/services.docx
cp /root/المكتبة.docx data/source/library_info.docx
cp "/root/قواعد البيانات والروابط.docx" data/source/databases_links.docx
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[project]
name = "gju-library-ai"
version = "0.0.1"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.32",
  "pydantic[email]>=2.9",
  "pydantic-settings>=2.6",
  "email-validator>=2.2",
  "sqlalchemy>=2.0.36",
  "alembic>=1.14",
  "psycopg[binary]>=3.2",
  "pgvector>=0.3.6",
  "python-jose[cryptography]>=3.3",
  "openpyxl>=3.1",
  "python-docx>=1.1",
  "pyyaml>=6.0",
  "httpx>=0.27",
  "FlagEmbedding>=1.3",
  "sentence-transformers>=3.3",
  "torch>=2.5",
  "ollama>=0.4",
  "tenacity>=9.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.3", "pytest-asyncio>=0.24", "ruff>=0.7"]

[tool.pytest.ini_options]
testpaths = ["backend/tests"]
asyncio_mode = "auto"
markers = ["slow: heavy tests requiring model downloads"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 3: Write `.gitignore`**

```gitignore
__pycache__/
*.py[cod]
.venv/
.env
.env.local
node_modules/
.next/
dist/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

- [ ] **Step 4: Write `.env.example`**

```dotenv
DATABASE_URL=postgresql+psycopg://gju:gju@postgres:5432/gju_library
APP_BASE_URL=http://localhost:8080
SESSION_SECRET=change-me-32-bytes-random
SESSION_COOKIE_NAME=gju_session
SESSION_TTL_HOURS=8

ALLOWED_EMAIL_DOMAINS=gju.edu.jo,example.com

LLM_PROVIDER=ollama
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=qwen2.5:7b-instruct

EMBEDDING_MODEL=BAAI/bge-m3
RERANKER_MODEL=BAAI/bge-reranker-v2-m3

RETRIEVE_TOPK_LEXICAL=50
RETRIEVE_TOPK_SEMANTIC=50
RRF_K=60
RERANK_TOPK=20
FINAL_TOPK=5
DB_SUGGESTIONS_MAX=3

USER_ID_PEPPER=change-me-32-bytes-random
```

- [ ] **Step 5: Commit**

```bash
git add gju-library-ai/
git commit -m "scaffold: project layout, pyproject, env example, source data"
```

---

### Task 0.2: Docker Compose with Postgres+pgvector and Ollama

**Files:**
- Create: `gju-library-ai/docker-compose.yml`
- Create: `gju-library-ai/backend/Dockerfile`
- Create: `gju-library-ai/frontend/Dockerfile`

- [ ] **Step 1: `docker-compose.yml`**

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: gju
      POSTGRES_PASSWORD: gju
      POSTGRES_DB: gju_library
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gju"]
      interval: 5s
      timeout: 3s
      retries: 20

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    ports: ["11434:11434"]

  backend:
    build: ./backend
    env_file: .env
    depends_on:
      postgres: { condition: service_healthy }
      ollama:   { condition: service_started }
    ports: ["8080:8080"]
    volumes:
      - ./backend:/app
      - ./data:/data:ro
    command: uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_BASE: http://backend:8080
    depends_on: [backend]
    ports: ["3000:3000"]
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    command: npm run dev

volumes:
  pg_data:
  ollama_data:
```

- [ ] **Step 2: `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .
COPY . /app/
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
```

- [ ] **Step 3: `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
EXPOSE 3000
```

- [ ] **Step 4: Boot postgres and pull the model**

```bash
cp .env.example .env
docker compose up -d postgres ollama
docker compose exec ollama ollama pull qwen2.5:7b-instruct
docker compose exec postgres psql -U gju -d gju_library -c \
  "CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE EXTENSION IF NOT EXISTS unaccent;"
```

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml backend/Dockerfile frontend/Dockerfile
git commit -m "infra: docker compose with pgvector + ollama"
```

---

### Task 0.3: FastAPI skeleton, settings, DB session

**Files:**
- Create: `backend/app/__init__.py` (empty)
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/db.py`
- Create: `backend/app/deps.py`

- [ ] **Step 1: `app/config.py`**

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    app_base_url: str = "http://localhost:8080"
    session_secret: str
    session_cookie_name: str = "gju_session"
    session_ttl_hours: int = 8
    allowed_email_domains: str = "gju.edu.jo"
    llm_provider: str = "ollama"
    ollama_host: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:7b-instruct"
    embedding_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    retrieve_topk_lexical: int = 50
    retrieve_topk_semantic: int = 50
    rrf_k: int = 60
    rerank_topk: int = 20
    final_topk: int = 5
    db_suggestions_max: int = 3
    user_id_pepper: str

    @property
    def allowed_domains_list(self) -> list[str]:
        return [d.strip().lower() for d in self.allowed_email_domains.split(",") if d.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
```

- [ ] **Step 2: `app/db.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase):
    pass
```

- [ ] **Step 3: `app/deps.py` (initial, expanded later)**

```python
from typing import Iterator
from sqlalchemy.orm import Session
from app.db import SessionLocal

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try: yield db
    finally: db.close()
```

- [ ] **Step 4: `app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(title="GJU Library AI", version="0.0.1")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}
    return app

app = create_app()
```

- [ ] **Step 5: Verify**

```bash
docker compose up -d backend
sleep 3
curl -s http://localhost:8080/healthz
```
Expected: `{"ok":true}`.

- [ ] **Step 6: Commit**

```bash
git add backend/app
git commit -m "backend: FastAPI skeleton with settings, db session, healthz"
```

---

### Task 0.4: Alembic init + extensions migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_extensions.py`

- [ ] **Step 1: Initialize alembic**

```bash
cd backend && alembic init alembic
```
Set `sqlalchemy.url` in `alembic.ini` to a placeholder; the real URL is loaded in `env.py`.

- [ ] **Step 2: Replace `alembic/env.py`**

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.config import get_settings
from app.db import Base
from app.models import (passage, subscription_database, user, session,
                        query_log, click_event, feedback_event)  # noqa: F401

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

- [ ] **Step 3: Write `alembic/versions/0001_extensions.py`**

```python
"""extensions"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
    op.execute("DROP EXTENSION IF EXISTS unaccent")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS vector")
```

- [ ] **Step 4: Run + commit**

```bash
docker compose exec backend alembic upgrade head
git add backend/alembic backend/alembic.ini
git commit -m "db: alembic init, extensions migration"
```

---

# Phase 1 — Data model and migrations

### Task 1.1: `subscription_databases` model + migration

**Files:**
- Create: `backend/app/models/__init__.py` (empty)
- Create: `backend/app/models/subscription_database.py`
- Create: `backend/alembic/versions/0002_subscription_databases.py`

- [ ] **Step 1: Model**

```python
# app/models/subscription_database.py
from sqlalchemy import Column, Integer, String, Text, ARRAY, Boolean, TIMESTAMP, func
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
```

- [ ] **Step 2: Migration `0002_subscription_databases.py` (`down_revision = "0001"`)**

```python
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "0002"; down_revision = "0001"; branch_labels = None; depends_on = None

def upgrade() -> None:
    op.create_table("subscription_databases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("vendor", sa.String(200)),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("content_types", postgresql.ARRAY(sa.String)),
        sa.Column("subjects", postgresql.ARRAY(sa.String)),
        sa.Column("languages", postgresql.ARRAY(sa.String)),
        sa.Column("access_method", sa.String(64)),
        sa.Column("description_en", sa.Text),
        sa.Column("description_ar", sa.Text),
        sa.Column("description_de", sa.Text),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sub_db_subjects", "subscription_databases", ["subjects"], postgresql_using="gin")

def downgrade() -> None:
    op.drop_index("ix_sub_db_subjects", "subscription_databases")
    op.drop_table("subscription_databases")
```

- [ ] **Step 3: Run + commit**

```bash
docker compose exec backend alembic upgrade head
git add backend/app/models backend/alembic/versions/0002_subscription_databases.py
git commit -m "db: subscription_databases table"
```

---

### Task 1.2: `passages` model + migration (tsvector + HNSW)

**Files:**
- Create: `backend/app/models/passage.py`
- Create: `backend/alembic/versions/0003_passages.py`

- [ ] **Step 1: Model**

```python
# app/models/passage.py
from sqlalchemy import Column, Integer, String, Text, ARRAY, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import TSVECTOR
from pgvector.sqlalchemy import Vector
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
```

- [ ] **Step 2: Migration `0003_passages.py` (`down_revision = "0002"`)**

```python
from alembic import op

revision = "0003"; down_revision = "0002"; branch_labels = None; depends_on = None

def upgrade() -> None:
    op.execute("""
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
          setweight(to_tsvector('simple', unaccent(coalesce(title,''))), 'A') ||
          setweight(to_tsvector('simple', unaccent(coalesce(body,''))),  'B')
        ) STORED,
      created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)
    op.execute("CREATE INDEX ix_passages_search_vector ON passages USING gin (search_vector);")
    op.execute("CREATE INDEX ix_passages_subjects ON passages USING gin (subjects);")
    op.execute("CREATE INDEX ix_passages_title_trgm ON passages USING gin (title gin_trgm_ops);")
    op.execute("""
      CREATE INDEX ix_passages_embedding_hnsw ON passages
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_passages_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_passages_title_trgm")
    op.execute("DROP INDEX IF EXISTS ix_passages_subjects")
    op.execute("DROP INDEX IF EXISTS ix_passages_search_vector")
    op.execute("DROP TABLE IF EXISTS passages")
```

- [ ] **Step 3: Run + verify**

```bash
docker compose exec backend alembic upgrade head
docker compose exec postgres psql -U gju -d gju_library -c "\d passages"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/passage.py backend/alembic/versions/0003_passages.py
git commit -m "db: passages with tsvector, trgm, HNSW vector index"
```

---

### Task 1.3: `users` and `sessions`

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/session.py`
- Create: `backend/alembic/versions/0004_users_sessions.py`

- [ ] **Step 1: Models**

```python
# app/models/user.py
from sqlalchemy import Column, String, TIMESTAMP, func
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String(64), primary_key=True)        # HMAC(email, pepper) hex
    email_domain = Column(String(128), nullable=False)
    department = Column(String(128))
    role = Column(String(16), nullable=False, default="user")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(TIMESTAMP(timezone=True))
```

```python
# app/models/session.py
from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, func
from app.db import Base

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
```

- [ ] **Step 2: Migration `0004` (`down_revision="0003"`)**

```python
import sqlalchemy as sa
from alembic import op

revision = "0004"; down_revision = "0003"; branch_labels = None; depends_on = None

def upgrade() -> None:
    op.create_table("users",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("email_domain", sa.String(128), nullable=False),
        sa.Column("department", sa.String(128)),
        sa.Column("role", sa.String(16), nullable=False, server_default="user"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_table("sessions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])

def downgrade() -> None:
    op.drop_index("ix_sessions_user_id", "sessions")
    op.drop_table("sessions"); op.drop_table("users")
```

- [ ] **Step 3: Run + commit**

```bash
docker compose exec backend alembic upgrade head
git add backend/app/models/user.py backend/app/models/session.py backend/alembic/versions/0004_users_sessions.py
git commit -m "db: users and sessions"
```

---

### Task 1.4: `query_log`, `click_events`, `feedback_events`

**Files:**
- Create: `backend/app/models/query_log.py`
- Create: `backend/app/models/click_event.py`
- Create: `backend/app/models/feedback_event.py`
- Create: `backend/alembic/versions/0005_logs.py`

- [ ] **Step 1: Models**

```python
# app/models/query_log.py
from sqlalchemy import Column, Integer, String, Text, ARRAY, TIMESTAMP, ForeignKey, func
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
```

```python
# app/models/click_event.py
from sqlalchemy import Column, String, Integer, Text, ForeignKey, TIMESTAMP, func
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
```

```python
# app/models/feedback_event.py
from sqlalchemy import Column, Integer, String, Text, SmallInteger, ForeignKey, TIMESTAMP, func
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
```

- [ ] **Step 2: Migration `0005_logs.py` (`down_revision="0004"`)**

```python
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "0005"; down_revision = "0004"; branch_labels = None; depends_on = None

def upgrade() -> None:
    op.create_table("query_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("raw_query", sa.Text, nullable=False),
        sa.Column("lang", sa.String(8)),
        sa.Column("extracted_filters", postgresql.JSONB),
        sa.Column("retrieved_passage_ids", postgresql.ARRAY(sa.Integer)),
        sa.Column("shown_database_slugs", postgresql.ARRAY(sa.String)),
        sa.Column("answer_text", sa.Text),
        sa.Column("model_name", sa.String(64)),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_query_log_user_created", "query_log", ["user_id", "created_at"])
    op.create_index("ix_query_log_created", "query_log", ["created_at"])

    op.create_table("click_events",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("query_id", sa.Integer, sa.ForeignKey("query_log.id")),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_ref", sa.String(256)),
        sa.Column("target_url", sa.Text, nullable=False),
        sa.Column("rendered_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("clicked_at", sa.TIMESTAMP(timezone=True)),
    )
    op.create_index("ix_click_target_clicked", "click_events", ["target_type", "target_ref", "clicked_at"])
    op.create_index("ix_click_query", "click_events", ["query_id"])

    op.create_table("feedback_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("scope", sa.String(16), nullable=False),
        sa.Column("query_id", sa.Integer, sa.ForeignKey("query_log.id")),
        sa.Column("click_id", sa.String(32), sa.ForeignKey("click_events.id")),
        sa.Column("rating", sa.SmallInteger),
        sa.Column("comment", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table("feedback_events")
    op.drop_index("ix_click_query", "click_events")
    op.drop_index("ix_click_target_clicked", "click_events")
    op.drop_table("click_events")
    op.drop_index("ix_query_log_created", "query_log")
    op.drop_index("ix_query_log_user_created", "query_log")
    op.drop_table("query_log")
```

- [ ] **Step 3: Run + commit**

```bash
docker compose exec backend alembic upgrade head
git add backend/app/models backend/alembic/versions/0005_logs.py
git commit -m "db: query_log, click_events, feedback_events"
```

---

# Phase 2 — Ingestion

### Task 2.1: Canonical `Passage` dataclass

**Files:**
- Create: `backend/ingest/__init__.py` (empty)
- Create: `backend/ingest/canonical.py`
- Create: `backend/tests/unit/test_canonical.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_canonical.py
from ingest.canonical import Passage

def test_passage_to_embedding_text_includes_title_and_body():
    p = Passage(source="faq", source_ref="row:3", lang="en",
                title="Library hours?", body="Open 8am–5pm.", subjects=["general"])
    text = p.embedding_text()
    assert "Library hours?" in text
    assert "Open 8am–5pm." in text
    assert "general" in text

def test_passage_embedding_text_omits_missing_title():
    p = Passage(source="services", source_ref="para:7", lang="ar",
                title=None, body="حجز قاعات الاجتماعات.", subjects=[])
    assert p.embedding_text().startswith("حجز")
```

- [ ] **Step 2: Run, expect FAIL**

```bash
docker compose exec backend pytest backend/tests/unit/test_canonical.py -v
```

- [ ] **Step 3: Implement**

```python
# ingest/canonical.py
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Passage:
    source: str
    source_ref: str
    lang: str
    body: str
    title: Optional[str] = None
    subjects: list[str] = field(default_factory=list)

    def embedding_text(self) -> str:
        parts: list[str] = []
        if self.title: parts.append(f"Title: {self.title}")
        if self.subjects: parts.append("Subjects: " + ", ".join(self.subjects))
        parts.append(self.body)
        return " | ".join(parts) if (self.title or self.subjects) else self.body
```

- [ ] **Step 4: PASS, commit**

```bash
docker compose exec backend pytest backend/tests/unit/test_canonical.py -v
git add backend/ingest/canonical.py backend/tests/unit/test_canonical.py
git commit -m "ingest: canonical Passage dataclass"
```

---

### Task 2.2: FAQ xlsx loader

**Files:**
- Create: `backend/ingest/faq_loader.py`
- Create: `backend/tests/fixtures/build_mini_faq.py`
- Create: `backend/tests/fixtures/mini_faq.xlsx`
- Create: `backend/tests/unit/test_faq_loader.py`

The two source FAQ files have different shapes (`Q (EN)`/`Q (AR)`/… vs. `Q`/`س`/…). Loader auto-detects via header aliases.

- [ ] **Step 1: Build fixture**

```python
# backend/tests/fixtures/build_mini_faq.py
import openpyxl
wb = openpyxl.Workbook(); ws = wb.active
ws.append(["Q (EN)", "Q (AR)", "A (EN)", "A (AR)", "Category"])
ws.append(["What are the library hours?", "ما هي ساعات الدوام؟",
           "Open 8am–5pm.", "مفتوحة من 8 صباحًا إلى 5 مساءً.", "General"])
ws.append([None, "أين تقع المكتبة؟", None, "داخل حرم الجامعة.", "General"])
wb.save("backend/tests/fixtures/mini_faq.xlsx")
```

```bash
docker compose exec backend python backend/tests/fixtures/build_mini_faq.py
```

- [ ] **Step 2: Failing test**

```python
# tests/unit/test_faq_loader.py
from ingest.faq_loader import load_faq_xlsx

def test_loads_one_passage_per_language_per_row():
    passages = load_faq_xlsx("backend/tests/fixtures/mini_faq.xlsx", source="faq_general")
    assert len(passages) == 3
    en = [p for p in passages if p.lang == "en"]
    ar = [p for p in passages if p.lang == "ar"]
    assert len(en) == 1 and len(ar) == 2
    assert "Library hours" in en[0].title
    assert "8am–5pm" in en[0].body
    assert "General" in en[0].subjects
```

- [ ] **Step 3: Implement**

```python
# ingest/faq_loader.py
from pathlib import Path
import openpyxl
from .canonical import Passage

HEADER_ALIASES = {
    "q (en)": "q_en", "q": "q_en",
    "q (ar)": "q_ar", "س": "q_ar",
    "q (de)": "q_de",
    "a (en)": "a_en", "a": "a_en",
    "a (ar)": "a_ar", "ج": "a_ar",
    "a (de)": "a_de",
    "category": "category",
}

def _norm_header(v) -> str | None:
    return HEADER_ALIASES.get(str(v).strip().lower()) if v is not None else None

def load_faq_xlsx(path: str | Path, source: str) -> list[Passage]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out: list[Passage] = []
    for sheet in wb.worksheets:
        rows = list(sheet.iter_rows(values_only=True))
        if not rows: continue
        header = [_norm_header(c) for c in rows[0]]
        for ri, row in enumerate(rows[1:], start=2):
            mapped = {h: row[i] for i, h in enumerate(header) if h is not None and i < len(row)}
            category = (mapped.get("category") or "")
            category = str(category).strip() or None
            for lang in ("en", "ar", "de"):
                q = mapped.get(f"q_{lang}"); a = mapped.get(f"a_{lang}")
                if not q or not a: continue
                out.append(Passage(
                    source=source,
                    source_ref=f"{sheet.title}:row{ri}:{lang}",
                    lang=lang,
                    title=str(q).strip(),
                    body=str(a).strip(),
                    subjects=[category] if category else [],
                ))
    return out
```

- [ ] **Step 4: PASS, commit**

```bash
docker compose exec backend pytest backend/tests/unit/test_faq_loader.py -v
git add backend/ingest/faq_loader.py backend/tests/fixtures backend/tests/unit/test_faq_loader.py
git commit -m "ingest: FAQ xlsx loader (multi-lang per row)"
```

---

### Task 2.3: Docx prose loader

**Files:**
- Create: `backend/ingest/docx_loader.py`
- Create: `backend/tests/fixtures/build_mini_services.py`
- Create: `backend/tests/fixtures/mini_services.docx`
- Create: `backend/tests/unit/test_docx_loader.py`

- [ ] **Step 1: Build fixture**

```python
# backend/tests/fixtures/build_mini_services.py
import docx
d = docx.Document()
d.add_paragraph("1. About the Library").bold = True
d.add_paragraph("The GJU Library serves students, faculty, and staff with print and digital resources.")
d.add_paragraph("2. الخدمات")
d.add_paragraph("تقدم المكتبة خدمات الإعارة والبحث في الفهرس.")
d.save("backend/tests/fixtures/mini_services.docx")
```

```bash
docker compose exec backend python backend/tests/fixtures/build_mini_services.py
```

- [ ] **Step 2: Failing test**

```python
# tests/unit/test_docx_loader.py
from ingest.docx_loader import load_docx_prose

def test_splits_by_heading_and_detects_lang():
    passages = load_docx_prose("backend/tests/fixtures/mini_services.docx", source="services")
    assert len(passages) >= 2
    en = [p for p in passages if "About" in (p.title or "")][0]
    ar = [p for p in passages if "الخدمات" in (p.title or "")][0]
    assert en.lang == "en" and ar.lang == "ar"
```

- [ ] **Step 3: Implement**

```python
# ingest/docx_loader.py
import re
from pathlib import Path
import docx
from .canonical import Passage

HEADING_RE = re.compile(r"^\s*\d+(\.\d+)*\.?\s+\S")

def _detect_lang(text: str) -> str:
    if not text: return "en"
    arabic = sum(1 for c in text if "؀" <= c <= "ۿ")
    latin  = sum(1 for c in text if c.isascii() and c.isalpha())
    de_markers = sum(text.lower().count(k) for k in (" und ", " der ", " die ", " das ", "ß", "ü", "ö", "ä"))
    if arabic > latin: return "ar"
    if de_markers >= 2: return "de"
    return "en"

def _is_heading(p) -> bool:
    txt = (p.text or "").strip()
    if not txt: return False
    if HEADING_RE.match(txt): return True
    runs_bold = all((r.bold or False) for r in p.runs if r.text.strip())
    return bool(runs_bold and len(txt) <= 80 and txt[-1] not in ".!?")

def load_docx_prose(path: str | Path, source: str) -> list[Passage]:
    doc = docx.Document(path)
    sections: list[tuple[str | None, list[str]]] = []
    title: str | None = None; body: list[str] = []
    for p in doc.paragraphs:
        txt = (p.text or "").strip()
        if not txt: continue
        if _is_heading(p):
            if title or body: sections.append((title, body))
            title, body = txt, []
        else:
            body.append(txt)
    if title or body: sections.append((title, body))

    out: list[Passage] = []
    for idx, (t, blines) in enumerate(sections):
        b = "\n".join(blines).strip()
        if not b and not t: continue
        if not b and t: b = t
        out.append(Passage(source=source, source_ref=f"section:{idx}",
                           lang=_detect_lang((t or "") + " " + b),
                           title=t, body=b, subjects=[]))
    return out
```

- [ ] **Step 4: PASS, commit**

```bash
docker compose exec backend pytest backend/tests/unit/test_docx_loader.py -v
git add backend/ingest/docx_loader.py backend/tests/fixtures/build_mini_services.py backend/tests/fixtures/mini_services.docx backend/tests/unit/test_docx_loader.py
git commit -m "ingest: docx prose loader (heading split + lang detection)"
```

---

### Task 2.4: Subscription-databases YAML seed

**Files:**
- Create: `data/seeds/subscription_databases.yaml`

15 entries, hand-curated from each database's public landing-page metadata. EN/AR/DE descriptions, subject areas, access method.

- [ ] **Step 1: Write the seed**

```yaml
# data/seeds/subscription_databases.yaml
- slug: sciencedirect
  name: ScienceDirect
  vendor: Elsevier
  url: https://www.sciencedirect.com
  content_types: [journals, ebooks]
  subjects: [Engineering, Computer Science, Health Sciences, Life Sciences, Physical Sciences, Social Sciences]
  languages: [en]
  access_method: ip-auth
  description_en: "Elsevier's full-text platform for peer-reviewed journals and ebooks across science, technology, and medicine."
  description_ar: "منصة إلسفير للوصول إلى الدوريات العلمية والكتب الإلكترونية في العلوم والتكنولوجيا والطب."
  description_de: "Elseviers Volltext-Plattform für begutachtete Fachzeitschriften und E-Books in Wissenschaft, Technik und Medizin."

- slug: wiley
  name: Wiley Online Library
  vendor: Wiley
  url: https://www.wileyonlinelibrary.com
  content_types: [journals, ebooks, reference]
  subjects: [Engineering, Business, Chemistry, Life Sciences, Medicine, Social Sciences, Humanities]
  languages: [en]
  access_method: ip-auth
  description_en: "Wiley's multidisciplinary collection of journals, ebooks, and reference works."
  description_ar: "مجموعة وايلي متعددة التخصصات من الدوريات والكتب والمراجع الإلكترونية."
  description_de: "Wileys interdisziplinäre Sammlung von Fachzeitschriften, E-Books und Nachschlagewerken."

- slug: statista
  name: Statista
  vendor: Statista
  url: https://www.statista.com
  content_types: [statistics, reports]
  subjects: [Business, Economics, Marketing, Industry, Society]
  languages: [en, de]
  access_method: ip-auth
  description_en: "Market and consumer statistics, industry reports, and forecasts."
  description_ar: "إحصاءات السوق والمستهلك وتقارير القطاعات والتوقعات."
  description_de: "Markt- und Verbraucherstatistiken, Branchenberichte und Prognosen."

- slug: ebrary
  name: Ebrary (ProQuest Ebook Central)
  vendor: ProQuest
  url: https://ebookcentral.proquest.com/lib/germanjordan-ebooks/home.action
  content_types: [ebooks]
  subjects: [Engineering, Business, Computer Science, Humanities, Social Sciences]
  languages: [en]
  access_method: ip-auth
  description_en: "Cross-publisher ebook collection covering academic disciplines."
  description_ar: "مجموعة كتب إلكترونية متعددة الناشرين تغطي التخصصات الأكاديمية."
  description_de: "Verlagsübergreifende E-Book-Sammlung über akademische Fachgebiete."

- slug: ieee
  name: IEEE Xplore (IEEE-IEL)
  vendor: IEEE
  url: https://ieeexplore.ieee.org/Xplore/home.jsp
  content_types: [journals, conference_proceedings, standards]
  subjects: [Electrical Engineering, Computer Science, Communications, Power Systems, Robotics, AI, Engineering]
  languages: [en]
  access_method: ip-auth
  description_en: "IEEE journals, conference proceedings, and standards in electrical engineering and computing."
  description_ar: "دوريات IEEE ومؤتمراتها والمعايير في الهندسة الكهربائية وعلوم الحاسوب."
  description_de: "IEEE-Fachzeitschriften, Konferenzbeiträge und Standards in Elektrotechnik und Informatik."

- slug: emerald
  name: Emerald Insight
  vendor: Emerald Publishing
  url: https://www.emerald.com
  content_types: [journals, ebooks, case_studies]
  subjects: [Business, Management, Education, Library Science, Engineering]
  languages: [en]
  access_method: ip-auth
  description_en: "Peer-reviewed research in management, business, education, and engineering."
  description_ar: "أبحاث محكّمة في الإدارة والأعمال والتربية والهندسة."
  description_de: "Begutachtete Forschung in Management, Wirtschaft, Bildung und Ingenieurwesen."

- slug: ebsco
  name: EBSCOhost
  vendor: EBSCO
  url: https://search.ebscohost.com/
  content_types: [journals, ebooks, magazines]
  subjects: [Business, Health, Education, General]
  languages: [en, ar]
  access_method: ip-auth
  description_en: "Multidisciplinary database aggregator with access via IP authentication."
  description_ar: "مُجمِّع قواعد بيانات متعدد التخصصات بالوصول عبر عنوان IP الجامعة."
  description_de: "Multidisziplinärer Datenbank-Aggregator mit IP-basiertem Zugang."

- slug: tandfonline
  name: Taylor & Francis Online
  vendor: Taylor & Francis
  url: https://www.tandfonline.com
  content_types: [journals]
  subjects: [Engineering, Social Sciences, Humanities, Education]
  languages: [en]
  access_method: ip-auth
  description_en: "Peer-reviewed journal articles across science, technology, and humanities."
  description_ar: "مقالات في دوريات محكّمة عبر العلوم والتكنولوجيا والعلوم الإنسانية."
  description_de: "Begutachtete Fachartikel über Wissenschaft, Technik und Geisteswissenschaften."

- slug: tandfebooks
  name: Taylor & Francis eBooks
  vendor: Taylor & Francis
  url: https://www.taylorfrancis.com/
  content_types: [ebooks]
  subjects: [Engineering, Humanities, Social Sciences]
  languages: [en]
  access_method: ip-auth
  description_en: "Taylor & Francis ebook collection across academic disciplines."
  description_ar: "مجموعة الكتب الإلكترونية لتايلور وفرانسيس عبر التخصصات الأكاديمية."
  description_de: "Taylor-&-Francis-E-Book-Sammlung über akademische Fachgebiete."

- slug: scopus
  name: Scopus
  vendor: Elsevier
  url: https://www.scopus.com/pages/home
  content_types: [abstracts_index, citations]
  subjects: [Engineering, Sciences, Health, Social Sciences]
  languages: [en]
  access_method: ip-auth
  description_en: "Abstract and citation database for peer-reviewed literature; bibliometrics and author profiles."
  description_ar: "قاعدة بيانات للملخصات والاستشهادات الببليومترية وملفات الباحثين."
  description_de: "Abstract- und Zitationsdatenbank; Bibliometrie und Autorenprofile."

- slug: springer
  name: SpringerLink
  vendor: Springer Nature
  url: https://link.springer.com/
  content_types: [journals, ebooks, reference]
  subjects: [Engineering, Computer Science, Mathematics, Medicine, Life Sciences, Business]
  languages: [en, de]
  access_method: ip-auth
  description_en: "Springer journals, books, and reference works."
  description_ar: "دوريات وكتب ومراجع إلكترونية من شبرنجر."
  description_de: "Springer-Fachzeitschriften, Bücher und Nachschlagewerke."

- slug: qistas
  name: Qistas
  vendor: Qistas
  url: https://research.qistas.com/ar
  content_types: [legal_database]
  subjects: [Law, Jurisprudence, Legislation]
  languages: [ar]
  access_method: login
  description_en: "Arabic legal research database covering Jordanian and regional legislation, case law, and jurisprudence."
  description_ar: "قاعدة بيانات قانونية عربية تغطي التشريعات الأردنية والإقليمية والاجتهادات القضائية."
  description_de: "Arabische juristische Forschungsdatenbank zu jordanischer und regionaler Gesetzgebung."

- slug: scival
  name: SciVal
  vendor: Elsevier
  url: https://www.scival.com/landing
  content_types: [research_analytics]
  subjects: [Research Performance, Bibliometrics]
  languages: [en]
  access_method: login
  description_en: "Research analytics tool for benchmarking institutions and analyzing research trends."
  description_ar: "أداة تحليلات بحثية للمقارنة المرجعية بين المؤسسات وتحليل اتجاهات البحث."
  description_de: "Forschungsanalytik-Tool für Institutionen-Benchmarking und Forschungstrend-Analyse."

- slug: europathek
  name: Europathek
  vendor: ciando
  url: https://www.europathek.de/campus/germanjordanian
  content_types: [ebooks]
  subjects: [German Studies, Engineering, Business, Humanities]
  languages: [de]
  access_method: ip-auth
  description_en: "German-language ebook platform; the GJU campus collection."
  description_ar: "منصة كتب إلكترونية باللغة الألمانية؛ مجموعة حرم الجامعة الألمانية الأردنية."
  description_de: "Deutschsprachige E-Book-Plattform; Campus-Sammlung der GJU."

- slug: deepknowledge
  name: Deep Knowledge
  vendor: Deep Knowledge
  url: https://www.gju.edu.jo/content/subscriptions-databases-list-6892
  content_types: [reference]
  subjects: [General]
  languages: [en]
  access_method: ip-auth
  description_en: "General reference database (placeholder; verify subject coverage with the library)."
  description_ar: "قاعدة بيانات مرجعية عامة (مؤقت؛ يُرجى التأكد من تغطية المواضيع مع المكتبة)."
  description_de: "Allgemeine Nachschlage-Datenbank (Platzhalter; Themenabdeckung mit der Bibliothek prüfen)."
```

- [ ] **Step 2: Commit**

```bash
git add data/seeds/subscription_databases.yaml
git commit -m "data: subscription databases seed (15 entries, EN/AR/DE)"
```

---

### Task 2.5: Subscription-databases loader

**Files:**
- Create: `backend/ingest/databases_loader.py`
- Create: `backend/tests/unit/test_databases_loader.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_databases_loader.py
from ingest.databases_loader import load_databases_yaml

def test_loads_yaml_into_records_and_passages():
    records, passages = load_databases_yaml("data/seeds/subscription_databases.yaml")
    assert len(records) == 15
    ieee = next(r for r in records if r["slug"] == "ieee")
    assert "Engineering" in ieee["subjects"]
    ieee_passages = [p for p in passages if p.source_ref == "db:ieee"]
    langs = {p.lang for p in ieee_passages}
    assert {"en", "ar", "de"} <= langs
```

- [ ] **Step 2: Implementation**

```python
# ingest/databases_loader.py
from pathlib import Path
from typing import Any
import yaml
from .canonical import Passage

REQUIRED = ["slug", "name", "url"]

def load_databases_yaml(path: str | Path) -> tuple[list[dict[str, Any]], list[Passage]]:
    with open(path, encoding="utf-8") as f:
        rows: list[dict[str, Any]] = yaml.safe_load(f)
    out_records: list[dict[str, Any]] = []
    out_passages: list[Passage] = []
    seen: set[str] = set()
    for r in rows:
        for k in REQUIRED:
            if not r.get(k): raise ValueError(f"Database row missing {k!r}: {r}")
        if r["slug"] in seen: raise ValueError(f"Duplicate slug: {r['slug']}")
        seen.add(r["slug"])
        out_records.append(r)
        for lang in ("en", "ar", "de"):
            desc = r.get(f"description_{lang}")
            if not desc: continue
            out_passages.append(Passage(
                source="databases", source_ref=f"db:{r['slug']}",
                lang=lang, title=r["name"], body=desc,
                subjects=r.get("subjects", []) or [],
            ))
    return out_records, out_passages
```

- [ ] **Step 3: PASS, commit**

```bash
docker compose exec backend pytest backend/tests/unit/test_databases_loader.py -v
git add backend/ingest/databases_loader.py backend/tests/unit/test_databases_loader.py
git commit -m "ingest: subscription databases YAML loader"
```

---

### Task 2.6: Embed + index passages, ingestion entry point

**Files:**
- Create: `backend/ingest/embed_index.py`
- Create: `backend/ingest/run.py`

- [ ] **Step 1: `embed_index.py`**

```python
# ingest/embed_index.py
from typing import Iterable
from FlagEmbedding import BGEM3FlagModel
from sqlalchemy import text
from sqlalchemy.orm import Session

_model: BGEM3FlagModel | None = None

def get_model(model_name: str = "BAAI/bge-m3") -> BGEM3FlagModel:
    global _model
    if _model is None:
        _model = BGEM3FlagModel(model_name, use_fp16=False)
    return _model

def embed_texts(texts: list[str], model_name: str = "BAAI/bge-m3") -> list[list[float]]:
    model = get_model(model_name)
    out = model.encode(texts, batch_size=16, max_length=2048)["dense_vecs"]
    return [v.tolist() for v in out]

def upsert_passages(db: Session, passages: Iterable, model_name: str = "BAAI/bge-m3") -> int:
    items = list(passages)
    if not items: return 0
    vectors = embed_texts([p.embedding_text() for p in items], model_name=model_name)
    n = 0
    for p, vec in zip(items, vectors):
        db.execute(text("""
          INSERT INTO passages (source, source_ref, lang, title, body, subjects, embedding)
          VALUES (:source, :source_ref, :lang, :title, :body, :subjects, :embedding)
          ON CONFLICT DO NOTHING
        """), {"source": p.source, "source_ref": p.source_ref, "lang": p.lang,
               "title": p.title, "body": p.body, "subjects": p.subjects, "embedding": vec})
        n += 1
    db.commit()
    return n
```

- [ ] **Step 2: `run.py`**

```python
# ingest/run.py
"""Run all loaders and embed into the DB.
Usage: docker compose exec backend python -m ingest.run
"""
from sqlalchemy import text
from app.db import SessionLocal
from app.config import get_settings
from .faq_loader import load_faq_xlsx
from .docx_loader import load_docx_prose
from .databases_loader import load_databases_yaml
from .embed_index import upsert_passages

DATA = "/data"

def upsert_databases(db, records: list[dict]) -> int:
    n = 0
    for r in records:
        db.execute(text("""
          INSERT INTO subscription_databases
            (slug, name, vendor, url, content_types, subjects, languages, access_method,
             description_en, description_ar, description_de, enabled)
          VALUES
            (:slug, :name, :vendor, :url, :content_types, :subjects, :languages, :access_method,
             :description_en, :description_ar, :description_de, true)
          ON CONFLICT (slug) DO UPDATE SET
            name=EXCLUDED.name, vendor=EXCLUDED.vendor, url=EXCLUDED.url,
            content_types=EXCLUDED.content_types, subjects=EXCLUDED.subjects,
            languages=EXCLUDED.languages, access_method=EXCLUDED.access_method,
            description_en=EXCLUDED.description_en,
            description_ar=EXCLUDED.description_ar,
            description_de=EXCLUDED.description_de
        """), {k: r.get(k) for k in (
            "slug","name","vendor","url","content_types","subjects","languages",
            "access_method","description_en","description_ar","description_de")})
        n += 1
    db.commit()
    return n

def main() -> None:
    s = get_settings()
    with SessionLocal() as db:
        all_passages = []
        all_passages += load_faq_xlsx(f"{DATA}/source/faq_general.xlsx",  source="faq_general")
        all_passages += load_faq_xlsx(f"{DATA}/source/faq_databases.xlsx", source="faq_databases")
        all_passages += load_docx_prose(f"{DATA}/source/services.docx",      source="services")
        all_passages += load_docx_prose(f"{DATA}/source/library_info.docx", source="library_info")
        records, db_passages = load_databases_yaml(f"{DATA}/seeds/subscription_databases.yaml")
        all_passages += db_passages

        db.execute(text("TRUNCATE passages RESTART IDENTITY"))
        db.commit()
        n_dbs = upsert_databases(db, records)
        n_pas = upsert_passages(db, all_passages, model_name=s.embedding_model)
        print(f"databases: {n_dbs} rows; passages: {n_pas} rows")

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run end-to-end**

```bash
docker compose exec backend python -m ingest.run
docker compose exec postgres psql -U gju -d gju_library -c "SELECT source, count(*) FROM passages GROUP BY source ORDER BY 1;"
```
Expected: rows for `faq_general`, `faq_databases`, `services`, `library_info`, `databases`.

- [ ] **Step 4: Commit**

```bash
git add backend/ingest/embed_index.py backend/ingest/run.py
git commit -m "ingest: BGE-M3 embed + DB upsert + run.py orchestrator"
```

---

# Phase 3 — Retrieval

### Task 3.1: Retriever interface

**Files:**
- Create: `backend/app/retrieval/__init__.py` (empty)
- Create: `backend/app/retrieval/interface.py`

- [ ] **Step 1: Interface**

```python
# app/retrieval/interface.py
from dataclasses import dataclass, field
from typing import Optional, Protocol

@dataclass
class PassageHit:
    id: int
    source: str
    source_ref: str
    lang: str
    title: Optional[str]
    body: str
    subjects: list[str]
    score: float

@dataclass
class DatabaseHit:
    slug: str
    name: str
    url: str
    subjects: list[str]
    description: str
    score: float

@dataclass
class RetrievalResult:
    passages: list[PassageHit]
    databases: list[DatabaseHit]
    debug: dict = field(default_factory=dict)

class Retriever(Protocol):
    def search(self, query: str, lang: str, k: int = 5) -> RetrievalResult: ...
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/retrieval/interface.py backend/app/retrieval/__init__.py
git commit -m "retrieval: interface + hit types"
```

---

### Task 3.2: Lexical retriever

**Files:**
- Create: `backend/app/retrieval/lexical.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/integration/test_lexical_retriever.py`

- [ ] **Step 1: Implementation**

```python
# app/retrieval/lexical.py
from sqlalchemy import text
from sqlalchemy.orm import Session
from .interface import PassageHit

LEXICAL_SQL = text("""
SELECT id, source, source_ref, lang, title, body, subjects,
       ts_rank_cd(search_vector, plainto_tsquery('simple', unaccent(:q))) AS score
FROM passages
WHERE search_vector @@ plainto_tsquery('simple', unaccent(:q))
ORDER BY score DESC
LIMIT :k
""")

def lexical_search(db: Session, query: str, k: int = 50) -> list[PassageHit]:
    rows = db.execute(LEXICAL_SQL, {"q": query, "k": k}).all()
    return [PassageHit(id=r.id, source=r.source, source_ref=r.source_ref,
                       lang=r.lang, title=r.title, body=r.body,
                       subjects=r.subjects or [], score=float(r.score)) for r in rows]
```

- [ ] **Step 2: `conftest.py`**

```python
# tests/conftest.py
import pytest
from sqlalchemy import text
from app.db import SessionLocal

@pytest.fixture
def db():
    s = SessionLocal()
    s.execute(text("BEGIN"))
    try: yield s
    finally:
        s.rollback(); s.close()

@pytest.fixture
def seeded_db(db):
    db.execute(text("""
        INSERT INTO passages (source, source_ref, lang, title, body, subjects)
        VALUES
          ('faq', 'r1', 'en', 'Library hours', 'The library opens at 8am and closes at 5pm.', ARRAY['general']),
          ('faq', 'r2', 'en', 'Remote access', 'Use the VPN to access databases from home.', ARRAY['databases']),
          ('faq', 'r3', 'ar', 'ساعات الدوام', 'المكتبة مفتوحة من الثامنة صباحًا حتى الخامسة مساءً.', ARRAY['general'])
    """))
    db.flush()
    return db
```

- [ ] **Step 3: Tests**

```python
# tests/integration/test_lexical_retriever.py
from app.retrieval.lexical import lexical_search

def test_finds_english_match(seeded_db):
    hits = lexical_search(seeded_db, "library hours", k=5)
    assert "Library hours" in [h.title for h in hits]

def test_finds_arabic_match(seeded_db):
    hits = lexical_search(seeded_db, "ساعات الدوام", k=5)
    assert any("ساعات" in (h.title or "") for h in hits)
```

- [ ] **Step 4: Run, PASS, commit**

```bash
docker compose exec backend pytest backend/tests/integration/test_lexical_retriever.py -v
git add backend/app/retrieval/lexical.py backend/tests/conftest.py backend/tests/integration/test_lexical_retriever.py
git commit -m "retrieval: tsvector lexical retriever"
```

---

### Task 3.3: Semantic retriever

**Files:**
- Create: `backend/app/retrieval/semantic.py`
- Create: `backend/tests/integration/test_semantic_retriever.py`

- [ ] **Step 1: Implementation**

```python
# app/retrieval/semantic.py
from sqlalchemy import text
from sqlalchemy.orm import Session
from ingest.embed_index import embed_texts
from .interface import PassageHit

SEMANTIC_SQL = text("""
SELECT id, source, source_ref, lang, title, body, subjects,
       1 - (embedding <=> CAST(:vec AS vector)) AS score
FROM passages
WHERE embedding IS NOT NULL
ORDER BY embedding <=> CAST(:vec AS vector) ASC
LIMIT :k
""")

def semantic_search(db: Session, query: str, k: int = 50,
                    model_name: str = "BAAI/bge-m3") -> list[PassageHit]:
    [vec] = embed_texts([query], model_name=model_name)
    rows = db.execute(SEMANTIC_SQL, {"vec": vec, "k": k}).all()
    return [PassageHit(id=r.id, source=r.source, source_ref=r.source_ref,
                       lang=r.lang, title=r.title, body=r.body,
                       subjects=r.subjects or [], score=float(r.score)) for r in rows]
```

- [ ] **Step 2: Test (requires `ingest.run` to have populated DB)**

```python
# tests/integration/test_semantic_retriever.py
import pytest
from app.retrieval.semantic import semantic_search

@pytest.mark.slow
def test_paraphrase_finds_hours(db):
    hits = semantic_search(db, "what time does the library close?", k=3)
    blob = " ".join((h.title or "") + " " + h.body for h in hits)
    assert "8" in blob and "5" in blob
```

- [ ] **Step 3: Run, PASS, commit**

```bash
docker compose exec backend pytest backend/tests/integration/test_semantic_retriever.py -v -m slow
git add backend/app/retrieval/semantic.py backend/tests/integration/test_semantic_retriever.py
git commit -m "retrieval: pgvector semantic retriever"
```

---

### Task 3.4: Reciprocal Rank Fusion

**Files:**
- Create: `backend/app/retrieval/fusion.py`
- Create: `backend/tests/unit/test_fusion.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_fusion.py
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.interface import PassageHit

def _h(i): return PassageHit(id=i, source="x", source_ref=f"r{i}", lang="en",
                              title=None, body="", subjects=[], score=0.0)

def test_rrf_prefers_consensus():
    a = [_h(1), _h(2), _h(3)]
    b = [_h(2), _h(1), _h(4)]
    fused = reciprocal_rank_fusion([a, b], k=60, top=4)
    assert fused[0].id == 2
    assert fused[1].id == 1
```

- [ ] **Step 2: Implementation**

```python
# app/retrieval/fusion.py
from collections import defaultdict
from .interface import PassageHit

def reciprocal_rank_fusion(rankings: list[list[PassageHit]], k: int = 60,
                           top: int = 20) -> list[PassageHit]:
    scores: dict[int, float] = defaultdict(float)
    by_id: dict[int, PassageHit] = {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, start=1):
            scores[hit.id] += 1.0 / (k + rank)
            by_id.setdefault(hit.id, hit)
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top]
    out = []
    for hid, sc in ordered:
        h = by_id[hid]
        out.append(PassageHit(id=h.id, source=h.source, source_ref=h.source_ref,
                              lang=h.lang, title=h.title, body=h.body,
                              subjects=h.subjects, score=sc))
    return out
```

- [ ] **Step 3: PASS, commit**

```bash
docker compose exec backend pytest backend/tests/unit/test_fusion.py -v
git add backend/app/retrieval/fusion.py backend/tests/unit/test_fusion.py
git commit -m "retrieval: RRF fusion"
```

---

### Task 3.5: Reranker

**Files:**
- Create: `backend/app/retrieval/reranker.py`

- [ ] **Step 1: Implementation**

```python
# app/retrieval/reranker.py
from FlagEmbedding import FlagReranker
from .interface import PassageHit

_reranker: FlagReranker | None = None

def get_reranker(model_name: str = "BAAI/bge-reranker-v2-m3") -> FlagReranker:
    global _reranker
    if _reranker is None:
        _reranker = FlagReranker(model_name, use_fp16=False)
    return _reranker

def rerank(query: str, hits: list[PassageHit], top: int = 5,
           model_name: str = "BAAI/bge-reranker-v2-m3") -> list[PassageHit]:
    if not hits: return []
    pairs = [(query, (h.title or "") + "\n" + h.body) for h in hits]
    scores = get_reranker(model_name).compute_score(pairs, normalize=True)
    if isinstance(scores, float): scores = [scores]
    scored = list(zip(hits, scores))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [PassageHit(id=h.id, source=h.source, source_ref=h.source_ref,
                       lang=h.lang, title=h.title, body=h.body,
                       subjects=h.subjects, score=float(s))
            for h, s in scored[:top]]
```

- [ ] **Step 2: Smoke test**

```bash
docker compose exec backend python -c "
from app.retrieval.reranker import rerank
from app.retrieval.interface import PassageHit
hits = [
  PassageHit(1,'faq','r1','en','Library hours','Open from 8am to 5pm.', [], 0.0),
  PassageHit(2,'faq','r2','en','Remote access','Use VPN.', [], 0.0)]
r = rerank('what time does the library close', hits, top=2)
print([(h.id, round(h.score,3)) for h in r])
"
```
Expected: id=1 ranked first.

- [ ] **Step 3: Commit**

```bash
git add backend/app/retrieval/reranker.py
git commit -m "retrieval: bge-reranker-v2-m3"
```

---

### Task 3.6: Subscription-database matcher

**Files:**
- Create: `backend/app/retrieval/databases.py`
- Create: `backend/tests/integration/test_databases_matcher.py`

- [ ] **Step 1: Implementation**

```python
# app/retrieval/databases.py
from sqlalchemy import text
from sqlalchemy.orm import Session
from .interface import DatabaseHit, PassageHit

SQL = text("SELECT slug, name, url, subjects, languages, "
           "description_en, description_ar, description_de "
           "FROM subscription_databases WHERE enabled = true")

def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)

def match_databases(db: Session, query_subjects: list[str], passages: list[PassageHit],
                    lang: str, max_results: int = 3) -> list[DatabaseHit]:
    rows = db.execute(SQL).mappings().all()
    union = {s.lower() for s in query_subjects}
    for p in passages:
        union |= {s.lower() for s in (p.subjects or [])}
    out: list[DatabaseHit] = []
    for r in rows:
        db_subjects = {s.lower() for s in (r["subjects"] or [])}
        score = _jaccard(union, db_subjects)
        if lang in (r["languages"] or []): score += 0.05
        if score <= 0: continue
        desc = r.get(f"description_{lang}") or r.get("description_en") or ""
        out.append(DatabaseHit(slug=r["slug"], name=r["name"], url=r["url"],
                               subjects=r["subjects"] or [], description=desc, score=score))
    out.sort(key=lambda d: d.score, reverse=True)
    return out[:max_results]
```

- [ ] **Step 2: Test**

```python
# tests/integration/test_databases_matcher.py
from app.retrieval.databases import match_databases

def test_engineering_query_recommends_engineering_db(db):
    hits = match_databases(db, query_subjects=["Engineering","Computer Science"],
                           passages=[], lang="en", max_results=3)
    slugs = [h.slug for h in hits]
    assert any(s in slugs for s in ("ieee","sciencedirect","scopus","springer"))
```

- [ ] **Step 3: PASS, commit**

```bash
docker compose exec backend pytest backend/tests/integration/test_databases_matcher.py -v
git add backend/app/retrieval/databases.py backend/tests/integration/test_databases_matcher.py
git commit -m "retrieval: subscription-database subject matcher"
```

---

### Task 3.7: Rule-based router

**Files:**
- Create: `backend/app/retrieval/routing.py`
- Create: `backend/tests/unit/test_routing.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_routing.py
from app.retrieval.routing import RuleBasedRouter

def test_detects_arabic():
    assert RuleBasedRouter().route("ما هي ساعات الدوام؟").lang == "ar"

def test_detects_german():
    assert RuleBasedRouter().route("Wo finde ich Bücher der Maschinenbau-Fakultät?").lang == "de"

def test_extracts_engineering_subject():
    r = RuleBasedRouter().route("I need IEEE papers on robotics")
    assert any(s in r.subjects for s in ("Engineering","Computer Science"))
```

- [ ] **Step 2: Implementation**

```python
# app/retrieval/routing.py
import re
from dataclasses import dataclass

SUBJECT_KEYWORDS: dict[str, list[str]] = {
    "Engineering": ["engineering","هندسة","robotics","circuit","ingenieur","maschinenbau","elektro"],
    "Computer Science": ["computer","software","ai","ml","informatik","حاسوب","برمجة","ذكاء اصطناعي"],
    "Business": ["business","management","marketing","finance","wirtschaft","إدارة","تسويق","أعمال"],
    "Law": ["law","legal","قانون","تشريع","recht"],
    "Medicine": ["medicine","health","طب","medizin"],
    "German Studies": ["german","deutsch","ألمانية"],
    "Statistics": ["statistics","statista","إحصاء","statistik"],
}

@dataclass
class Route:
    lang: str
    subjects: list[str]

class RuleBasedRouter:
    def route(self, q: str) -> Route:
        return Route(lang=self._lang(q), subjects=self._subjects(q))

    def _lang(self, q: str) -> str:
        if any("؀" <= c <= "ۿ" for c in q): return "ar"
        ql = q.lower()
        if re.search(r"\b(der|die|das|und|wo|wie|ist|für|mit|nicht)\b", ql) or any(c in q for c in "äöüß"):
            return "de"
        return "en"

    def _subjects(self, q: str) -> list[str]:
        ql = q.lower()
        return [subj for subj, kws in SUBJECT_KEYWORDS.items() if any(k in ql for k in kws)]
```

- [ ] **Step 3: PASS, commit**

```bash
docker compose exec backend pytest backend/tests/unit/test_routing.py -v
git add backend/app/retrieval/routing.py backend/tests/unit/test_routing.py
git commit -m "retrieval: rule-based language + subject router"
```

---

### Task 3.8: Hybrid retriever

**Files:**
- Create: `backend/app/retrieval/hybrid.py`
- Create: `backend/tests/integration/test_hybrid_retriever.py`

- [ ] **Step 1: Implementation**

```python
# app/retrieval/hybrid.py
from sqlalchemy.orm import Session
from app.config import get_settings
from .interface import RetrievalResult
from .lexical import lexical_search
from .semantic import semantic_search
from .fusion import reciprocal_rank_fusion
from .reranker import rerank
from .databases import match_databases
from .routing import RuleBasedRouter

class HybridRetriever:
    def __init__(self, db: Session, router=None):
        self.db = db
        self.router = router or RuleBasedRouter()
        self.s = get_settings()

    def search(self, query: str, lang: str | None = None, k: int | None = None) -> RetrievalResult:
        s = self.s
        route = self.router.route(query)
        lang = lang or route.lang
        k = k or s.final_topk

        lex = lexical_search(self.db, query, k=s.retrieve_topk_lexical)
        sem = semantic_search(self.db, query, k=s.retrieve_topk_semantic, model_name=s.embedding_model)
        fused = reciprocal_rank_fusion([lex, sem], k=s.rrf_k, top=s.rerank_topk)
        ranked = rerank(query, fused, top=k, model_name=s.reranker_model)
        databases = match_databases(self.db, query_subjects=route.subjects,
                                    passages=ranked, lang=lang,
                                    max_results=s.db_suggestions_max)
        return RetrievalResult(passages=ranked, databases=databases,
                               debug={"lang": lang, "subjects": route.subjects,
                                      "n_lex": len(lex), "n_sem": len(sem), "n_fused": len(fused)})
```

- [ ] **Step 2: Test**

```python
# tests/integration/test_hybrid_retriever.py
import pytest
from app.retrieval.hybrid import HybridRetriever

@pytest.mark.slow
def test_arabic_hours_query(db):
    res = HybridRetriever(db).search("ما هي ساعات الدوام؟")
    assert res.passages
    blob = " ".join((h.title or "") + " " + h.body for h in res.passages[:3])
    assert "ساعات" in blob or "8" in blob

@pytest.mark.slow
def test_engineering_recommends_dbs(db):
    res = HybridRetriever(db).search("I need recent IEEE papers on robotics")
    slugs = [d.slug for d in res.databases]
    assert any(s in slugs for s in ("ieee","sciencedirect","scopus"))
```

- [ ] **Step 3: PASS, commit**

```bash
docker compose exec backend pytest backend/tests/integration/test_hybrid_retriever.py -v -m slow
git add backend/app/retrieval/hybrid.py backend/tests/integration/test_hybrid_retriever.py
git commit -m "retrieval: hybrid orchestrator"
```

---

# Phase 4 — LLM client and prompts

### Task 4.1: `LLMClient` interface

**Files:**
- Create: `backend/app/llm/__init__.py` (empty)
- Create: `backend/app/llm/interface.py`

- [ ] **Step 1: Interface**

```python
# app/llm/interface.py
from dataclasses import dataclass
from typing import Protocol

@dataclass
class ChatMessage:
    role: str   # system | user | assistant
    content: str

@dataclass
class ChatResponse:
    text: str
    model: str
    latency_ms: int

class LLMClient(Protocol):
    def complete(self, messages: list[ChatMessage], temperature: float = 0.2,
                 max_tokens: int = 800) -> ChatResponse: ...
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/llm/interface.py backend/app/llm/__init__.py
git commit -m "llm: client interface"
```

---

### Task 4.2: Ollama client

**Files:**
- Create: `backend/app/llm/ollama_client.py`

- [ ] **Step 1: Implementation**

```python
# app/llm/ollama_client.py
import time
from ollama import Client
from .interface import LLMClient, ChatMessage, ChatResponse

class OllamaClient(LLMClient):
    def __init__(self, host: str, model: str):
        self._client = Client(host=host)
        self._model = model

    def complete(self, messages: list[ChatMessage], temperature: float = 0.2,
                 max_tokens: int = 800) -> ChatResponse:
        start = time.perf_counter()
        resp = self._client.chat(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            options={"temperature": temperature, "num_predict": max_tokens},
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        return ChatResponse(text=resp["message"]["content"], model=self._model, latency_ms=elapsed)
```

- [ ] **Step 2: Smoke test**

```bash
docker compose exec backend python -c "
from app.config import get_settings
from app.llm.ollama_client import OllamaClient
from app.llm.interface import ChatMessage
s = get_settings()
print(OllamaClient(s.ollama_host, s.ollama_model).complete(
    [ChatMessage('user','Reply in one short sentence: hello.')]).text)
"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/llm/ollama_client.py
git commit -m "llm: Ollama client"
```

---

### Task 4.3: Trilingual prompt templates

**Files:**
- Create: `backend/app/llm/prompts.py`
- Create: `backend/tests/unit/test_prompts.py`

The system prompt instructs the model to reply in the user's language and to cite passages as `[P<id>]` and databases as `[DB:<slug>]`. The renderer turns those tokens into structured segments — the model never returns raw URLs, and the frontend never receives raw HTML.

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_prompts.py
from app.llm.prompts import build_messages
from app.retrieval.interface import PassageHit, DatabaseHit, RetrievalResult

def _r():
    return RetrievalResult(
        passages=[PassageHit(1,"faq","r1","en","Library hours","Open 8am-5pm.", [], 0.9)],
        databases=[DatabaseHit("ieee","IEEE Xplore","https://ieeexplore.ieee.org",
                                ["Engineering"],"IEEE journals.",0.8)],
        debug={"lang":"en"})

def test_arabic_system_prompt_in_arabic():
    msgs = build_messages("ما هي ساعات الدوام؟", _r(), lang="ar")
    assert msgs[0].role == "system"
    assert "العربية" in msgs[0].content

def test_messages_contain_passages_and_db_tokens():
    msgs = build_messages("library hours?", _r(), lang="en")
    user_text = msgs[-1].content
    assert "[P1]" in user_text
    assert "[DB:ieee]" in user_text
    assert "https://" not in user_text  # raw URLs are NOT in the prompt
```

- [ ] **Step 2: Implementation**

```python
# app/llm/prompts.py
from .interface import ChatMessage
from app.retrieval.interface import RetrievalResult

SYSTEM = {
    "en": (
        "You are the GJU Library assistant. Answer the user's question using ONLY the "
        "PASSAGES provided. If a passage supports a fact, cite it inline as [P<id>]. "
        "If you recommend a subscription database, mention it using [DB:<slug>] tokens "
        "(NEVER write a raw URL — the system replaces tokens with tracked links). If "
        "the passages do not contain the answer, say so briefly and suggest contacting "
        "the library. Answer in English."
    ),
    "ar": (
        "أنت المساعد الذكي لمكتبة الجامعة الألمانية الأردنية. أجب عن سؤال المستخدم "
        "باستخدام المقاطع (PASSAGES) المُقدَّمة فقط. اذكر استشهادك بصيغة [P<id>] داخل "
        "النص. عند التوصية بقاعدة بيانات استخدم [DB:<slug>] ولا تكتب الروابط مباشرة "
        "(يستبدلها النظام بروابط متتبَّعة). إذا لم تتضمن المقاطع الإجابة، اذكر ذلك "
        "بإيجاز واقترح التواصل مع المكتبة. أجب باللغة العربية."
    ),
    "de": (
        "Du bist die KI-Assistenz der GJU-Bibliothek. Beantworte die Nutzerfrage "
        "AUSSCHLIESSLICH anhand der bereitgestellten PASSAGES. Belege jede Aussage "
        "inline mit [P<id>]. Wenn du eine Abonnement-Datenbank empfiehlst, verwende "
        "ausschließlich [DB:<slug>] – schreibe NIEMALS Roh-URLs (das System ersetzt "
        "die Tokens durch nachverfolgte Links). Wenn die Passages die Frage nicht "
        "beantworten, sage das knapp und empfiehl, die Bibliothek zu kontaktieren. "
        "Antworte auf Deutsch."
    ),
}

def build_messages(query: str, result: RetrievalResult, lang: str) -> list[ChatMessage]:
    sys_text = SYSTEM.get(lang, SYSTEM["en"])
    parts: list[str] = ["PASSAGES:"]
    for p in result.passages:
        head = (p.title or p.source_ref).strip()
        parts.append(f"[P{p.id}] ({p.lang}) {head}\n{p.body}")
    if result.databases:
        parts.append("\nDATABASES:")
        for d in result.databases:
            parts.append(f"[DB:{d.slug}] {d.name} — subjects: {', '.join(d.subjects)}\n{d.description}")
    parts.append(f"\nQUESTION:\n{query}")
    return [ChatMessage("system", sys_text), ChatMessage("user", "\n\n".join(parts))]
```

- [ ] **Step 3: PASS, commit**

```bash
docker compose exec backend pytest backend/tests/unit/test_prompts.py -v
git add backend/app/llm/prompts.py backend/tests/unit/test_prompts.py
git commit -m "llm: trilingual prompts with [P<id>] and [DB:slug] tokens (no raw URLs)"
```

---

# Phase 5 — Auth (M0 stub)

### Task 5.1: HMAC user-id helper

**Files:**
- Create: `backend/app/auth/__init__.py` (empty)
- Create: `backend/app/auth/ids.py`
- Create: `backend/tests/unit/test_ids.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_ids.py
from app.auth.ids import hash_email, email_domain

def test_hash_email_is_deterministic():
    assert hash_email("alice@gju.edu.jo","p1") == hash_email("alice@gju.edu.jo","p1")
    assert hash_email("alice@gju.edu.jo","p1") != hash_email("alice@gju.edu.jo","p2")

def test_email_domain_lowercased():
    assert email_domain("Bob@GJU.edu.JO") == "gju.edu.jo"
```

- [ ] **Step 2: Implementation**

```python
# app/auth/ids.py
import hashlib, hmac

def hash_email(email: str, pepper: str) -> str:
    return hmac.new(pepper.encode(), email.strip().lower().encode(), hashlib.sha256).hexdigest()

def email_domain(email: str) -> str:
    if "@" not in email: raise ValueError("not an email")
    return email.split("@", 1)[1].strip().lower()
```

- [ ] **Step 3: PASS, commit**

```bash
docker compose exec backend pytest backend/tests/unit/test_ids.py -v
git add backend/app/auth/ids.py backend/app/auth/__init__.py backend/tests/unit/test_ids.py
git commit -m "auth: HMAC user-id helpers"
```

---

### Task 5.2: Session JWT

**Files:**
- Create: `backend/app/auth/jwt.py`

- [ ] **Step 1: Implementation**

```python
# app/auth/jwt.py
import datetime as dt
from jose import jwt
from app.config import get_settings

ALG = "HS256"

def mint_session(user_id: str) -> str:
    s = get_settings()
    now = dt.datetime.now(dt.timezone.utc)
    return jwt.encode(
        {"sub": user_id, "iat": int(now.timestamp()),
         "exp": int((now + dt.timedelta(hours=s.session_ttl_hours)).timestamp())},
        s.session_secret, algorithm=ALG)

def verify_session(token: str) -> str | None:
    s = get_settings()
    try:
        return jwt.decode(token, s.session_secret, algorithms=[ALG]).get("sub")
    except Exception:
        return None
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/auth/jwt.py
git commit -m "auth: session JWT mint/verify"
```

---

### Task 5.3: Email-domain stub login + `current_user` dep

**Files:**
- Create: `backend/app/auth/stub.py`
- Create: `backend/app/routers/__init__.py` (empty)
- Create: `backend/app/routers/auth.py`
- Modify: `backend/app/deps.py`
- Modify: `backend/app/main.py`

> NOTE: This is a M0 dev stub. Replace with Entra ID OIDC before production rollout (spec §9). The `get_current_user_id` dependency is the seam.

- [ ] **Step 1: `app/auth/stub.py`**

```python
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import get_settings
from .ids import hash_email, email_domain

def login_email(db: Session, email: str) -> str:
    s = get_settings()
    dom = email_domain(email)
    if dom not in s.allowed_domains_list:
        raise HTTPException(status_code=403, detail="email domain not allowed")
    uid = hash_email(email, s.user_id_pepper)
    db.execute(text("""
        INSERT INTO users (id, email_domain, role)
        VALUES (:id, :dom, 'user')
        ON CONFLICT (id) DO UPDATE SET last_seen_at = now()
    """), {"id": uid, "dom": dom})
    db.commit()
    return uid
```

- [ ] **Step 2: `app/routers/auth.py`**

```python
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.config import get_settings
from app.deps import get_db, get_current_user_id
from app.auth.stub import login_email
from app.auth.jwt import mint_session

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginIn(BaseModel):
    email: EmailStr

@router.post("/login")
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    s = get_settings()
    uid = login_email(db, payload.email)
    response.set_cookie(
        s.session_cookie_name, mint_session(uid),
        max_age=s.session_ttl_hours * 3600,
        httponly=True, secure=False, samesite="lax", path="/")
    return {"ok": True}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(get_settings().session_cookie_name, path="/")
    return {"ok": True}

@router.get("/me")
def me(uid: str = Depends(get_current_user_id)):
    return {"user_id": uid}
```

- [ ] **Step 3: Replace `app/deps.py`**

```python
from typing import Iterator
from fastapi import Cookie, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.config import get_settings
from app.auth.jwt import verify_session

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_current_user_id(gju_session: str | None = Cookie(default=None, alias="gju_session")) -> str:
    if not gju_session:
        raise HTTPException(status_code=401, detail="not authenticated")
    uid = verify_session(gju_session)
    if not uid:
        raise HTTPException(status_code=401, detail="invalid session")
    return uid
```

(If `SESSION_COOKIE_NAME` is changed from `gju_session`, update the alias literal.)

- [ ] **Step 4: Wire in `main.py`**

```python
# app/main.py — append after CORS middleware:
from app.routers import auth as auth_router
app.include_router(auth_router.router)
```

- [ ] **Step 5: Verify**

```bash
docker compose restart backend
curl -s -c c.txt -H 'content-type: application/json' \
     -d '{"email":"test@gju.edu.jo"}' http://localhost:8080/auth/login
curl -s -b c.txt http://localhost:8080/auth/me
curl -s -i -H 'content-type: application/json' \
     -d '{"email":"x@evil.com"}' http://localhost:8080/auth/login | head -1
```
Expected: 200, 200 with `user_id`, then 403.

- [ ] **Step 6: Commit**

```bash
git add backend/app/auth backend/app/routers backend/app/deps.py backend/app/main.py
git commit -m "auth(stub): email-domain login + JWT cookie + current_user dep"
```

---

# Phase 6 — Chat pipeline and endpoint (no raw HTML)

### Task 6.1: Answer renderer — typed segments, no HTML

**Files:**
- Create: `backend/app/chat/__init__.py` (empty)
- Create: `backend/app/chat/render.py`
- Create: `backend/tests/unit/test_render.py`

The renderer parses the raw LLM text and returns:
- `segments`: a list of typed nodes the frontend can render as React elements (no HTML strings).
- `clicks`: pending `click_events` rows.

Segment shapes:
```python
{"type": "text", "value": str}
{"type": "passage_ref", "passage_id": int}
{"type": "link", "click_id": str, "label": str, "kind": "database"|"external", "ref": str|None}
```

The model is told never to emit raw URLs; if it does anyway (`http://...`), the renderer extracts and tracks them. Critically: **all data flowing into segments is plain text** — the frontend never `dangerouslySetInnerHTML`s anything.

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_render.py
from app.chat.render import render_answer, RenderInput

def _dbs(): return [("ieee","IEEE Xplore","https://ieeexplore.ieee.org")]

def test_db_token_becomes_link_segment_and_text_around_stays_text():
    out = render_answer(RenderInput(
        answer_raw="Try IEEE Xplore [DB:ieee] for engineering papers.",
        databases=_dbs(), passages=[], base_url="http://x"))
    types = [s["type"] for s in out.segments]
    assert types == ["text","link","text"]
    link = out.segments[1]
    assert link["kind"] == "database" and link["ref"] == "ieee" and link["label"] == "IEEE Xplore"
    assert any(c.target_type == "database" and c.target_ref == "ieee" for c in out.clicks)

def test_passage_ref_becomes_passage_ref_segment():
    out = render_answer(RenderInput(
        answer_raw="The library opens at 8am [P12].",
        databases=[], passages=[12], base_url="http://x"))
    assert out.segments[-1]["type"] == "passage_ref"
    assert out.segments[-1]["passage_id"] == 12

def test_unknown_db_slug_is_dropped_safely():
    out = render_answer(RenderInput(
        answer_raw="See [DB:bogus] for that.",
        databases=_dbs(), passages=[], base_url="http://x"))
    # token removed; no link, no click, no exception
    assert all(s["type"] != "link" for s in out.segments)
    assert out.clicks == []

def test_raw_url_in_model_output_gets_tracked_and_replaced():
    out = render_answer(RenderInput(
        answer_raw="See https://www.gju.edu.jo/library for more.",
        databases=[], passages=[], base_url="http://x"))
    link = next(s for s in out.segments if s["type"] == "link")
    assert link["kind"] == "external"
    assert any(c.target_type == "external" for c in out.clicks)

def test_segment_text_is_never_html():
    out = render_answer(RenderInput(
        answer_raw="<script>alert(1)</script> ok [DB:ieee]",
        databases=_dbs(), passages=[], base_url="http://x"))
    # the angle-bracketed text passes through as plain text — frontend escapes it
    assert any(s["type"] == "text" and "<script>" in s["value"] for s in out.segments)
```

- [ ] **Step 2: Implementation**

```python
# app/chat/render.py
import re, secrets
from dataclasses import dataclass
from typing import Any

CLICK_ID_LEN = 12

@dataclass
class PendingClick:
    id: str
    target_type: str   # database | external | passage
    target_ref: str | None
    target_url: str

@dataclass
class RenderInput:
    answer_raw: str
    databases: list[tuple[str, str, str]]   # (slug, name, url)
    passages: list[int]                     # known passage ids the model may cite
    base_url: str

@dataclass
class RenderOutput:
    segments: list[dict[str, Any]]
    answer_text: str                        # raw for query_log
    clicks: list[PendingClick]

# Order matters: parse [DB:...] first (it can contain colons), then [P<id>], then bare URLs
DB_TOKEN_RE = re.compile(r"\[DB:([a-z0-9_-]+)\]")
P_TOKEN_RE  = re.compile(r"\[P(\d+)\]")
URL_RE      = re.compile(r"https?://[^\s)\]]+")

def _new_click_id() -> str:
    return "c_" + secrets.token_urlsafe(9)[:CLICK_ID_LEN]

def _push_text(segments: list[dict], buf: str) -> None:
    if buf:
        if segments and segments[-1]["type"] == "text":
            segments[-1]["value"] += buf
        else:
            segments.append({"type": "text", "value": buf})

def render_answer(inp: RenderInput) -> RenderOutput:
    db_by_slug = {slug: (name, url) for slug, name, url in inp.databases}
    known_passages = set(inp.passages)
    segments: list[dict[str, Any]] = []
    clicks: list[PendingClick] = []

    # Single pass scanning earliest match among the three regexes
    s = inp.answer_raw
    pos = 0
    while pos < len(s):
        m_db = DB_TOKEN_RE.search(s, pos)
        m_p  = P_TOKEN_RE.search(s, pos)
        m_u  = URL_RE.search(s, pos)
        candidates = [m for m in (m_db, m_p, m_u) if m]
        if not candidates:
            _push_text(segments, s[pos:])
            break
        m = min(candidates, key=lambda x: x.start())
        if m.start() > pos:
            _push_text(segments, s[pos:m.start()])

        if m is m_db:
            slug = m.group(1)
            if slug in db_by_slug:
                name, url = db_by_slug[slug]
                cid = _new_click_id()
                clicks.append(PendingClick(cid, "database", slug, url))
                segments.append({"type":"link","click_id":cid,"label":name,"kind":"database","ref":slug})
            # unknown slug → silently drop
        elif m is m_p:
            pid = int(m.group(1))
            if pid in known_passages:
                segments.append({"type":"passage_ref","passage_id":pid})
            else:
                _push_text(segments, m.group(0))   # keep unknown as plain text
        else:  # raw URL
            url = m.group(0)
            cid = _new_click_id()
            clicks.append(PendingClick(cid, "external", None, url))
            segments.append({"type":"link","click_id":cid,"label":url,"kind":"external","ref":None})
        pos = m.end()

    return RenderOutput(segments=segments, answer_text=inp.answer_raw, clicks=clicks)
```

- [ ] **Step 3: PASS, commit**

```bash
docker compose exec backend pytest backend/tests/unit/test_render.py -v
git add backend/app/chat backend/tests/unit/test_render.py
git commit -m "chat: typed-segment renderer (no HTML, no XSS surface)"
```

---

### Task 6.2: Chat pipeline

**Files:**
- Create: `backend/app/chat/pipeline.py`

- [ ] **Step 1: Implementation**

```python
# app/chat/pipeline.py
import time
from dataclasses import dataclass
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.routing import RuleBasedRouter
from app.llm.interface import LLMClient
from app.llm.prompts import build_messages
from .render import render_answer, RenderInput, PendingClick

@dataclass
class ChatTurnOut:
    query_id: int
    segments: list[dict[str, Any]]
    answer_text: str
    citations: list[dict]
    suggested_databases: list[dict]
    clicks: list[PendingClick]
    lang: str
    latency_ms: int

def run_chat(db: Session, user_id: str, query: str, llm: LLMClient) -> ChatTurnOut:
    s = get_settings()
    t0 = time.perf_counter()

    router = RuleBasedRouter()
    route = router.route(query)
    res = HybridRetriever(db, router=router).search(query, lang=route.lang, k=s.final_topk)

    msgs = build_messages(query, res, lang=route.lang)
    llm_resp = llm.complete(msgs, temperature=0.2, max_tokens=600)

    rin = RenderInput(
        answer_raw=llm_resp.text,
        databases=[(d.slug, d.name, d.url) for d in res.databases],
        passages=[p.id for p in res.passages],
        base_url=s.app_base_url,
    )
    rout = render_answer(rin)

    qid = db.execute(text("""
        INSERT INTO query_log
          (user_id, raw_query, lang, extracted_filters, retrieved_passage_ids,
           shown_database_slugs, answer_text, model_name, latency_ms)
        VALUES (:uid,:q,:lang,:filters,:pids,:dbs,:atext,:model,:lat)
        RETURNING id
    """), {"uid": user_id, "q": query, "lang": route.lang,
           "filters": {"subjects": route.subjects},
           "pids": [p.id for p in res.passages],
           "dbs":  [d.slug for d in res.databases],
           "atext": rout.answer_text, "model": llm_resp.model, "lat": llm_resp.latency_ms}).scalar_one()

    for c in rout.clicks:
        db.execute(text("""
            INSERT INTO click_events (id, user_id, query_id, target_type, target_ref, target_url)
            VALUES (:id, :uid, :qid, :tt, :tr, :url)
        """), {"id": c.id, "uid": user_id, "qid": qid,
               "tt": c.target_type, "tr": c.target_ref, "url": c.target_url})
    db.commit()

    return ChatTurnOut(
        query_id=qid, segments=rout.segments, answer_text=rout.answer_text,
        citations=[{"id": p.id, "title": p.title, "source": p.source} for p in res.passages],
        suggested_databases=[{"slug": d.slug, "name": d.name} for d in res.databases],
        clicks=rout.clicks, lang=route.lang,
        latency_ms=int((time.perf_counter() - t0) * 1000),
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/chat/pipeline.py
git commit -m "chat: pipeline (retrieve -> LLM -> render -> log)"
```

---

### Task 6.3: `/chat` router + LLM dependency

**Files:**
- Modify: `backend/app/deps.py`
- Create: `backend/app/routers/chat.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Append `get_llm` to `app/deps.py`**

```python
# append to app/deps.py
from app.llm.interface import LLMClient
from app.llm.ollama_client import OllamaClient

def get_llm() -> LLMClient:
    s = get_settings()
    if s.llm_provider == "ollama":
        return OllamaClient(host=s.ollama_host, model=s.ollama_model)
    raise RuntimeError(f"Unknown LLM_PROVIDER: {s.llm_provider}")
```

- [ ] **Step 2: `app/routers/chat.py`**

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user_id, get_llm
from app.llm.interface import LLMClient
from app.chat.pipeline import run_chat

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatIn(BaseModel):
    query: str = Field(min_length=1, max_length=2000)

@router.post("")
def chat(payload: ChatIn,
         uid: str = Depends(get_current_user_id),
         db: Session = Depends(get_db),
         llm: LLMClient = Depends(get_llm)):
    out = run_chat(db, user_id=uid, query=payload.query, llm=llm)
    return {
        "query_id": out.query_id,
        "segments": out.segments,             # structured, no HTML
        "answer_text": out.answer_text,
        "citations": out.citations,
        "suggested_databases": out.suggested_databases,
        "lang": out.lang,
        "latency_ms": out.latency_ms,
    }
```

- [ ] **Step 3: Wire**

```python
# app/main.py — append:
from app.routers import chat as chat_router
app.include_router(chat_router.router)
```

- [ ] **Step 4: Smoke**

```bash
docker compose restart backend
curl -s -c c.txt -H 'content-type: application/json' \
     -d '{"email":"test@gju.edu.jo"}' http://localhost:8080/auth/login >/dev/null
curl -s -b c.txt -H 'content-type: application/json' \
     -d '{"query":"What are the library hours?"}' http://localhost:8080/chat | jq .
```
Expected: JSON with `segments[]`, `citations`, `latency_ms`. No `answer_html` field anywhere.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/chat.py backend/app/deps.py backend/app/main.py
git commit -m "chat: /chat endpoint returning typed segments"
```

---

# Phase 7 — Click tracking and feedback

### Task 7.1: `/go/<click_id>` redirect

**Files:**
- Create: `backend/app/routers/go.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/integration/test_go_endpoint.py`

- [ ] **Step 1: Implementation**

```python
# app/routers/go.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user_id

router = APIRouter(tags=["click"])

@router.get("/go/{click_id}")
def go(click_id: str,
       uid: str = Depends(get_current_user_id),
       db: Session = Depends(get_db)):
    row = db.execute(text("""
        UPDATE click_events
           SET clicked_at = COALESCE(clicked_at, now())
         WHERE id = :id AND user_id = :uid
         RETURNING target_url
    """), {"id": click_id, "uid": uid}).first()
    db.commit()
    if not row: raise HTTPException(status_code=404, detail="not found")
    return RedirectResponse(url=row.target_url, status_code=302)
```

- [ ] **Step 2: Wire**

```python
# app/main.py — append:
from app.routers import go as go_router
app.include_router(go_router.router)
```

- [ ] **Step 3: Integration test**

```python
# tests/integration/test_go_endpoint.py
from fastapi.testclient import TestClient
from app.main import app

def test_login_chat_click_flow():
    client = TestClient(app, follow_redirects=False)
    assert client.post("/auth/login", json={"email":"test@gju.edu.jo"}).status_code == 200
    r = client.post("/chat", json={"query":"I need IEEE engineering papers"})
    assert r.status_code == 200
    body = r.json()
    link = next((s for s in body["segments"] if s["type"]=="link"), None)
    assert link is not None
    cid = link["click_id"]
    r = client.get(f"/go/{cid}")
    assert r.status_code == 302
    assert r.headers["location"].startswith("http")
```

- [ ] **Step 4: Run, PASS, commit**

```bash
docker compose restart backend
docker compose exec backend pytest backend/tests/integration/test_go_endpoint.py -v
git add backend/app/routers/go.py backend/app/main.py backend/tests/integration/test_go_endpoint.py
git commit -m "click: /go/<id> tracked redirect"
```

---

### Task 7.2: `/feedback`

**Files:**
- Create: `backend/app/routers/feedback.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/integration/test_feedback_endpoint.py`

- [ ] **Step 1: Implementation**

```python
# app/routers/feedback.py
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user_id

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackIn(BaseModel):
    scope: Literal["answer", "click"]
    query_id: Optional[int] = None
    click_id: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=-1, le=1)
    comment: Optional[str] = Field(default=None, max_length=2000)

@router.post("")
def feedback(payload: FeedbackIn,
             uid: str = Depends(get_current_user_id),
             db: Session = Depends(get_db)):
    if payload.scope == "answer" and payload.query_id is None:
        raise HTTPException(400, "query_id required for answer scope")
    if payload.scope == "click" and payload.click_id is None:
        raise HTTPException(400, "click_id required for click scope")
    db.execute(text("""
        INSERT INTO feedback_events (user_id, scope, query_id, click_id, rating, comment)
        VALUES (:uid, :scope, :qid, :cid, :rating, :comment)
    """), {"uid": uid, "scope": payload.scope, "qid": payload.query_id,
           "cid": payload.click_id, "rating": payload.rating, "comment": payload.comment})
    db.commit()
    return {"ok": True}
```

- [ ] **Step 2: Wire**

```python
# app/main.py — append:
from app.routers import feedback as fb_router
app.include_router(fb_router.router)
```

- [ ] **Step 3: Tests**

```python
# tests/integration/test_feedback_endpoint.py
from fastapi.testclient import TestClient
from app.main import app

def test_answer_feedback():
    c = TestClient(app)
    c.post("/auth/login", json={"email":"test@gju.edu.jo"})
    qid = c.post("/chat", json={"query":"library hours?"}).json()["query_id"]
    assert c.post("/feedback", json={"scope":"answer","query_id":qid,"rating":1}).status_code == 200

def test_feedback_requires_ids():
    c = TestClient(app)
    c.post("/auth/login", json={"email":"test@gju.edu.jo"})
    assert c.post("/feedback", json={"scope":"answer","rating":1}).status_code == 400
```

- [ ] **Step 4: Run, commit**

```bash
docker compose restart backend
docker compose exec backend pytest backend/tests/integration/test_feedback_endpoint.py -v
git add backend/app/routers/feedback.py backend/app/main.py backend/tests/integration/test_feedback_endpoint.py
git commit -m "feedback: /feedback endpoint"
```

---

# Phase 8 — Frontend

### Task 8.1: Frontend scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.mjs`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.mjs`
- Create: `frontend/app/globals.css`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/page.tsx`

- [ ] **Step 1: `package.json`**

```json
{
  "name": "gju-library-ai-frontend",
  "version": "0.0.1",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start -p 3000"
  },
  "dependencies": {
    "next": "14.2.15",
    "react": "18.3.1",
    "react-dom": "18.3.1"
  },
  "devDependencies": {
    "@types/node": "20.16.10",
    "@types/react": "18.3.11",
    "@types/react-dom": "18.3.0",
    "autoprefixer": "10.4.20",
    "postcss": "8.4.47",
    "tailwindcss": "3.4.13",
    "typescript": "5.6.2"
  }
}
```

- [ ] **Step 2: `tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "ES2022"],
    "module": "esnext",
    "moduleResolution": "bundler",
    "jsx": "preserve",
    "strict": true,
    "noEmit": true,
    "skipLibCheck": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 3: `next.config.mjs`**

```js
/** @type {import('next').NextConfig} */
export default { reactStrictMode: true };
```

- [ ] **Step 4: `tailwind.config.ts` and `postcss.config.mjs`**

```ts
// frontend/tailwind.config.ts
import type { Config } from "tailwindcss";
const config: Config = { content: ["./app/**/*.{ts,tsx}"], theme: { extend: {} }, plugins: [] };
export default config;
```

```js
// frontend/postcss.config.mjs
export default { plugins: { tailwindcss: {}, autoprefixer: {} } };
```

- [ ] **Step 5: Globals, layout, root**

```css
/* frontend/app/globals.css */
@tailwind base; @tailwind components; @tailwind utilities;
:root { --bg: #fafaf9; --fg: #1f2937; }
html, body { background: var(--bg); color: var(--fg); }
[dir="rtl"] { font-family: system-ui, "Noto Naskh Arabic", serif; }
```

```tsx
// frontend/app/layout.tsx
import "./globals.css";
import type { Metadata } from "next";
export const metadata: Metadata = { title: "GJU Library AI" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body className="min-h-screen">{children}</body></html>;
}
```

```tsx
// frontend/app/page.tsx
import { redirect } from "next/navigation";
export default function Home() { redirect("/chat"); }
```

- [ ] **Step 6: Boot**

```bash
docker compose up -d frontend
sleep 5
curl -s http://localhost:3000/ | head -5
```

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "frontend: Next.js 14 scaffold + Tailwind"
```

---

### Task 8.2: Types, api proxy, fetch wrapper, i18n

**Files:**
- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/api.ts`
- Create: `frontend/lib/i18n.ts`
- Create: `frontend/app/api/[...path]/route.ts`

- [ ] **Step 1: `lib/types.ts`**

```ts
// frontend/lib/types.ts
export type Lang = "en" | "ar" | "de";
export type Segment =
  | { type: "text"; value: string }
  | { type: "passage_ref"; passage_id: number }
  | { type: "link"; click_id: string; label: string; kind: "database" | "external"; ref: string | null };

export type ChatResponse = {
  query_id: number;
  segments: Segment[];
  answer_text: string;
  citations: { id: number; title: string | null; source: string }[];
  suggested_databases: { slug: string; name: string }[];
  lang: Lang;
  latency_ms: number;
};
```

- [ ] **Step 2: `lib/api.ts`**

```ts
// frontend/lib/api.ts
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init, credentials: "include",
    headers: { "content-type":"application/json", ...(init?.headers||{}) },
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}
```

- [ ] **Step 3: `lib/i18n.ts`**

```ts
// frontend/lib/i18n.ts
import type { Lang } from "./types";
export const dirOf = (l: Lang): "ltr" | "rtl" => (l === "ar" ? "rtl" : "ltr");

export const T: Record<Lang, Record<string, string>> = {
  en: { send: "Send", helpful: "Was this helpful?", yes: "Yes", no: "No", skip: "Skip",
        login: "Sign in", emailLabel: "GJU email", askPlaceholder: "What are the library hours?" },
  ar: { send: "إرسال", helpful: "هل كان هذا مفيدًا؟", yes: "نعم", no: "لا", skip: "تخطّي",
        login: "تسجيل الدخول", emailLabel: "البريد الجامعي", askPlaceholder: "ما هي ساعات الدوام؟" },
  de: { send: "Senden", helpful: "War das hilfreich?", yes: "Ja", no: "Nein", skip: "Überspringen",
        login: "Anmelden", emailLabel: "GJU-E-Mail", askPlaceholder: "Wie sind die Öffnungszeiten?" },
};
```

- [ ] **Step 4: API proxy**

```ts
// frontend/app/api/[...path]/route.ts
import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_API_BASE ?? "http://backend:8080";

async function proxy(req: NextRequest, ctx: { params: { path: string[] } }) {
  const path = ctx.params.path.join("/");
  const url = `${BACKEND}/${path}${req.nextUrl.search}`;
  const headers = new Headers(req.headers);
  headers.set("host", new URL(BACKEND).host);
  const init: RequestInit = {
    method: req.method, headers,
    body: ["GET","HEAD"].includes(req.method) ? undefined : await req.text(),
    redirect: "manual",
  };
  const upstream = await fetch(url, init);
  const res = new NextResponse(upstream.body, { status: upstream.status });
  upstream.headers.forEach((v, k) => {
    if (k.toLowerCase() === "set-cookie") res.headers.append("set-cookie", v);
    else res.headers.set(k, v);
  });
  return res;
}

export const GET = proxy; export const POST = proxy;
export const PUT = proxy; export const DELETE = proxy;
```

- [ ] **Step 5: Commit**

```bash
git add frontend/lib frontend/app/api
git commit -m "frontend: types, api proxy, fetch wrapper, i18n"
```

---

### Task 8.3: Login page

**Files:**
- Create: `frontend/app/login/page.tsx`

- [ ] **Step 1: Implementation**

```tsx
// frontend/app/login/page.tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { T } from "@/lib/i18n";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const router = useRouter();

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(null);
    try {
      await api("/auth/login", { method: "POST", body: JSON.stringify({ email }) });
      router.push("/chat");
    } catch (x: any) { setErr(String(x.message || x)); }
  }

  return (
    <main className="mx-auto max-w-sm p-8">
      <h1 className="text-2xl font-semibold mb-6">GJU Library AI</h1>
      <form onSubmit={submit} className="space-y-3">
        <label className="block text-sm">{T.en.emailLabel}</label>
        <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
               className="w-full border rounded px-3 py-2" placeholder="you@gju.edu.jo" />
        <button className="w-full bg-black text-white rounded px-3 py-2">{T.en.login}</button>
        {err && <p className="text-red-600 text-sm">{err}</p>}
      </form>
      <p className="text-xs text-neutral-500 mt-6">M0 dev login. Entra ID SSO replaces this in a later milestone.</p>
    </main>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/login
git commit -m "frontend: dev login page"
```

---

### Task 8.4: AnswerSegments and TrackedLink components

**Files:**
- Create: `frontend/app/chat/components/TrackedLink.tsx`
- Create: `frontend/app/chat/components/AnswerSegments.tsx`

The renderer outputs typed segments. The frontend maps them to React elements — text becomes `{value}` (auto-escaped by React), passage references become a small superscript, links use `TrackedLink`. **No `dangerouslySetInnerHTML`.**

- [ ] **Step 1: `TrackedLink.tsx`**

```tsx
// frontend/app/chat/components/TrackedLink.tsx
"use client";
type Props = {
  clickId: string;
  label: string;
  apiBase?: string;   // defaults to relative /api proxy
};
export function TrackedLink({ clickId, label, apiBase = "/api" }: Props) {
  return (
    <a href={`${apiBase}/go/${encodeURIComponent(clickId)}`}
       target="_blank" rel="noopener noreferrer"
       className="underline decoration-dotted">
      {label}
    </a>
  );
}
```

- [ ] **Step 2: `AnswerSegments.tsx`**

```tsx
// frontend/app/chat/components/AnswerSegments.tsx
"use client";
import type { Segment } from "@/lib/types";
import { TrackedLink } from "./TrackedLink";

export function AnswerSegments({ segments }: { segments: Segment[] }) {
  return (
    <span>
      {segments.map((s, i) => {
        if (s.type === "text") return <span key={i}>{s.value}</span>;
        if (s.type === "passage_ref")
          return <sup key={i} className="text-xs text-neutral-500">[P{s.passage_id}]</sup>;
        // link
        return <TrackedLink key={i} clickId={s.click_id} label={s.label} />;
      })}
    </span>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app/chat/components/TrackedLink.tsx frontend/app/chat/components/AnswerSegments.tsx
git commit -m "frontend: TrackedLink + AnswerSegments (no innerHTML)"
```

---

### Task 8.5: ChatMessage, ChatInput, FeedbackPrompt

**Files:**
- Create: `frontend/app/chat/components/ChatMessage.tsx`
- Create: `frontend/app/chat/components/ChatInput.tsx`
- Create: `frontend/app/chat/components/FeedbackPrompt.tsx`

- [ ] **Step 1: `ChatMessage.tsx`**

```tsx
// frontend/app/chat/components/ChatMessage.tsx
import type { Lang, Segment } from "@/lib/types";
import { dirOf } from "@/lib/i18n";
import { AnswerSegments } from "./AnswerSegments";

type Props = {
  role: "user" | "assistant";
  text?: string;
  segments?: Segment[];
  lang: Lang;
  citations?: { id: number; title: string | null; source: string }[];
};

export function ChatMessage({ role, text, segments, lang, citations }: Props) {
  const dir = dirOf(lang);
  const base = role === "assistant" ? "bg-white border" : "bg-neutral-100";
  return (
    <article className={`rounded-lg p-3 ${base}`} dir={dir}>
      {role === "assistant" && segments
        ? <div className="leading-relaxed"><AnswerSegments segments={segments} /></div>
        : <div className="whitespace-pre-wrap">{text}</div>}
      {citations && citations.length > 0 && (
        <ul className="mt-2 text-xs text-neutral-500 list-disc ms-5">
          {citations.map(c => <li key={c.id}>[P{c.id}] {c.title || c.source}</li>)}
        </ul>
      )}
    </article>
  );
}
```

- [ ] **Step 2: `ChatInput.tsx`**

```tsx
// frontend/app/chat/components/ChatInput.tsx
"use client";
import { useState } from "react";
import type { Lang } from "@/lib/types";
import { T } from "@/lib/i18n";

export function ChatInput({ onSend, lang }: { onSend: (q: string) => void; lang: Lang }) {
  const [v, setV] = useState("");
  return (
    <form className="flex gap-2"
          onSubmit={e => { e.preventDefault(); if (v.trim()) { onSend(v); setV(""); } }}>
      <input value={v} onChange={e => setV(e.target.value)} placeholder={T[lang].askPlaceholder}
             className="flex-1 border rounded px-3 py-2" />
      <button className="bg-black text-white rounded px-4 py-2">{T[lang].send}</button>
    </form>
  );
}
```

- [ ] **Step 3: `FeedbackPrompt.tsx`**

```tsx
// frontend/app/chat/components/FeedbackPrompt.tsx
"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import type { Lang } from "@/lib/types";
import { T } from "@/lib/i18n";

export function FeedbackPrompt({ queryId, lang }: { queryId: number; lang: Lang }) {
  const [done, setDone] = useState<string | null>(null);
  async function send(rating: number | null) {
    await api("/feedback", { method: "POST",
      body: JSON.stringify({ scope: "answer", query_id: queryId, rating }) });
    setDone(rating === 1 ? T[lang].yes : rating === -1 ? T[lang].no : T[lang].skip);
  }
  if (done) return <p className="text-xs text-neutral-500">✓ {done}</p>;
  return (
    <div className="text-xs text-neutral-500 flex items-center gap-2">
      <span>{T[lang].helpful}</span>
      <button className="underline" onClick={() => send(1)}>{T[lang].yes}</button>
      <button className="underline" onClick={() => send(-1)}>{T[lang].no}</button>
      <button className="underline" onClick={() => send(null)}>{T[lang].skip}</button>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/app/chat/components/ChatMessage.tsx frontend/app/chat/components/ChatInput.tsx frontend/app/chat/components/FeedbackPrompt.tsx
git commit -m "frontend: chat components"
```

---

### Task 8.6: Chat page

**Files:**
- Create: `frontend/app/chat/page.tsx`

- [ ] **Step 1: Implementation**

```tsx
// frontend/app/chat/page.tsx
"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { ChatResponse, Lang, Segment } from "@/lib/types";
import { ChatMessage } from "./components/ChatMessage";
import { ChatInput } from "./components/ChatInput";
import { FeedbackPrompt } from "./components/FeedbackPrompt";

type Turn = {
  role: "user" | "assistant";
  text?: string;
  segments?: Segment[];
  lang: Lang;
  query_id?: number;
  citations?: ChatResponse["citations"];
};

export default function ChatPage() {
  const router = useRouter();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const [lang, setLang] = useState<Lang>("en");

  useEffect(() => { api("/auth/me").catch(() => router.push("/login")); }, [router]);

  async function send(query: string) {
    setBusy(true);
    setTurns(t => [...t, { role: "user", text: query, lang }]);
    try {
      const r = await api<ChatResponse>("/chat", { method: "POST", body: JSON.stringify({ query }) });
      setLang(r.lang);
      setTurns(t => [...t, {
        role: "assistant", segments: r.segments, query_id: r.query_id,
        citations: r.citations, lang: r.lang,
      }]);
    } catch (e: any) {
      setTurns(t => [...t, { role: "assistant", text: `Error: ${e.message}`, lang }]);
    } finally { setBusy(false); }
  }

  return (
    <main className="mx-auto max-w-3xl p-6 flex flex-col gap-4 min-h-screen">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">GJU Library AI</h1>
        <select value={lang} onChange={e => setLang(e.target.value as Lang)}
                className="border rounded px-2 py-1 text-sm">
          <option value="en">English</option><option value="ar">العربية</option><option value="de">Deutsch</option>
        </select>
      </header>
      <div className="flex-1 flex flex-col gap-3">
        {turns.map((t, i) => (
          <div key={i} className="space-y-1">
            <ChatMessage role={t.role} segments={t.segments} text={t.text}
                         lang={t.lang} citations={t.citations} />
            {t.role === "assistant" && t.query_id && <FeedbackPrompt queryId={t.query_id} lang={t.lang} />}
          </div>
        ))}
        {busy && <p className="text-sm text-neutral-500">…</p>}
      </div>
      <div className="sticky bottom-0 bg-white pt-2"><ChatInput onSend={send} lang={lang} /></div>
    </main>
  );
}
```

- [ ] **Step 2: Verify**

```bash
docker compose restart frontend
# Open http://localhost:3000 in a browser:
# 1) login with test@gju.edu.jo
# 2) ask "What are the library hours?" → answer renders, [P<id>] superscripts visible
# 3) ask "I need IEEE engineering papers" → IEEE link appears, click → /api/go/c_… → external redirect
# 4) ask "ما هي ساعات الدوام؟" → answer renders RTL in Arabic
# 5) feedback 👍 → recorded in feedback_events
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app/chat/page.tsx
git commit -m "frontend: chat page wiring segments + feedback (no innerHTML)"
```

---

# Phase 9 — End-to-end verification + handoff

### Task 9.1: README and runbook

**Files:**
- Create: `gju-library-ai/README.md`
- Create: `gju-library-ai/docs/runbook-m0.md`

- [ ] **Step 1: `README.md`**

```markdown
# GJU Library AI — M0

Trilingual (EN/AR/DE) library-information chatbot grounded in the FAQ + services + databases corpus, with click-tracking and feedback logging.

## Quickstart

cp .env.example .env
docker compose up -d postgres ollama
docker compose exec ollama ollama pull qwen2.5:7b-instruct
docker compose up -d backend
docker compose exec backend alembic upgrade head
docker compose exec backend python -m ingest.run
docker compose up -d frontend

Open http://localhost:3000 and sign in with any `@gju.edu.jo` email.

## What's in M0
- 5-file corpus (FAQs + services + library info + 15-database registry).
- Hybrid retrieval (tsvector + pgvector → RRF → bge-reranker-v2-m3).
- Trilingual prompting with [P<id>] citations and [DB:slug] tracked links.
- Email-domain dev login (Entra ID OIDC arrives later).
- Click and feedback logging to PostgreSQL.
- **No innerHTML on the frontend** — answers are rendered from typed segments.

## What's NOT in M0
- Entra ID SSO (stub used).
- Admin dashboard + PDF export.
- MARC catalog + DSpace ingestion.
- Retention purge cron, off-site backups.

See `docs/superpowers/specs/2026-04-28-gju-library-ai-design.md`.
```

- [ ] **Step 2: `docs/runbook-m0.md`**

```markdown
# Runbook (M0)

## Reset corpus
docker compose exec backend python -m ingest.run

## Add a database
Edit `data/seeds/subscription_databases.yaml`, then re-run ingestion.

## Inspect logs
docker compose exec postgres psql -U gju -d gju_library -c \
  "SELECT created_at, lang, raw_query, model_name, latency_ms FROM query_log ORDER BY id DESC LIMIT 20;"

## Click-through analytics
docker compose exec postgres psql -U gju -d gju_library -c "
SELECT target_ref AS db,
       count(*) FILTER (WHERE clicked_at IS NOT NULL) AS clicked,
       count(*) AS shown,
       round(100.0 * count(*) FILTER (WHERE clicked_at IS NOT NULL) / nullif(count(*),0), 1) AS ctr
FROM click_events WHERE target_type='database' GROUP BY 1 ORDER BY shown DESC;"
```

- [ ] **Step 3: Commit**

```bash
git add README.md docs/runbook-m0.md
git commit -m "docs: M0 README + minimal runbook"
```

---

### Task 9.2: End-to-end smoke script

**Files:**
- Create: `gju-library-ai/scripts/smoke.sh`

- [ ] **Step 1: Write script**

```bash
#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://localhost:8080}"
EMAIL="${EMAIL:-smoke@gju.edu.jo}"
COOKIE=$(mktemp)

curl -sf -c "$COOKIE" -H 'content-type: application/json' \
     -d "{\"email\":\"$EMAIL\"}" "$BASE/auth/login" >/dev/null
echo "✓ login"

for Q in "What are the library hours?" "ما هي ساعات الدوام؟" "Wie greife ich von zu Hause auf Datenbanken zu?" "I need IEEE engineering papers on robotics"; do
  RES=$(curl -sf -b "$COOKIE" -H 'content-type: application/json' \
        -d "$(jq -nc --arg q "$Q" '{query:$q}')" "$BASE/chat")
  LAT=$(echo "$RES" | jq -r .latency_ms)
  N=$(echo "$RES" | jq '.segments | length')
  echo "✓ chat ($LAT ms, $N segments): $Q"
  CID=$(echo "$RES" | jq -r '[.segments[] | select(.type=="link")][0].click_id // empty')
  if [[ -n "${CID:-}" ]]; then
    LOC=$(curl -sf -b "$COOKIE" -o /dev/null -w '%{redirect_url}' "$BASE/go/$CID")
    echo "  → click → $LOC"
  fi
done

rm -f "$COOKIE"
echo "all ✓"
```

- [ ] **Step 2: Run**

```bash
chmod +x scripts/smoke.sh
./scripts/smoke.sh
```
Expected: 4 ✓ chat lines with non-zero latency; at least one `→ click → https://...`.

- [ ] **Step 3: Commit**

```bash
git add scripts/smoke.sh
git commit -m "scripts: end-to-end smoke"
```

---

### Task 9.3: Manual UI sanity + SQL spot-check

- [ ] **Step 1: Open `http://localhost:3000`, sign in.**

- [ ] **Step 2: Ask in EN, AR, DE — verify:**
  - Answer renders in the asked language (RTL for AR).
  - `[P<id>]` superscripts present where the model cited.
  - At least one DB recommendation when a subject keyword appears.
  - Database name is a clickable link, `href` is `/api/go/c_…` (not raw URL).
  - Clicking opens the real database URL in a new tab.
  - Feedback 👍/👎/skip records.

- [ ] **Step 3: SQL spot-check**

```bash
docker compose exec postgres psql -U gju -d gju_library <<'EOF'
SELECT lang, count(*) FROM query_log GROUP BY 1 ORDER BY 1;
SELECT target_type,
       count(*) FILTER (WHERE clicked_at IS NOT NULL) AS clicked,
       count(*) AS shown
FROM click_events GROUP BY 1;
SELECT scope, count(*), avg(rating)::numeric(5,2) FROM feedback_events GROUP BY 1;
EOF
```

If all three return rows reflecting your interactions, M0 is done.

- [ ] **Step 4: Tag**

```bash
git tag m0-complete
```

---

## Definition of Done — M0

- [ ] `docker compose up` brings the system up.
- [ ] `python -m ingest.run` ingests the 5 source files + 15 databases.
- [ ] `/auth/login` accepts `*@gju.edu.jo`, rejects others.
- [ ] `/chat` returns typed segments (no HTML) in EN/AR/DE.
- [ ] Frontend renders segments via React (no `dangerouslySetInnerHTML` anywhere).
- [ ] `/go/<id>` redirects and stamps `clicked_at`.
- [ ] `/feedback` records both answer- and click-scoped ratings.
- [ ] `query_log`, `click_events`, `feedback_events` populate end-to-end.
- [ ] Smoke script passes.

## Hand-off to later milestones

- **MARC + DSpace ingestion (M2):** add `ingest/marc_loader.py` and `ingest/dspace_loader.py` producing `Passage`s; reuse `embed_index.upsert_passages`. Retrieval/chat unchanged.
- **Entra ID SSO (M3):** replace `auth/stub.py` with `auth/oidc.py` behind the same `get_current_user_id` dependency.
- **Admin dashboard + PDF export (M4):** add `routers/admin.py` with SQL views over `query_log`/`click_events`/`feedback_events`; PDF via `reportlab`.
- **Retention purge + backups (M5):** cron service in compose; `ingest/retention_purge.py`.
