# Phase 3: Live Web Search for LLM (Design)

**Date:** 2026-07-06  
**Goal:** Give the chatbot the ability to search the internet in real time so it can answer questions that fall outside the static corpus — new library hours, staff changes, event announcements, full book details not in Open Library, etc.

## Motivation

The current stack is retrieval-augmented generation (RAG) over a static corpus ingested offline.  
Gaps identified in M0 testing:

- Library contact details, director name, office hours — were only available by manually scraping the GJU website and inserting passages (done as a one-off in M0).
- Book details beyond what Open Library returns (local cover art, availability, branch location) require a live OPAC query, which the LLM cannot do today.
- Staff changes, holiday closures, new subscription announcements — content that goes stale between ingest runs.

## Approach: Tool-calling Loop (ReAct pattern)

The chatbot gains a `web_search` tool and a `fetch_url` tool.  
On each turn, the LLM can choose to call one of these tools, inspect the result, and either answer or call another tool.

```
user query
    │
    ▼
router (unchanged)
    │
    ▼
RAG retrieval (unchanged, still the first pass)
    │
    ▼
Tool-calling LLM loop (new in Phase 3)
  ┌─────────────────────────────────┐
  │  1. Decide: answer or search?   │
  │  2. If search: call web_search  │
  │  3. Observe result              │
  │  4. Repeat up to N=3 times      │
  │  5. Final answer                │
  └─────────────────────────────────┘
    │
    ▼
render_answer (unchanged)
```

## Why This Requires a Bigger Model

`qwen2.5:3b-instruct` is reliable for extraction and short answers but cannot reliably follow the JSON schema for tool calls.  
Phase 3 requires one of:

| Option | Model | Notes |
|--------|-------|-------|
| A (recommended) | Gemini 2.0 Flash | Free tier, supports function calling natively, already planned in the Gemini provider plan (`2026-06-01-gemini-provider.md`) |
| B | GPT-4o-mini | ~$0.15/1M tokens, OpenAI tool-calling API |
| C | qwen2.5:7b-instruct (local) | Larger local model, better tool-following, no API cost but slower CPU |

## Tools to Implement

### `web_search(query: str) -> list[SearchResult]`

Wrapper around a search API. Priority:
1. **SerpAPI** (free 100 searches/month trial) or **Brave Search API** (free 2k/month)
2. **DuckDuckGo HTML scrape** (zero-cost fallback, no API key, robots.txt compliant)

Returns top-5 results: `{title, url, snippet}`.

### `fetch_url(url: str) -> str`

Fetches a URL and returns cleaned text (boilerplate stripped via `trafilatura`).  
Hard-coded allow-list to start: `*.gju.edu.jo`, `opac.jopuls.edu.jo`, `openlibrary.org`.

## Scope for Phase 3

**In scope:**
- `web_search` and `fetch_url` tools wired into a ReAct loop in `pipeline.py`
- Tool results injected as assistant/tool message pairs in the conversation
- Max 3 tool calls per turn (hard cap, cost control)
- GJU-specific sources prioritised in the search query (`site:gju.edu.jo OR site:jopuls.edu.jo`)

**Out of scope:**
- Web search in Arabic (search query will be English-first; translation left for later)
- Persistent web-search cache (each turn is fresh)
- Admin UI to configure search tool settings

## Migration Path

1. Complete the Gemini provider (plan: `2026-06-01-gemini-provider.md`).
2. Implement `backend/app/tools/web_search.py` and `backend/app/tools/fetch_url.py`.
3. Add tool-call loop in `pipeline.py` between RAG retrieval and `build_messages`.
4. Feature-flag via env var `ENABLE_WEB_SEARCH=false` — off by default so the Ollama path is unaffected.
5. Test on Railway with Gemini provider enabled.

## Success Criteria

- "Who is the head of the GJU library?" → real-time answer from `gju.edu.jo` staff page.
- "Is the library open on Eid Al-Adha?" → correct holiday closure from GJU announcements.
- "Where can I find book X in the OPAC?" → live OPAC result with direct link.
- No more than 5s added latency per search call.
