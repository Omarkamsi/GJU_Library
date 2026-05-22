# Rich Answer Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render book catalog answers as structured visual cards and all other answers with markdown formatting.

**Architecture:** Backend `render.py` pre-scans LLM output with a regex to extract book card blocks into typed `book_card` segments. Frontend renders `book_card` segments as `<BookCard>` components and `text` segments with `react-markdown`. The streaming fallback (raw text during stream → structured cards on `done`) requires no extra work — this is how the existing `done` event already replaces streaming text.

**Tech Stack:** Python `re` module (backend), React + Tailwind CSS, `react-markdown` + `remark-gfm` (frontend), pytest (tests).

---

### Task 1: Bump max_tokens

**Files:**
- Modify: `backend/app/chat/pipeline.py:36` and `:126`

A single book card is ~80 tokens. Five books ≈ 400 tokens, exceeding the current 300-token limit and truncating answers. No test needed — this is a config value change with no branching logic.

- [ ] **Step 1: Update both call sites in pipeline.py**

In `backend/app/chat/pipeline.py`, change `max_tokens=300` → `max_tokens=800` at both call sites:

Line ~36 (in `stream_chat`):
```python
    for piece in llm.stream(msgs, temperature=0.2, max_tokens=800):
```

Line ~126 (in `run_chat`):
```python
    llm_resp = llm.complete(msgs, temperature=0.2, max_tokens=800)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/chat/pipeline.py
git commit -m "feat: bump max_tokens 300→800 to fit multi-book card answers"
```

---

### Task 2: Backend — book_card segment extraction (TDD)

**Files:**
- Modify: `backend/app/chat/render.py`
- Modify: `backend/tests/unit/test_render.py`

The LLM produces a card block in this exact format (from the system prompt template):

```
Yes, GJU Library holds this book in its physical collection [P139].
📖 Title: The seduction of unreason
✍️ Author: Wolin, Richard.
🏷️ Genre / Subject: Political Science.
🔢 Call Number: JC481.W65 2004
📅 Publication Year: 2004
🔍 Check availability & shelf location: http://hip.jopuls.org.jo/web/gju
```

`render_answer` pre-scans the full response for card blocks, converts each to a `book_card` segment dict + `PendingClick`, then runs the existing token loop on the remaining text.

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/unit/test_render.py`:

```python
CARD_RAW = (
    "Yes, GJU Library holds this book in its physical collection [P139].\n"
    "📖 Title: The seduction of unreason\n"
    "✍️ Author: Wolin, Richard.\n"
    "🏷️ Genre / Subject: Political Science.\n"
    "🔢 Call Number: JC481.W65 2004\n"
    "📅 Publication Year: 2004\n"
    "🔍 Check availability & shelf location: http://hip.jopuls.org.jo/web/gju"
)


def test_book_card_segment_extracted():
    out = render_answer(
        RenderInput(answer_raw=CARD_RAW, databases=[], passages=[139], base_url="http://x")
    )
    cards = [s for s in out.segments if s["type"] == "book_card"]
    assert len(cards) == 1
    c = cards[0]
    assert c["title"] == "The seduction of unreason"
    assert c["author"] == "Wolin, Richard"
    assert c["genre"] == "Political Science"
    assert c["call_number"] == "JC481.W65 2004"
    assert c["year"] == "2004"
    assert c["opac_url"] == "http://hip.jopuls.org.jo/web/gju"
    assert c["passage_ids"] == [139]
    assert "click_id" in c


def test_book_card_opac_click_registered():
    out = render_answer(
        RenderInput(answer_raw=CARD_RAW, databases=[], passages=[139], base_url="http://x")
    )
    cards = [s for s in out.segments if s["type"] == "book_card"]
    cid = cards[0]["click_id"]
    assert any(
        cl.id == cid and cl.target_type == "external"
        and cl.target_url == "http://hip.jopuls.org.jo/web/gju"
        for cl in out.clicks
    )


def test_two_consecutive_book_cards():
    two = CARD_RAW + "\n\n" + CARD_RAW.replace("[P139]", "[P200]").replace(
        "seduction of unreason", "second book"
    )
    out = render_answer(
        RenderInput(answer_raw=two, databases=[], passages=[139, 200], base_url="http://x")
    )
    cards = [s for s in out.segments if s["type"] == "book_card"]
    assert len(cards) == 2
    assert cards[0]["passage_ids"] == [139]
    assert cards[1]["passage_ids"] == [200]


def test_book_card_with_text_before_and_after():
    wrapped = "Here is what I found:\n\n" + CARD_RAW + "\n\nLet me know if you need more."
    out = render_answer(
        RenderInput(answer_raw=wrapped, databases=[], passages=[139], base_url="http://x")
    )
    types = [s["type"] for s in out.segments]
    assert "book_card" in types
    assert types[0] == "text"
    assert types[-1] == "text"


def test_book_card_year_not_listed():
    raw = CARD_RAW.replace("📅 Publication Year: 2004", "📅 Publication Year: Not listed")
    out = render_answer(
        RenderInput(answer_raw=raw, databases=[], passages=[139], base_url="http://x")
    )
    card = next(s for s in out.segments if s["type"] == "book_card")
    assert card["year"] == "Not listed"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
docker compose exec backend python -m pytest tests/unit/test_render.py -k "book_card" -v
```

Expected: 5 failures — `AssertionError` (no `book_card` segments yet).

- [ ] **Step 3: Implement CARD_RE and extraction in render.py**

Replace the full content of `backend/app/chat/render.py` with:

```python
import re
import secrets
from dataclasses import dataclass
from typing import Any

CLICK_ID_LEN = 12


@dataclass
class PendingClick:
    id: str
    target_type: str  # database | external | passage
    target_ref: str | None
    target_url: str


@dataclass
class RenderInput:
    answer_raw: str
    databases: list[tuple[str, str, str]]  # (slug, name, url)
    passages: list[int]
    base_url: str


@dataclass
class RenderOutput:
    segments: list[dict[str, Any]]
    answer_text: str
    clicks: list[PendingClick]


DB_TOKEN_RE = re.compile(r"\[DB:([a-z0-9_-]+)\]")
# Tolerate model misbehavior: [P12], [P12, P34], [P 12, P34], [P12،P34] (Arabic comma).
P_TOKEN_RE = re.compile(r"\[P\s*(\d+(?:\s*[,،]\s*P?\s*\d+)*)\]")
URL_RE = re.compile(r"https?://[^\s)\]]+")

# Matches the book card block the LLM produces per the system prompt template.
# Uses [^\n]*? after each emoji to absorb optional variation selectors (U+FE0F).
CARD_RE = re.compile(
    r"Yes,\s+GJU Library holds this book[^\n]*?\[P(\d+)\][^\n]*\n"
    r"\s*📖[^\n]*?Title:\s*([^\n]+)\n"
    r"\s*✍[^\n]*?Author:\s*([^\n]+)\n"
    r"\s*🏷[^\n]*?Genre[^\n]*?Subject:\s*([^\n]+)\n"
    r"\s*🔢[^\n]*?Call Number:\s*([^\n]+)\n"
    r"\s*📅[^\n]*?Publication Year:\s*([^\n]+)\n"
    r"\s*🔍[^\n]*?Check availability[^\n]*?:\s*(https?://[^\s\n]+)",
    re.UNICODE,
)


def _new_click_id() -> str:
    return "c_" + secrets.token_urlsafe(9)[:CLICK_ID_LEN]


def _push_text(segments: list[dict], buf: str) -> None:
    if not buf:
        return
    if segments and segments[-1]["type"] == "text":
        segments[-1]["value"] += buf
    else:
        segments.append({"type": "text", "value": buf})


def render_answer(inp: RenderInput) -> RenderOutput:
    # Pre-pass: locate all book card blocks
    _card_spans: dict[int, tuple[int, dict, PendingClick]] = {}
    for m in CARD_RE.finditer(inp.answer_raw):
        cid = _new_click_id()
        opac_url = m.group(7).strip()
        _card_spans[m.start()] = (
            m.end(),
            {
                "type": "book_card",
                "title": m.group(2).strip().rstrip(" ."),
                "author": m.group(3).strip().rstrip(" ."),
                "genre": m.group(4).strip().rstrip(" ."),
                "call_number": m.group(5).strip(),
                "year": m.group(6).strip().rstrip(" ."),
                "opac_url": opac_url,
                "passage_ids": [int(m.group(1))],
                "click_id": cid,
            },
            PendingClick(cid, "external", None, opac_url),
        )

    db_by_slug = {slug: (name, url) for slug, name, url in inp.databases}
    known_passages = set(inp.passages)
    segments: list[dict[str, Any]] = []
    clicks: list[PendingClick] = []

    s = inp.answer_raw
    pos = 0
    while pos < len(s):
        # Card takes priority over all other token types
        if pos in _card_spans:
            end, seg, click = _card_spans[pos]
            segments.append(seg)
            clicks.append(click)
            pos = end
            continue

        next_card = min((k for k in _card_spans if k > pos), default=len(s))

        m_db = DB_TOKEN_RE.search(s, pos)
        m_p = P_TOKEN_RE.search(s, pos)
        m_u = URL_RE.search(s, pos)
        # Only consider matches before the next card block
        candidates = [m for m in (m_db, m_p, m_u) if m and m.start() < next_card]
        if not candidates:
            _push_text(segments, s[pos:next_card])
            pos = next_card
            continue
        m = min(candidates, key=lambda x: x.start())
        if m.start() > pos:
            _push_text(segments, s[pos:m.start()])

        if m is m_db:
            slug = m.group(1)
            if slug in db_by_slug:
                name, url = db_by_slug[slug]
                cid = _new_click_id()
                clicks.append(PendingClick(cid, "database", slug, url))
                segments.append(
                    {
                        "type": "link",
                        "click_id": cid,
                        "label": name,
                        "kind": "database",
                        "ref": slug,
                    }
                )
            # unknown slug → silently drop the token
        elif m is m_p:
            ids = [int(x) for x in re.findall(r"\d+", m.group(1))]
            any_pushed = False
            for pid in ids:
                if pid in known_passages:
                    segments.append({"type": "passage_ref", "passage_id": pid})
                    any_pushed = True
            if not any_pushed:
                _push_text(segments, m.group(0))
        else:  # raw URL
            url = m.group(0)
            cid = _new_click_id()
            clicks.append(PendingClick(cid, "external", None, url))
            segments.append(
                {
                    "type": "link",
                    "click_id": cid,
                    "label": url,
                    "kind": "external",
                    "ref": None,
                }
            )
        pos = m.end()

    return RenderOutput(segments=segments, answer_text=inp.answer_raw, clicks=clicks)
```

- [ ] **Step 4: Run all render tests**

```bash
docker compose exec backend python -m pytest tests/unit/test_render.py -v
```

Expected: all 10 tests PASS (5 existing + 5 new).

- [ ] **Step 5: Commit**

```bash
git add backend/app/chat/render.py backend/tests/unit/test_render.py
git commit -m "feat: extract book_card segments from LLM card block output"
```

---

### Task 3: Frontend types

**Files:**
- Modify: `frontend/lib/types.ts`

Add the `BookCardSegment` type and extend the `Segment` union.

- [ ] **Step 1: Update types.ts**

Replace the content of `frontend/lib/types.ts` with:

```typescript
export type Lang = "en" | "ar" | "de";

export type BookCardSegment = {
  type: "book_card";
  title: string;
  author: string;
  genre: string;
  call_number: string;
  year: string;
  opac_url: string;
  passage_ids: number[];
  click_id: string;
};

export type Segment =
  | { type: "text"; value: string }
  | { type: "passage_ref"; passage_id: number }
  | {
      type: "link";
      click_id: string;
      label: string;
      kind: "database" | "external";
      ref: string | null;
    }
  | BookCardSegment;

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

- [ ] **Step 2: Verify TypeScript compiles**

```bash
docker compose exec frontend npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/types.ts
git commit -m "feat: add BookCardSegment type to Segment union"
```

---

### Task 4: Install react-markdown

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Install dependencies**

```bash
docker compose exec frontend npm install react-markdown remark-gfm
```

Expected output ends with: `added N packages` (no errors).

- [ ] **Step 2: Verify import works**

```bash
docker compose exec frontend node -e "require('react-markdown'); require('remark-gfm'); console.log('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat: add react-markdown + remark-gfm dependencies"
```

---

### Task 5: BookCard component

**Files:**
- Create: `frontend/app/chat/components/BookCard.tsx`

Renders a `BookCardSegment` as a structured card. Uses the `/api/go/<click_id>` URL pattern directly (same as TrackedLink uses internally) to avoid modifying the existing TrackedLink component.

- [ ] **Step 1: Create BookCard.tsx**

Create `frontend/app/chat/components/BookCard.tsx`:

```tsx
import type { BookCardSegment } from "@/lib/types";

type Props = {
  segment: BookCardSegment;
};

export function BookCard({ segment }: Props) {
  return (
    <div className="rounded-xl border border-gju-ink/10 bg-white overflow-hidden my-2 shadow-sm">
      {/* Title header */}
      <div className="border-b border-gju-ink/10 px-4 py-3 bg-gju-blue/5">
        <p className="font-semibold text-gju-ink text-[14px] leading-snug">
          📖 {segment.title}
        </p>
      </div>

      {/* Fields */}
      <div className="px-4 py-3 space-y-1.5 text-[13px] text-gju-ink/80">
        {segment.author && (
          <p>
            <span className="font-medium text-gju-ink">✍️ Author:</span>{" "}
            {segment.author}
          </p>
        )}
        {segment.genre && (
          <p>
            <span className="font-medium text-gju-ink">🏷️ Genre / Subject:</span>{" "}
            {segment.genre}
          </p>
        )}
        {segment.call_number && (
          <p>
            <span className="font-medium text-gju-ink">🔢 Call Number:</span>{" "}
            {segment.call_number}
          </p>
        )}
        {segment.year && (
          <p>
            <span className="font-medium text-gju-ink">📅 Year:</span>{" "}
            {segment.year}
          </p>
        )}
      </div>

      {/* OPAC link */}
      <div className="px-4 pb-3">
        <a
          href={`/api/go/${encodeURIComponent(segment.click_id)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] font-medium bg-gju-blue text-white hover:bg-gju-blue/90 transition-colors"
        >
          Check availability &amp; shelf location →
        </a>
      </div>

      {/* Passage citation chips */}
      {segment.passage_ids.length > 0 && (
        <div className="px-4 pb-2 flex gap-1 flex-wrap">
          {segment.passage_ids.map((pid) => (
            <sup
              key={pid}
              className="inline-flex items-center px-1.5 py-0.5 rounded-md text-[10px] font-mono bg-gju-blue-soft text-gju-blue ring-1 ring-gju-blue/10"
            >
              P{pid}
            </sup>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
docker compose exec frontend npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/chat/components/BookCard.tsx
git commit -m "feat: add BookCard component for catalog answer rendering"
```

---

### Task 6: Wire up AnswerSegments — book_card + markdown

**Files:**
- Modify: `frontend/app/chat/components/AnswerSegments.tsx`

Two changes:
1. Handle `book_card` segments → render `<BookCard>`.
2. `text` segments → render with `ReactMarkdown` instead of plain `<span>`.
3. Change root wrapper from `<span>` to `<>` (fragment) — `ReactMarkdown` emits block elements (`<p>`) which are invalid inside `<span>`.

- [ ] **Step 1: Update AnswerSegments.tsx**

Replace the full content of `frontend/app/chat/components/AnswerSegments.tsx` with:

```tsx
"use client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Segment } from "@/lib/types";
import { TrackedLink } from "./TrackedLink";
import { BookCard } from "./BookCard";

type Citation = { id: number; title: string | null; source: string };

export function AnswerSegments({
  segments,
  citations,
}: {
  segments: Segment[];
  citations?: Citation[];
}) {
  const byId = new Map((citations ?? []).map((c) => [c.id, c]));
  return (
    <>
      {segments.map((s, i) => {
        if (s.type === "text") {
          return (
            <ReactMarkdown
              key={i}
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => (
                  <span className="block">{children}</span>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside my-1 space-y-0.5">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside my-1 space-y-0.5">
                    {children}
                  </ol>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold">{children}</strong>
                ),
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gju-blue underline decoration-dotted underline-offset-2"
                  >
                    {children}
                  </a>
                ),
              }}
            >
              {s.value}
            </ReactMarkdown>
          );
        }
        if (s.type === "book_card") {
          return <BookCard key={i} segment={s} />;
        }
        if (s.type === "passage_ref") {
          const c = byId.get(s.passage_id);
          const title = c ? c.title || c.source : `Passage ${s.passage_id}`;
          return (
            <sup
              key={i}
              className="inline-flex items-center mx-0.5 px-1.5 py-0.5 rounded-md text-[10px] font-mono bg-gju-blue-soft text-gju-blue ring-1 ring-gju-blue/10 cursor-help align-baseline"
              title={title}
            >
              P{s.passage_id}
            </sup>
          );
        }
        return <TrackedLink key={i} clickId={s.click_id} label={s.label} kind={s.kind} />;
      })}
    </>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
docker compose exec frontend npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Restart frontend to pick up new dependencies**

```bash
docker compose restart frontend
```

Wait ~10 seconds for Next.js to rebuild.

- [ ] **Step 4: Smoke test in browser**

1. Go to `http://localhost:3000`, log in.
2. Ask: **"do you have the book seduction of unreason"**
3. Expected: a structured card renders with title, author, genre, call number, year, and a blue "Check availability" button.
4. Ask: **"what are the borrowing rules for graduate students"**
5. Expected: bullet points or bold text rendered (not raw `**` asterisks).

- [ ] **Step 5: Commit**

```bash
git add frontend/app/chat/components/AnswerSegments.tsx
git commit -m "feat: render book_card segments as BookCard + markdown for text"
```
