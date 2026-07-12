# Phase 3 Web Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real-time web search to the GJU Library AI chatbot via a Gemini-powered ReAct (tool-calling) loop so the bot can answer questions about current staff, hours, events, and book availability that fall outside the static RAG corpus.

**Architecture:** Three new files (`tools/web_search.py`, `tools/fetch_url.py`, `chat/react_agent.py`) plus targeted additions to `GeminiClient`, `config.py`, `pipeline.py`, and `prompts.py`. Guarded by `ENABLE_WEB_SEARCH=false` env flag — Ollama path is unaffected. The ReAct loop runs only when the LLM provider is Gemini and `ENABLE_WEB_SEARCH=true`.

**Tech Stack:** google-genai>=1.0 function calling, `duckduckgo-search`, `trafilatura`, `httpx` (already in deps).

## Global Constraints

- `ENABLE_WEB_SEARCH=false` by default; must be explicitly enabled in `.env`.
- Max 3 tool calls per turn — hard cap, enforced in `react_agent.py`.
- `fetch_url` enforces a hard-coded allow-list: `gju.edu.jo`, `jopuls.org.jo`, `openlibrary.org`.
- The Ollama / 3B-model path must remain identical — no regressions.
- `.env` is gitignored and must never be committed.

---

### Task 1: Enable Gemini provider and install new deps

**Files:**
- Modify: `backend/pyproject.toml`
- Manual: `.env` (not committed)

**Interfaces:**
- Produces: `duckduckgo_search.DDGS` importable; `trafilatura` importable; backend running on Gemini.

- [ ] **Step 1: Update `.env`**

Open `/root/gju-library-ai/.env` and apply these changes:

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=<your-key-from-aistudio.google.com>
GEMINI_MODEL=gemini-2.0-flash
ENABLE_WEB_SEARCH=true
```

(Keep everything else unchanged.)

- [ ] **Step 2: Add deps to pyproject.toml**

In `backend/pyproject.toml`, add two lines to the `dependencies` list after `"google-genai>=1.0"`:

```toml
  "google-genai>=1.0",
  "duckduckgo-search>=6.0",
  "trafilatura>=2.0",
```

- [ ] **Step 3: Install deps in the running backend container**

```bash
docker.exe compose -f /root/gju-library-ai/docker-compose.yml exec backend pip install "duckduckgo-search>=6.0" "trafilatura>=2.0"
```

Expected: `Successfully installed ...` or `Requirement already satisfied`.

- [ ] **Step 4: Verify imports**

```bash
docker.exe compose -f /root/gju-library-ai/docker-compose.yml exec backend python -c "
from duckduckgo_search import DDGS
import trafilatura
from google import genai
print('all ok')
"
```

Expected: `all ok`

- [ ] **Step 5: Restart backend and verify Gemini starts**

```bash
docker.exe compose -f /root/gju-library-ai/docker-compose.yml restart backend
sleep 5
docker.exe compose -f /root/gju-library-ai/docker-compose.yml logs backend --tail=8
```

Expected: `Application startup complete.` — no errors about GeminiClient or missing API key.

- [ ] **Step 6: Smoke-test Gemini in browser**

Open `http://localhost:3000`, log in, ask: **"what are the borrowing rules?"**
Expected: a coherent answer (may be faster than Ollama, no stack trace).

- [ ] **Step 7: Commit**

```bash
cd /root/gju-library-ai
git add backend/pyproject.toml
git commit -m "feat: add duckduckgo-search and trafilatura deps for Phase 3 web search"
```

---

### Task 2: `web_search` tool

**Files:**
- Create: `backend/app/tools/__init__.py`
- Create: `backend/app/tools/web_search.py`

**Interfaces:**
- Produces: `web_search(query: str, max_results: int = 5) -> str`
  Returns a formatted text block (one result per line: `Title\nURL\nSnippet\n---`).

- [ ] **Step 1: Create `backend/app/tools/__init__.py`**

Create an empty file at `backend/app/tools/__init__.py`:

```python
```

- [ ] **Step 2: Create `backend/app/tools/web_search.py`**

```python
from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web via DuckDuckGo. Returns formatted results text."""
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        return f"Search failed: {exc}"

    if not hits:
        return "No results found."

    lines: list[str] = []
    for h in hits:
        lines.append(h.get("title", ""))
        lines.append(h.get("href", ""))
        lines.append(h.get("body", ""))
        lines.append("---")
    return "\n".join(lines)
```

- [ ] **Step 3: Smoke-test inside container**

```bash
docker.exe compose -f /root/gju-library-ai/docker-compose.yml exec backend python -c "
from app.tools.web_search import web_search
print(web_search('GJU library Jordan director', max_results=2))
"
```

Expected: two results with titles, URLs, and snippets separated by `---`. If DDG rate-limits, retry once.

- [ ] **Step 4: Commit**

```bash
cd /root/gju-library-ai
git add backend/app/tools/__init__.py backend/app/tools/web_search.py
git commit -m "feat: add web_search tool (DuckDuckGo, no API key)"
```

---

### Task 3: `fetch_url` tool

**Files:**
- Create: `backend/app/tools/fetch_url.py`

**Interfaces:**
- Produces: `fetch_url(url: str) -> str`
  Returns cleaned plain text (up to 3 000 chars) or an error string if the URL is not in the allow-list.

- [ ] **Step 1: Create `backend/app/tools/fetch_url.py`**

```python
import httpx
import trafilatura

# Only GJU-related domains are permitted — prevents SSRF to arbitrary hosts.
_ALLOWED_DOMAINS = (
    "gju.edu.jo",
    "jopuls.org.jo",
    "openlibrary.org",
)

_MAX_CHARS = 3_000
_HEADERS = {"User-Agent": "GJULibraryAI/1.0 (+https://library.gju.edu.jo)"}


def fetch_url(url: str) -> str:
    """Fetch a URL and return extracted plain text (allow-listed domains only)."""
    if not any(domain in url for domain in _ALLOWED_DOMAINS):
        return f"URL not allowed. Only GJU and JOPULS domains are permitted."

    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True, headers=_HEADERS)
        resp.raise_for_status()
    except Exception as exc:
        return f"Fetch failed: {exc}"

    text = trafilatura.extract(resp.text) or resp.text
    return text[:_MAX_CHARS]
```

- [ ] **Step 2: Test allow-list enforcement inside container**

```bash
docker.exe compose -f /root/gju-library-ai/docker-compose.yml exec backend python -c "
from app.tools.fetch_url import fetch_url
# Should be blocked
print(fetch_url('https://example.com'))
# Should be allowed (will print page text)
print(fetch_url('https://www.gju.edu.jo/en/page/library')[:200])
"
```

Expected: first call prints `URL not allowed...`; second call prints up to 200 chars of GJU page text (or a fetch error if the URL 404s — that's fine).

- [ ] **Step 3: Commit**

```bash
cd /root/gju-library-ai
git add backend/app/tools/fetch_url.py
git commit -m "feat: add fetch_url tool with GJU domain allow-list"
```

---

### Task 4: Extend GeminiClient with raw generation (for tool-calling)

**Files:**
- Modify: `backend/app/llm/gemini_client.py`

**Interfaces:**
- Produces: `GeminiClient.generate_raw(contents, system_instruction, tools=None, temperature=0.2, max_tokens=800) -> types.GenerateContentResponse`
  Returns the SDK response object so the caller can inspect `candidates[0].content.parts` for text vs function-call.

- [ ] **Step 1: Add `generate_raw` to `GeminiClient`**

Open `backend/app/llm/gemini_client.py`. After the `stream` method (line 68), add:

```python
    def generate_raw(
        self,
        contents: list,
        system_instruction: str | None,
        tools: list | None = None,
        temperature: float = 0.2,
        max_tokens: int = 800,
    ):
        """Return the raw SDK GenerateContentResponse (used by the ReAct agent)."""
        from google.genai import types as _t

        config = _t.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools or [],
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        return self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=config,
        )
```

- [ ] **Step 2: Verify import still works**

```bash
docker.exe compose -f /root/gju-library-ai/docker-compose.yml exec backend python -c "
from app.llm.gemini_client import GeminiClient; print('ok')
"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
cd /root/gju-library-ai
git add backend/app/llm/gemini_client.py
git commit -m "feat: add generate_raw method to GeminiClient for tool-calling support"
```

---

### Task 5: ReAct agent

**Files:**
- Create: `backend/app/chat/react_agent.py`

**Interfaces:**
- Consumes:
  - `GeminiClient._build_contents(messages) -> (list[Content], str | None)`
  - `GeminiClient.generate_raw(contents, system_instruction, tools, temperature, max_tokens)`
  - `web_search(query) -> str` from `app.tools.web_search`
  - `fetch_url(url) -> str` from `app.tools.fetch_url`
  - `ChatMessage` from `app.llm.interface`
- Produces: `run_react(client: GeminiClient, messages: list[ChatMessage], max_calls: int = 3) -> str`
  Returns the final answer text after the tool-calling loop.

- [ ] **Step 1: Create `backend/app/chat/react_agent.py`**

```python
"""ReAct (Reason + Act) loop using Gemini function-calling."""
from __future__ import annotations

from google.genai import types

from app.llm.gemini_client import GeminiClient
from app.llm.interface import ChatMessage
from app.tools.fetch_url import fetch_url as _fetch_url
from app.tools.web_search import web_search as _web_search

# --------------------------------------------------------------------------- #
# Tool declarations sent to Gemini                                              #
# --------------------------------------------------------------------------- #

_WEB_SEARCH_DECL = types.FunctionDeclaration(
    name="web_search",
    description=(
        "Search the internet for current information about the GJU Library — "
        "staff contacts, hours, events, announcements, or any fact not found "
        "in the provided PASSAGES."
    ),
    parameters={
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "STRING",
                "description": (
                    "A concise search query. Prefer queries like "
                    "'GJU library director contact site:gju.edu.jo'."
                ),
            }
        },
        "required": ["query"],
    },
)

_FETCH_URL_DECL = types.FunctionDeclaration(
    name="fetch_url",
    description=(
        "Fetch and read the full text of a URL. "
        "Only works for gju.edu.jo, jopuls.org.jo, and openlibrary.org domains."
    ),
    parameters={
        "type": "OBJECT",
        "properties": {
            "url": {
                "type": "STRING",
                "description": "The full URL to fetch (must be from an allowed domain).",
            }
        },
        "required": ["url"],
    },
)

_TOOLS = types.Tool(function_declarations=[_WEB_SEARCH_DECL, _FETCH_URL_DECL])

# --------------------------------------------------------------------------- #
# Tool execution dispatch                                                       #
# --------------------------------------------------------------------------- #

_TOOL_FNS = {
    "web_search": lambda args: _web_search(args.get("query", ""), max_results=5),
    "fetch_url": lambda args: _fetch_url(args.get("url", "")),
}


def _execute_tool(name: str, args: dict) -> str:
    fn = _TOOL_FNS.get(name)
    if fn is None:
        return f"Unknown tool: {name}"
    try:
        return fn(args)
    except Exception as exc:
        return f"Tool error: {exc}"


# --------------------------------------------------------------------------- #
# Public entry point                                                            #
# --------------------------------------------------------------------------- #

def run_react(
    client: GeminiClient,
    messages: list[ChatMessage],
    max_calls: int = 3,
    temperature: float = 0.2,
    max_tokens: int = 600,
) -> str:
    """
    Run a ReAct tool-calling loop and return the final answer text.

    Converts ChatMessages to Gemini Contents, then loops:
      1. Call Gemini with tools available.
      2. If the model returns a function_call: execute the tool, append
         the result to the conversation, continue.
      3. If the model returns text: return it immediately.
    After max_calls tool calls, force a final answer without tools.
    """
    contents, system_instruction = client._build_contents(messages)
    calls_made = 0

    while calls_made < max_calls:
        response = client.generate_raw(
            contents,
            system_instruction,
            tools=[_TOOLS],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        candidate = response.candidates[0]
        model_content = candidate.content

        # Check every part — model may include text AND a function_call
        func_call_part = None
        for part in model_content.parts:
            if hasattr(part, "function_call") and part.function_call:
                func_call_part = part
                break

        if func_call_part is None:
            # Pure text response — we're done
            return "".join(
                p.text for p in model_content.parts if hasattr(p, "text") and p.text
            )

        # Execute the requested tool
        fc = func_call_part.function_call
        tool_result = _execute_tool(fc.name, dict(fc.args))
        calls_made += 1

        # Extend conversation: model turn (with function_call) + tool result
        contents.append(model_content)
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=fc.name,
                        response={"result": tool_result},
                    )
                ],
            )
        )

    # Max calls reached — force a final answer without tools
    final = client.generate_raw(
        contents,
        system_instruction,
        tools=None,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return "".join(
        p.text
        for p in final.candidates[0].content.parts
        if hasattr(p, "text") and p.text
    )
```

- [ ] **Step 2: Verify import inside container**

```bash
docker.exe compose -f /root/gju-library-ai/docker-compose.yml exec backend python -c "
from app.chat.react_agent import run_react; print('ok')
"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
cd /root/gju-library-ai
git add backend/app/chat/react_agent.py
git commit -m "feat: add ReAct agent with web_search + fetch_url tool-calling loop"
```

---

### Task 6: Wire ReAct into config, prompts, and pipeline

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/llm/prompts.py`
- Modify: `backend/app/chat/pipeline.py`
- Manual: `.env` (already has `ENABLE_WEB_SEARCH=true` from Task 1)

**Interfaces:**
- Consumes:
  - `run_react` from `app.chat.react_agent`
  - `get_settings().enable_web_search: bool`
  - `build_messages` (unchanged — also used by ReAct path)

- [ ] **Step 1: Add `enable_web_search` to `config.py`**

In `backend/app/config.py`, add one line after `dev_auth_stub`:

```python
    dev_auth_stub: bool = False
    enable_web_search: bool = False
```

- [ ] **Step 2: Add web-search instructions to system prompts in `prompts.py`**

In `backend/app/llm/prompts.py`, add this constant just above the `SYSTEM` dict (around line 194):

```python
_WEB_SEARCH_PREFIX = (
    "TOOLS AVAILABLE:\n"
    "You have two tools: web_search(query) and fetch_url(url).\n"
    "Use web_search when the PASSAGES do not contain the answer — especially for "
    "current staff contacts, holiday closures, events, or live catalog lookups.\n"
    "Use fetch_url to read a specific GJU or JOPULS page when a search result "
    "URL would give a better answer.\n"
    "Prefer PASSAGES when they have the answer. Only call tools when they don't.\n\n"
)
```

Then add a helper function just below that constant:

```python
def build_react_system(lang: str) -> str:
    """Return the system prompt with web-search tool instructions prepended."""
    return _WEB_SEARCH_PREFIX + SYSTEM.get(lang, SYSTEM["en"])
```

- [ ] **Step 3: Wire ReAct loop into `pipeline.py`**

Open `backend/app/chat/pipeline.py`. 

Add imports at the top (after the existing `from app.llm.prompts import ...` line):

```python
from app.llm.prompts import build_book_card, build_messages, _fetch_book_info, _opac_url, build_react_system
```

Also add:

```python
import re as _re
```

is already there; add these two new imports right after the existing import block:

```python
from app.config import get_settings
```

(already present — leave it) and:

```python
# Imported lazily inside the function to avoid import error when Gemini is not configured:
# from app.chat.react_agent import run_react
```

No, let's do it differently — add the import at the top level but guard it:

After the existing `from app.config import get_settings` line, add:

```python
_react_available = False
try:
    from app.chat.react_agent import run_react as _run_react
    _react_available = True
except ImportError:
    pass
```

Now in **`stream_chat`**, find this block (around line 126–133):

```python
    history = _load_history(db, conv_id)
    msgs = build_messages(query, res, lang=route.lang, history=history)
    pieces: list[str] = []
    llm_t0 = time.perf_counter()
    for piece in llm.stream(msgs, temperature=0.2, max_tokens=350):
        pieces.append(piece)
        yield f"data: {_json.dumps({'type': 'token', 'text': piece})}\n\n"
    llm_latency = int((time.perf_counter() - llm_t0) * 1000)
    answer_raw = "".join(pieces)
```

Replace it with:

```python
    history = _load_history(db, conv_id)
    msgs = build_messages(query, res, lang=route.lang, history=history)
    pieces: list[str] = []
    llm_t0 = time.perf_counter()

    if _react_available and s.enable_web_search and hasattr(llm, "generate_raw"):
        # Inject web-search system prompt then run ReAct loop (no streaming)
        for i, m in enumerate(msgs):
            if m.role == "system":
                from app.llm.interface import ChatMessage as _CM
                msgs[i] = _CM("system", build_react_system(route.lang))
                break
        answer_raw = _run_react(llm, msgs)
        # Emit the full answer as a single token so the SSE contract is met
        yield f"data: {_json.dumps({'type': 'token', 'text': answer_raw})}\n\n"
    else:
        for piece in llm.stream(msgs, temperature=0.2, max_tokens=350):
            pieces.append(piece)
            yield f"data: {_json.dumps({'type': 'token', 'text': piece})}\n\n"
        answer_raw = "".join(pieces)

    llm_latency = int((time.perf_counter() - llm_t0) * 1000)
```

Now in **`run_chat`**, find this block (around line 232–236):

```python
    history = _load_history(db, conv_id)
    msgs = build_messages(query, res, lang=route.lang, history=history)
    llm_resp = llm.complete(msgs, temperature=0.2, max_tokens=350)

    # Prepend Python-generated book cards so the full answer includes the card
    answer_raw = llm_resp.text
```

Replace with:

```python
    history = _load_history(db, conv_id)
    msgs = build_messages(query, res, lang=route.lang, history=history)

    if _react_available and s.enable_web_search and hasattr(llm, "generate_raw"):
        for i, m in enumerate(msgs):
            if m.role == "system":
                from app.llm.interface import ChatMessage as _CM
                msgs[i] = _CM("system", build_react_system(route.lang))
                break
        answer_raw = _run_react(llm, msgs)
        llm_latency_ms = 0  # ReAct doesn't expose per-call latency simply
    else:
        llm_resp = llm.complete(msgs, temperature=0.2, max_tokens=350)
        answer_raw = llm_resp.text
        llm_latency_ms = llm_resp.latency_ms
```

Also update the `query_log` INSERT in `run_chat` to use `llm_latency_ms` (replacing `llm_resp.latency_ms`):

Find:
```python
            "lat": llm_resp.latency_ms,
```
Replace with:
```python
            "lat": llm_latency_ms,
```

And update the `model` field — find:
```python
            "model": llm_resp.model,
```
Replace with:
```python
            "model": getattr(llm, "_model", "unknown"),
```

- [ ] **Step 4: Restart backend and verify startup**

```bash
docker.exe compose -f /root/gju-library-ai/docker-compose.yml restart backend
sleep 6
docker.exe compose -f /root/gju-library-ai/docker-compose.yml logs backend --tail=10
```

Expected: `Application startup complete.` — no import errors.

- [ ] **Step 5: Integration test — web search triggered**

In the browser at `http://localhost:3000`, ask:

**"Who is the current head of the GJU Library?"**

Expected: The answer includes laith.alnaser@gju.edu.jo (from RAG corpus) OR a fresh web-sourced answer from gju.edu.jo. Check backend logs to see if a tool call was made:

```bash
docker.exe compose -f /root/gju-library-ai/docker-compose.yml logs backend --tail=20
```

Look for any errors. If you see `Tool error:` in logs, note what failed.

- [ ] **Step 6: Integration test — RAG answer not overridden**

Ask: **"What are the borrowing rules for graduate students?"**

Expected: Answer comes from PASSAGES (no web search needed) — should be fast and cite [Pxx].

- [ ] **Step 7: Commit**

```bash
cd /root/gju-library-ai
git add backend/app/config.py backend/app/llm/prompts.py backend/app/chat/pipeline.py
git commit -m "feat: wire Phase 3 ReAct web-search loop into pipeline with ENABLE_WEB_SEARCH flag"
```

---

### Task 7: Push and verify

- [ ] **Step 1: Push branch**

```bash
cd /root/gju-library-ai
git push
```

- [ ] **Step 2: Final end-to-end test matrix**

| Question | Expected behaviour |
|----------|--------------------|
| "Who is the GJU library director?" | Name + email (RAG or web) |
| "Is the library open on Eid Al-Adha?" | Web search triggered (not in corpus) |
| "Show me books about software engineering" | Book cards + RAG, no web search |
| "How do I access Turnitin?" | RAG answer with Nesreen.Malkawi email |
| "fetch https://evil.com" | fetch_url returns "URL not allowed" |

Verify each by asking in the browser and checking `docker.exe compose logs backend --tail=30`.

- [ ] **Step 3: Final commit if any fixes were needed**

```bash
cd /root/gju-library-ai
git add -p
git commit -m "fix: web search integration adjustments after end-to-end testing"
git push
```
