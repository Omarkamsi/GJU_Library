# Gemini Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Gemini 2.0 Flash as a swappable LLM provider behind the existing `LLMClient` protocol.

**Architecture:** Create `GeminiClient` in `backend/app/llm/gemini_client.py` implementing the `LLMClient` Protocol. Wire it into the `get_llm()` factory in `deps.py` via a new `llm_provider == "gemini"` branch. Provider is selected at runtime via `LLM_PROVIDER` env var — no code changes needed to switch back to Ollama.

**Tech Stack:** Python `google-genai>=1.0` SDK, existing `LLMClient` Protocol, pydantic-settings.

---

### Task 1: Add google-genai dependency

**Files:**
- Modify: `backend/pyproject.toml`

No test needed — this is a dependency declaration.

- [ ] **Step 1: Add google-genai to pyproject.toml**

In `backend/pyproject.toml`, add `"google-genai>=1.0"` to the `dependencies` list:

```toml
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
  "ollama>=0.4",
  "tenacity>=9.0",
  "google-genai>=1.0",
]
```

- [ ] **Step 2: Install in the running backend container**

```bash
docker compose exec backend pip install google-genai
```

Expected: `Successfully installed google-genai-...` (or "already satisfied").

- [ ] **Step 3: Verify import**

```bash
docker compose exec backend python -c "from google import genai; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add backend/pyproject.toml
git commit -m "feat: add google-genai dependency for Gemini provider"
```

---

### Task 2: GeminiClient

**Files:**
- Create: `backend/app/llm/gemini_client.py`

No unit tests — `GeminiClient` is a thin SDK adapter with no business logic, exactly like `OllamaClient` which also has no unit tests. Integration is verified by running the chatbot in Task 3.

- [ ] **Step 1: Create gemini_client.py**

Create `backend/app/llm/gemini_client.py`:

```python
import time
from typing import Iterator

from google import genai
from google.genai import types

from .interface import ChatMessage, ChatResponse, LLMClient


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def _build_contents(
        self, messages: list[ChatMessage]
    ) -> tuple[list[types.Content], str | None]:
        """Split system messages into system_instruction; convert the rest to Content objects."""
        system_parts = [m.content for m in messages if m.role == "system"]
        system_instruction = "\n\n".join(system_parts) if system_parts else None

        contents = [
            types.Content(
                role="user" if m.role == "user" else "model",
                parts=[types.Part.from_text(text=m.content)],
            )
            for m in messages
            if m.role != "system"
        ]
        return contents, system_instruction

    def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> ChatResponse:
        contents, system_instruction = self._build_contents(messages)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        start = time.perf_counter()
        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=config,
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        return ChatResponse(
            text=response.text or "",
            model=self._model,
            latency_ms=elapsed,
        )

    def stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> Iterator[str]:
        contents, system_instruction = self._build_contents(messages)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        for chunk in self._client.models.generate_content_stream(
            model=self._model,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/llm/gemini_client.py
git commit -m "feat: add GeminiClient implementing LLMClient protocol"
```

---

### Task 3: Wire config, deps, and env

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/deps.py`
- Modify: `.env` (manual step — user adds key)

- [ ] **Step 1: Add Gemini settings to config.py**

In `backend/app/config.py`, add two fields to the `Settings` class after the `ollama_keep_alive` line:

```python
    ollama_keep_alive: str = "30m"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
```

- [ ] **Step 2: Add Gemini branch to get_llm() in deps.py**

In `backend/app/deps.py`, update `get_llm()` to:

```python
def get_llm() -> LLMClient:
    s = get_settings()
    if s.llm_provider == "ollama":
        return OllamaClient(host=s.ollama_host, model=s.ollama_model, keep_alive=s.ollama_keep_alive)
    if s.llm_provider == "gemini":
        from app.llm.gemini_client import GeminiClient
        return GeminiClient(api_key=s.gemini_api_key, model=s.gemini_model)
    raise RuntimeError(f"Unknown LLM_PROVIDER: {s.llm_provider}")
```

- [ ] **Step 3: Add env vars to .env**

Open the `.env` file in the project root and add:

```
LLM_PROVIDER=gemini
GEMINI_API_KEY=<your-key-here>
GEMINI_MODEL=gemini-2.0-flash
```

Replace `<your-key-here>` with the actual Gemini API key from Google AI Studio.

- [ ] **Step 4: Restart backend to pick up new env**

```bash
docker compose restart backend
```

Wait ~5 seconds, then check it started cleanly:

```bash
docker compose logs backend --tail=5
```

Expected: no errors, uvicorn reports `Application startup complete`.

- [ ] **Step 5: Smoke test in browser**

Go to `http://localhost:3000`, log in, and ask: **"what are the borrowing rules for graduate students"**

Expected: answer arrives (may be faster than Ollama), no errors in `docker compose logs backend --tail=10`.

- [ ] **Step 6: Commit code changes**

```bash
git add backend/app/config.py backend/app/deps.py
git commit -m "feat: wire Gemini provider into config and get_llm factory"
```

Note: `.env` is gitignored and must not be committed (contains the API key).
