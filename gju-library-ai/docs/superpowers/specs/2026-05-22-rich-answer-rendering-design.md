# Rich Answer Rendering Design

**Date:** 2026-05-22  
**Branch:** gju-library-ai-m0  
**Status:** Approved

## Problem

AI responses render as plain text in the chat UI. The book card format (title, author, genre, call number, year, OPAC link) is produced by the LLM as an emoji-labeled text block, but the frontend displays it as a raw string with no structure. Non-book answers (FAQs, borrowing rules, services) also render as plain text with no bold, bullets, or line breaks.

## Goal

1. Book catalog answers render as structured visual cards with a tracked OPAC link button.
2. All other answers render with markdown formatting (bold, bullets, line breaks).

## Constraints

- No paid LLM API — stays on local `qwen2.5:7b-instruct` via Ollama.
- No changes to the LLM prompt format — the card block the model already produces is the source of truth.

## Approach: Backend structured segment + frontend markdown

`render.py` detects the LLM's card block pattern and converts it into a typed `book_card` segment. The frontend renders `book_card` segments as `<BookCard>` components and `text` segments with `react-markdown`.

Rejected alternatives:
- **Frontend regex extraction**: fragile, hard to test, no typing.
- **JSON structured output from LLM**: `qwen2.5:7b` unreliable at producing valid JSON under a complex prompt.

## Data Flow

```
LLM streams tokens → frontend shows raw text live
                  ↓ (on done)
render_answer(answer_raw)
  → CARD_RE matches each book block
  → book_card segment (typed fields + click_id)
  → remaining text → text segments
done SSE event → frontend replaces stream with structured segments
```

The `render_answer` function already runs on the complete response after streaming finishes. Card detection fits naturally here alongside the existing `[P\d+]` and `[DB:slug]` token parsing.

**Streaming UX note:** During streaming, the frontend shows raw token text (emojis + labels as plain text). When the `done` event arrives, `AnswerSegments` replaces the raw text with structured segments including `<BookCard>`. This transition is already how citation superscripts and database links work — no extra handling needed.

## Backend Changes

### `app/chat/pipeline.py`

Bump `max_tokens` from `300` to `800` in both `run_chat` and `stream_chat` call sites. A single book card is ~80 tokens; 5 books = ~400 tokens, which exceeds the current limit and truncates answers.

### `app/chat/render.py`

Add `CARD_RE` regex matching the card block the LLM produces:

```
Yes, GJU Library holds this book in its physical collection [P139].
📖 Title: <title>
✍️ Author: <author>
🏷️ Genre / Subject: <genre>
🔢 Call Number: <call_number>
📅 Publication Year: <year>
🔍 Check availability & shelf location: <url>
```

For each match:
- Extract passage IDs from `[P\d+]` on the confirmation line.
- Parse each labeled field (title, author, genre, call_number, year, opac_url).
- Generate a `click_id` and register a `PendingClick` (target_type `"external"`, target_url = opac_url) so click tracking works.
- Emit a `book_card` segment dict.
- The confirmation line and field lines are consumed; surrounding text becomes `text` segments.

Missing fields (model omits a line) default to empty string `""`.

New segment shape:
```python
{
    "type": "book_card",
    "title": str,
    "author": str,
    "genre": str,
    "call_number": str,
    "year": str,
    "opac_url": str,
    "passage_ids": list[int],
    "click_id": str,
}
```

## Frontend Changes

### `package.json`

Add dependencies: `react-markdown`, `remark-gfm`.

### `lib/types.ts`

Add `BookCardSegment` type matching the backend segment shape above. Update the `Segment` union type.

### `app/chat/components/BookCard.tsx`

New component. Layout:
- White card, subtle border (`border-gju-ink/10`), rounded corners — matches existing chat bubble style.
- Bold title with `📖` prefix as card header with GJU blue accent line.
- Rows for author, genre, call number, year with their emoji labels.
- `TrackedLink` button for OPAC link (reuses existing tracked-click infrastructure).
- Passage ID superscripts below the card (reuses existing `passage_ref` chip style).
- Multiple books: cards stack vertically with `gap-3`.

### `app/chat/components/AnswerSegments.tsx`

- `text` segments: replace `<span>{s.value}</span>` with `<ReactMarkdown remarkPlugins={[remarkGfm]}>`.
- `book_card` segments: render `<BookCard>`.
- Other segment types (`passage_ref`, `link`) unchanged.

## Testing

### `backend/tests/unit/test_render.py`

Unit tests for `render_answer` with book card inputs:

| Test | Input | Expected |
|---|---|---|
| Single card | One card block | One `book_card` segment, correct fields |
| Two cards | Two consecutive blocks | Two `book_card` segments |
| Card + text | Card then paragraph | `book_card` + `text` segments |
| Missing field | Card with no year line | `book_card` with `year: ""` |
| Year "Not listed" | `📅 Publication Year: Not listed` | `year: "Not listed"` |

No automated frontend tests — visual verification in browser after implementation.

## Files Changed

| File | Change |
|---|---|
| `backend/app/chat/pipeline.py` | `max_tokens` 300 → 800 (2 call sites) |
| `backend/app/chat/render.py` | `CARD_RE` + `book_card` segment extraction |
| `frontend/lib/types.ts` | Add `BookCardSegment`, update `Segment` union |
| `frontend/app/chat/components/BookCard.tsx` | New component |
| `frontend/app/chat/components/AnswerSegments.tsx` | Handle `book_card`, markdown for text |
| `frontend/package.json` | Add `react-markdown`, `remark-gfm` |
| `backend/tests/unit/test_render.py` | New unit tests |
