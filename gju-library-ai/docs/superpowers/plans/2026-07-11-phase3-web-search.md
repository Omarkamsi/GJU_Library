# Phase 3 Web Search Implementation Plan

> **Status: COMPLETE** — All 7 tasks implemented and verified. Provider switched from Gemini (geo-blocked in Jordan) to Groq (`llama-4-scout-17b-16e-instruct`), free tier, accessible from Jordan.

**Goal:** Add real-time web search to the GJU Library AI chatbot via a Groq-powered ReAct (tool-calling) loop so the bot can answer questions about current staff, hours, events, and book availability that fall outside the static RAG corpus.

**Architecture:** Three new files (`tools/web_search.py`, `tools/fetch_url.py`, `chat/groq_react_agent.py`) plus a new `GroqClient`, updates to `config.py`, `pipeline.py`, `prompts.py`, `deps.py`, and `pyproject.toml`. Guarded by `ENABLE_WEB_SEARCH=true` env flag. The ReAct loop runs only when `LLM_PROVIDER=groq` and `ENABLE_WEB_SEARCH=true`.

**Tech Stack:** `groq>=0.11` (OpenAI-compatible tool-calling), `ddgs>=0.1` (DuckDuckGo, no API key), `trafilatura>=2.0`, `httpx` (already in deps).

## Global Constraints

- `ENABLE_WEB_SEARCH=false` by default; must be explicitly enabled in `.env`.
- Max 3 tool calls per turn — hard cap, enforced in `groq_react_agent.py`.
- `fetch_url` enforces a hard-coded allow-list: `gju.edu.jo`, `jopuls.org.jo`, `openlibrary.org`. SSRF-hardened with `urlparse` hostname extraction (not substring match).
- Book cards suppressed for non-book queries via `_want_book_cards()` in `pipeline.py`.
- `.env` is gitignored and must never be committed.
- Gemini code remains in place; geo-blocked from Jordan on free tier.

## What was built

### Task 1: Groq provider + deps ✅
- `backend/pyproject.toml`: added `groq>=0.11`, `ddgs>=0.1`, `trafilatura>=2.0`
- `.env`: `LLM_PROVIDER=groq`, `GROQ_API_KEY=...`, `GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct`, `ENABLE_WEB_SEARCH=true`

### Task 2: `web_search` tool ✅
- `backend/app/tools/web_search.py`: DuckDuckGo via `ddgs.DDGS`, returns formatted title/url/snippet blocks

### Task 3: `fetch_url` tool ✅
- `backend/app/tools/fetch_url.py`: SSRF-hardened with `urlparse`, allow-list, IP literal rejection, manual redirect re-validation

### Task 4: `GroqClient` ✅
- `backend/app/llm/groq_client.py`: implements `LLMClient` (complete + stream) plus `chat_with_tools()` for ReAct

### Task 5: ReAct agent ✅
- `backend/app/chat/groq_react_agent.py`: OpenAI-compatible tool-calling loop, max 3 calls, prompt-injection envelope

### Task 6: Wired into pipeline ✅
- `backend/app/config.py`: `groq_api_key`, `groq_model`, `enable_web_search`
- `backend/app/deps.py`: `LLM_PROVIDER=groq` branch
- `backend/app/llm/prompts.py`: `build_react_system()`, tool-use rules
- `backend/app/chat/pipeline.py`: `_want_book_cards()` gate, Groq ReAct branch with real latency tracking

### Task 7: Verified ✅

| Question | Result |
|---|---|
| "Who is the GJU library director?" | Web search → staff directory link |
| "Is the library open on Eid Al-Adha?" | Infers from passages (public holiday = closed) + contact |
| "Show me books about software engineering" | Book cards (Ian Sommerville etc.) |
| "How do I access Turnitin?" | RAG → Nesreen.Malkawi@gju.edu.jo |
| `fetch_url('https://evil.com')` | "URL not allowed" ✅ |
| `fetch_url('https://evil.com?x=gju.edu.jo')` | "URL not allowed" ✅ (SSRF-safe) |
| Arabic: "ما هي ساعات عمل المكتبة؟" | Full RTL Arabic answer ✅ |
| Browser (Playwright, 1280×900) | 6/7 pass (book card timing issue in test only) |

## Commits
- `7e50659` feat: Groq ReAct agent for live web search (replaces Gemini)
- `45f882e` fix: suppress book card leakage and improve ReAct tool-use
