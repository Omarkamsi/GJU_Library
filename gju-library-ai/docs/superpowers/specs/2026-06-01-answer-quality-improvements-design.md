# Answer Quality Improvements Design

**Date:** 2026-06-01
**Goal:** Ensure subscription database links always appear in topic answers, and book list responses include up to 5 books without truncation.

## Problems

1. **Database links missing for general queries** — `match_databases` uses Jaccard subject overlap. Queries like "online journals" or "help with research" don't trigger subject extraction, so no databases are matched. Even when databases ARE in context, the LLM adds description text after `[DB:slug]` tokens, creating messy interleaved text+link segments.

2. **Book list truncation** — max_tokens=800 cuts multi-book responses short (each book entry ≈ 80 tokens; 5 books + intro + DB links ≈ 900–1100 tokens).

## Changes

### 1. `backend/app/llm/prompts.py` — mandatory DB inclusion rule

Replace the passive "when recommending a database, write [DB:slug]" with:

> "If DATABASES are listed in your context, you MUST include every one in your answer with its [DB:slug] token. Write the token only — do not add the database name or description after it."

Add to book routing rules:

> "When asked for a list of books, present up to 5 matching catalog books using the card format."

Apply the same update to all three languages (EN, AR, DE).

### 2. `backend/app/retrieval/routing.py` — general research keywords

Add keywords that trigger broad subject matching so "online journals", "research databases", "digital resources" queries match databases:

```python
"General": [
    "database", "databases", "journal", "journals", "online resource",
    "digital resource", "subscription", "research resource",
    "قاعدة بيانات", "مجلة", "مصادر رقمية",
    "Datenbank", "Zeitschrift", "digitale Ressource",
]
```

And add "General" to subscription databases' subject lists in the DB seed data, so they match this new subject.

### 3. `backend/app/chat/pipeline.py` — bump max_tokens 800 → 1200

At both call sites (`stream_chat` and `run_chat`).

## Out of Scope

- No frontend changes
- No new segment types
- No changes to `render.py` or `match_databases` scoring logic
