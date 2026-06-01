# Gemini Provider Design

**Date:** 2026-06-01
**Goal:** Add Gemini 2.0 Flash as a swappable LLM provider behind the existing `LLMClient` protocol.

## Context

The backend already has a `LLMClient` Protocol (`backend/app/llm/interface.py`) and a `llm_provider` config field. Only `OllamaClient` is implemented today. The `get_llm()` factory in `deps.py` raises `RuntimeError` for any provider other than `"ollama"`.

## Changes

### 1. `backend/app/llm/gemini_client.py` (new)

Implements `LLMClient` using `google-genai` SDK (`google.genai`).

**Message conversion:** The `build_messages()` function returns `list[ChatMessage]` with roles `system | user | assistant`. Gemini's API separates system prompts from conversation turns:
- Messages with `role == "system"` → joined as `system_instruction` in `GenerateContentConfig`
- Remaining messages → `contents` list with `role="user"` or `role="model"` (Gemini uses `"model"` not `"assistant"`)

**`complete()`:** Calls `client.models.generate_content(model, contents, config)`, returns `ChatResponse(text, model, latency_ms)`.

**`stream()`:** Calls `client.models.generate_content_stream(...)`, yields `chunk.text` for each non-empty chunk.

### 2. `backend/app/config.py`

Add two fields to `Settings`:
```python
gemini_api_key: str = ""
gemini_model: str = "gemini-2.0-flash"
```

### 3. `backend/app/deps.py`

Add branch in `get_llm()`:
```python
elif s.llm_provider == "gemini":
    from app.llm.gemini_client import GeminiClient
    return GeminiClient(api_key=s.gemini_api_key, model=s.gemini_model)
```

### 4. `pyproject.toml`

Add `google-genai>=1.0` to `dependencies`.

### 5. `.env` (user-managed, not committed)

User adds:
```
LLM_PROVIDER=gemini
GEMINI_API_KEY=<key>
GEMINI_MODEL=gemini-2.0-flash
```

To revert to Ollama: set `LLM_PROVIDER=ollama`.

## Out of Scope

- No changes to pipeline, render, retrieval, or tests
- No streaming fallback or retry logic — Gemini API errors propagate as-is
- No model validation — invalid model names fail at request time with a clear API error
