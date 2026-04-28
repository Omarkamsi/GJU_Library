# GJU Library AI Assistant — Design Spec

**Date:** 2026-04-28
**Author:** Omar Alamssi (with design assistance)
**Stakeholder:** Mr. Laith Alnaser, Library Director, German Jordanian University
**Status:** Awaiting approval

## 1. Purpose & scope

A natural-language assistant for the GJU Library catalog (~45,000 records — books and bachelor/master/PhD theses) that:

1. Lets students search the catalog conversationally, in English, Arabic, or German.
2. Surfaces the library's paid subscription databases (IEEE, JSTOR, ScienceDirect, etc.) alongside catalog results.
3. Tracks which databases are clicked and whether students find them helpful, producing analytics that drive renewal decisions.
4. Restricts access to GJU users via Microsoft Entra ID SSO.

**Deployment target:** production pilot. The library plans to run this for real students; design decisions favor robustness and operability over feature breadth.

**Explicitly out of scope for v1:** patron borrowing records, fines, room booking, multi-turn agentic retrieval, real-time dashboards, predictive renewal modeling, personalized ranking.

## 2. Background — what we already know about GJU's environment

| Concern | Finding | Implication |
|---|---|---|
| Catalog (ILS) | Horizon Information Portal at `hip.jopuls.org.jo/web/gju` (SirsiDynix Horizon, shared across Jordanian universities) | MARC21 export must be requested from library staff; no live API |
| Theses repository | MyVLib at `myvlib.gju.edu.jo/xmlui/` — DSpace 5/6 | Harvestable via OAI-PMH at `/oai/request` |
| Subscription databases | 16 confirmed (ScienceDirect, IEEE Xplore, Scopus, Springer, EBSCO, Emerald, Sage, Taylor & Francis, ProQuest, Statista, Ebrary, ICE Virtual Library, SciVal, Qistas, Europathek, Deepknowledge) | Small enough to maintain by hand |
| SSO | Microsoft Entra ID (GJU is a Microsoft 365 tenant) | OIDC Authorization Code + PKCE |
| Stakeholder | Mr. Laith Alnaser, `Laith.Alnaser@gju.edu.jo`, ext. 4871 | Single decision-maker for data access and dashboard requirements |

## 3. Stack decisions (locked)

| Layer | Choice | Reason |
|---|---|---|
| Backend | Python 3.12 + FastAPI | Async, type-safe, matches RAG ecosystem |
| Frontend | Next.js 14 (App Router) + Tailwind + shadcn/ui | Standalone at `library-ai.gju.edu.jo` |
| Database | PostgreSQL 16 + pgvector | One DB for vectors, audit, analytics — single backup path |
| Embeddings | BAAI/BGE-M3 (1024-dim, multilingual) | Trilingual coverage, open weights, CPU-feasible |
| Reranker | BAAI/bge-reranker-v2-m3 | Sharper top-k, ~50ms for 20 pairs on CPU |
| LLM | Self-hosted (Qwen 2.5 / Llama 3.1) via vLLM, **abstracted behind `LLMClient` interface** so Azure OpenAI can be swapped in by config | Privacy + cost; swap-out path required |
| Auth | Microsoft Entra ID OIDC (Authorization Code + PKCE) | GJU is a Microsoft tenant |
| Container | Docker Compose (postgres + app + optional vllm) | Single-VM deployment; library IT can operate it |

## 4. High-level architecture

```
Browser (library-ai.gju.edu.jo, Next.js)
      │ OIDC ↔ Entra ID
      │ /api/* (cookie-JWT)
      ▼
FastAPI backend
  ├── /chat        — RAG orchestration
  ├── /go/<id>     — click-tracking proxy (302 redirect)
  ├── /feedback    — 👍/👎 capture
  └── /admin/*     — analytics + PDF export
      │
      ├──▶ PostgreSQL + pgvector  (one DB: bib + audit + analytics)
      └──▶ LLM service            (vLLM local, or Azure OpenAI)

Ingestion workers (cron, separate from web app):
  • marc_ingest.py    — Horizon MARC21 dump
  • dspace_ingest.py  — MyVLib OAI-PMH
  • embed_index.py    — BGE-M3 → pgvector + tsvector
  • retention_purge.py — 12-month PII purge
```

**Hard component boundaries.** Frontend doesn't know how retrieval works; retrieval doesn't know which LLM is plugged in; ingestion doesn't import web-app code. Each piece is independently testable.

## 5. Ingestion pipeline

### 5.1 MARC21 source (Horizon)

`pymarc`-based parser extracts these tags:

| Tag | Subfield | Field |
|---|---|---|
| 245 | $a $b | title (+ subtitle) |
| 100 / 700 | $a | authors[] |
| 260 / 264 | $b $c | publisher, year |
| 502 | $a | thesis_note → drives `material_type` and `thesis_level` |
| 520 | $a | abstract |
| 650 | $a | subjects[] |
| 050 / 082 | $a | call_number |
| 856 | $u $z | online_url, online_label |
| 008 pos 35-37 | — | language |

Thesis level extracted from 502 via regex matching `Ph.D|Master|M.Sc|Bachelor|B.Sc` (and German/Arabic variants). Records with 502 but unmatched degree → `thesis_level='unknown'` with warning logged.

### 5.2 DSpace source (MyVLib)

`sickle` OAI-PMH harvester against `metadataPrefix=oai_dc`. Maps Dublin Core to the same canonical schema. All DSpace records are theses by construction.

### 5.3 Canonical record schema

Every parsed record — book or thesis, Horizon or DSpace — becomes one row in `bib_items`:

```jsonc
{
  "id": "marc:0000123" | "myvlib:hdl_...",
  "source": "horizon" | "myvlib",
  "material_type": "book" | "thesis",
  "thesis_level": null | "bachelor" | "master" | "phd" | "unknown",
  "title": "...", "authors": [...], "year": 2023, "language": "eng",
  "call_number": "...", "subjects": [...], "abstract": "...",
  "online_url": "...",
  "embedding_text": "Title: ... | Authors: ... | Type: ... | Subjects: ... | Abstract: ..."
}
```

The `embedding_text` template gives the embedder structural signal that flat concatenation hides.

### 5.4 Idempotency, incremental sync, quality gates

- Upsert on `id`; re-runs don't duplicate.
- DSpace harvest uses `from=` parameter against `ingest_state.last_run_at`.
- MARC ingest is full-replace by default; `--since` flag supported.
- Embeddings skipped when `embedding_text` hash unchanged.
- Each run writes `report.json` with input/output counts and warnings (missing 245, missing 520, unrecognized degree, etc.) — this is the artifact we hand to cataloguers.

### 5.5 Decisions on edge cases

- **Records with no abstract:** embed anyway with title + subjects (don't skip — losing 412+ records hurts recall more than embedding weak text).
- **Mixed-language records:** one record, one embedding (BGE-M3 handles cross-lingual queries natively; splitting adds dedup complexity for marginal recall gain).
- **`embedding_text` weighting:** abstract appears once, not duplicated (no evidence duplication helps with BGE-M3).

## 6. Hybrid retrieval pipeline

Three-stage: parallel candidate generation → fusion → rerank.

### 6.1 Stage 1: parallel candidates (top-50 each)

**Lexical** — Postgres `tsvector` (search_vector generated column over title + authors + subjects + abstract) with GIN index, plus `pg_trgm` GIN index over title+authors for fuzzy author matching. `'simple'` config (no stemming) since BGE-M3 handles morphology on the vector side.

**Semantic** — pgvector HNSW index on `embedding vector(1024)`, cosine distance.

Both queries accept structured filters (`material_type`, `thesis_level`, `year_min/max`) so the planner can narrow candidates before scoring.

### 6.2 Stage 2: Reciprocal Rank Fusion

```
score(doc) = Σᵢ 1 / (k + rankᵢ(doc))      k = 60
```

RRF over weighted-sum: no normalization needed, robust to one retriever returning garbage. Output: top-20.

### 6.3 Stage 3: Cross-encoder reranker

`bge-reranker-v2-m3` rescores the top-20. Output: top-5 to LLM. **Enabled by default** (50ms latency cost is invisible; quality gain is the single biggest lever).

### 6.4 Pre-retrieval: query understanding

Two implementations behind one interface:

- **`RuleBasedRouter`** — regex-driven extraction of `material_type`, `thesis_level`, year filters. Default for v1.
- **`LLMRouter`** — JSON-schema-constrained LLM call. Built as stub, enabled only when eval shows rule misses.

### 6.5 Post-retrieval: subscription-database matcher

After top-5 bib items are selected, the `subscription_databases` table is queried for rows whose `subjects[]` overlap either the retrieved items' subjects or query-extracted subjects. **Always shown, capped at 3, visually separated from book results** (footer block: *"For more recent research, try:"*).

### 6.6 Retriever interface

```python
class Retriever(Protocol):
    def search(self, query: str, user: User, k: int = 5) -> RetrievalResult: ...

@dataclass
class RetrievalResult:
    items: list[BibItem]
    databases: list[Database]
    debug: dict   # per-stage scores, for offline replay
```

The `debug` field makes every retrieval replayable in evaluation.

## 7. Click tracking & feedback

### 7.1 Proxy (`/go/<click_id>`)

Chatbot output **never** contains raw external URLs. At answer-render time, every external link is wrapped:

```
displayed: https://library-ai.gju.edu.jo/go/c_8a3f2e1b
target:    https://ieeexplore.ieee.org/document/9876543
```

A `click_events` row is inserted at render time with `clicked_at = NULL`. `/go/<id>` looks up the row, verifies `user_id == current SSO user`, sets `clicked_at = now()`, and **302-redirects** to the target URL. This gives us shown-vs-clicked CTR per database, not just raw click counts.

### 7.2 Feedback prompt

After each click, the chat UI shows a per-link prompt with a **30-second delay** (so the rating reflects actual evaluation, not impulse): *"Was this helpful?"* with 👍 / 👎 / skip. Independently, every chat answer carries an answer-level 👍/👎. Skip is recorded explicitly (`rating = NULL`) so engagement rate is measurable.

**Cadence for v1:** prompt after every click for the first 4 weeks of pilot (we need the data to validate the system), then re-evaluate based on response rate.

### 7.3 Query log

Every chat turn writes one `query_log` row before the LLM is called: raw query, language, extracted filters, retrieved IDs, shown databases, answer text, latency, model name. This is the join key for all analytics.

### 7.4 Privacy boundary (non-negotiable)

- `user_id = HMAC(email, server_pepper)` — never store email, name, or student ID.
- Department joined from Entra ID's `department` claim (or a fallback lookup table from IT) — sufficient for "which majors use which databases" analytics.
- `raw_query`, `answer_text`, and feedback `comment` are PII-class with **12-month retention**; aggregates retained indefinitely.
- No keystroke logging, no scroll tracking, no third-party analytics.
- Aggregates suppress any cell with fewer than 5 distinct users.

## 8. Data model

Eight tables in PostgreSQL. Full DDL will be produced as part of the implementation plan; key shape:

| Table | Purpose | Key indexes |
|---|---|---|
| `bib_items` | Catalog records + embeddings | GIN(search_vector), HNSW(embedding), GIN(trgm), B-tree(material_type, thesis_level, year) |
| `subscription_databases` | The 16 paid databases + subjects + URLs | — |
| `users` | Hashed SSO subjects with department/role | PK on hash |
| `sessions` | Login-bounded sessions | FK to users |
| `query_log` | Every chat turn | (user_id, created_at), (created_at) |
| `click_events` | Pre-allocated at render, updated on click | (target_type, target_id, clicked_at), (query_id) |
| `feedback_events` | Per-click and per-answer ratings | FK to click_events / query_log |
| `ingest_state` | Operational checkpoint per source | PK on source |

Migrations managed by Alembic.

## 9. Authentication

OIDC Authorization Code + PKCE against the GJU Entra ID tenant. Strict rules:

1. **Email domain enforced server-side** — Entra ID returns guests; FastAPI rejects anything not matching `@gju.edu.jo` even with a valid token (configurable via `ALLOWED_EMAIL_DOMAINS`).
2. **No tokens in localStorage** — session cookie is `HttpOnly; Secure; SameSite=Lax`, holding a backend-signed JWT (8h expiry); the frontend never sees the Entra ID token.
3. **Department claim is load-bearing** — the audit value depends on knowing which majors click which databases. If GJU IT hasn't populated the `department` claim universally, we fall back to a lookup table they provide. **Worth confirming with IT during onboarding.**

Admin role is granted via direct SQL `UPDATE users SET role='admin' WHERE id=...` — explicit, auditable, no self-service.

## 10. Analytics dashboard

Single page, four panels, one filter bar (date range × faculty × department × language).

| Panel | Question answered | Data source |
|---|---|---|
| 1. Database usage & CTR | "Which databases are students actually using?" | `click_events` × `subscription_databases` |
| 2. Satisfaction by database | "Are the databases I'm paying for finding what students need?" | `feedback_events` joined to clicks |
| 3. Unanswered queries (clustered by embedding similarity ≥ 0.85) | "Where are the gaps in our collection?" | `query_log` with empty `retrieved_ids` or down-rated answers |
| 4. Usage by department | "Which majors use which resources?" | `click_events` × `users.department` |

**PDF export** (`/admin/export/budget-report`): four-page report built with `reportlab` — cover page, four panels, appendix listing bottom-20% databases with one-line recommendations. This is the artifact Mr. Alnaser hands to the budget committee.

## 11. Folder structure

```
gju-library-ai/
├── README.md, docker-compose*.yml, .env.example, pyproject.toml
├── backend/
│   ├── app/
│   │   ├── main.py, config.py, deps.py, db.py
│   │   ├── auth/        — oidc, jwt, user
│   │   ├── routers/     — auth, chat, go, feedback, admin
│   │   ├── retrieval/   — interface, hybrid, lexical, semantic, reranker, fusion, routing, databases
│   │   ├── llm/         — interface, azure_openai, vllm_local, prompts
│   │   ├── analytics/   — queries, clustering, pdf_report
│   │   └── models/      — one file per table
│   ├── ingest/          — marc_ingest, dspace_ingest, embed_index, seed_databases, retention_purge
│   ├── alembic/
│   └── tests/           — unit, integration, e2e, fixtures
├── frontend/            — Next.js 14 app router
│   ├── app/             — layout, chat, admin, api proxy
│   ├── components/      — ChatMessage, BibCard, DatabaseSuggestion, FeedbackPrompt
│   └── lib/, tailwind.config.ts
├── docs/
│   ├── architecture.md, runbook.md, data-request.md
│   └── adr/             — 0001-pgvector-not-chroma, 0002-self-hosted-llm, 0003-rrf, 0004-hash-only-user-id
└── .github/workflows/   — ci.yml, deploy.yml
```

Key boundaries:
- `ingest/` is a separate package; cannot import `app/`.
- `llm/interface.py` is the single swap-point between vLLM and Azure OpenAI.
- `adr/` records non-obvious decisions for future maintainers.

## 12. Deployment

Three environments, one codebase, three `.env` files:

| Env | Postgres | LLM | OIDC |
|---|---|---|---|
| dev | local | Azure OpenAI | Entra ID dev app |
| staging | GJU dev VM | Azure OpenAI | Entra ID dev app |
| prod | GJU prod VM | vLLM (when GPU available) | Entra ID prod app |

Docker Compose with three services: `postgres` (pgvector image), `app` (FastAPI + Next.js build), `llm` (vLLM, added later). Behind nginx/Caddy on the host for TLS termination.

## 13. Operational guarantees (v1 SLOs)

| Metric | Target |
|---|---|
| Chat response latency p95 | < 3 s end-to-end |
| Retrieval-only latency p95 | < 200 ms |
| Uptime during semester | 99% (~7 hr/month budget) |
| Data freshness — books | Weekly |
| Data freshness — theses | Daily (DSpace OAI-PMH incremental) |
| Backup RPO | 24 h |
| Backup RTO | 4 h |

## 14. Runbook (for GJU IT)

Single `docs/runbook.md`:

1. First-time deployment — `docker compose up -d`, run migrations, seed databases, MARC ingest, embed index. ~2 hours.
2. Daily cron — DSpace harvest 02:00, embed refresh 03:00, retention purge 04:00, backup 05:00.
3. Adding a subscription — one SQL insert, no code change.
4. Promoting an admin — one SQL update, audited via `pg_audit`.
5. Backups — nightly `pg_dump`, weekly off-site.
6. Triaging bad answers — flowchart routing to data quality vs. prompt/model issues.
7. Annual `USER_ID_PEPPER` rotation procedure.
8. Decommissioning — aggregate export + secure PII wipe.

## 15. Data dependencies (requested from library)

Sent to Mr. Alnaser on 2026-04-28:

1. Full MARC21 export (~45,000 records, MARCXML or `.mrc`, with tags 245/100/700/502/520/650/050/082/856).
2. Permission to harvest MyVLib via OAI-PMH at `myvlib.gju.edu.jo/oai/request`.
3. Subscription registry with EZproxy URLs.
4. Entra ID app registration (Tenant ID, Client ID, redirect URI, scoped client secret).
5. Historical EZproxy logs (baseline for analytics).
6. 50–100 anonymized real student questions (evaluation set).
7. Update cadence + cataloguing-team contact.
8. Confirmation that abstracts (520) may be displayed in answers.

Items 1, 3, 4, 5 are blockers; 2, 6, 7, 8 unblock quality but work can start without them.

## 16. Out of scope for v1 (recorded so we don't drift)

- Agentic / multi-hop retrieval
- On-the-fly web search
- Personalized ranking (no per-user model)
- Real-time dashboards (24h freshness is enough for renewal decisions)
- Per-student drill-down (privacy line)
- Predictive renewal modeling (insufficient time series)
- Trending-queries-this-week panel (irrelevant to renewal decision)

## 17. Risks & mitigations

| Risk | Mitigation |
|---|---|
| MARC21 export delayed by library bureaucracy | Start with 50-record fixture in repo; build ingestion + retrieval against it |
| `department` claim missing in Entra ID | Fallback lookup table from IT |
| Self-hosted LLM not feasible (no GPU) | `LLMClient` interface lets us ship with Azure OpenAI from day one |
| Catalog records have poor abstracts | Quality report from each ingest run drives cataloguer cleanup; embed title+subjects when 520 is missing |
| Privacy review blocks deployment | Hash-only user IDs, 12-month retention, suppression at 5-user cells, all documented in §7.4 |
| Data licensing on 520 abstracts | Confirm with Mr. Alnaser; truncate to first N words if licensing limits apply |

## 18. Implementation milestones (rough)

- **M1 — Ingestion + retrieval working on fixture data** (~2 weeks)
- **M2 — Full MARC + DSpace ingest from real GJU data** (~1 week, gated on data delivery)
- **M3 — Chat UI + Entra ID SSO + click tracking** (~2 weeks)
- **M4 — Analytics dashboard + PDF export** (~1 week)
- **M5 — Hardening, runbook, GJU IT handoff** (~1 week)

Detailed implementation plan to follow in the writing-plans phase.
