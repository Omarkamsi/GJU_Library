# GJU Library Catalog RAG Integration — Design Spec

**Date:** 2026-05-19  
**Project:** gju-library-ai (M0 backend)  
**Branch:** gju-library-ai-m0

---

## Overview

Add the GJU physical book catalog (43,079 titles from `GJU_TITLES.xlsx`) to the RAG pipeline so the AI assistant can answer questions about which books the library holds, give call numbers, and direct users to the OPAC for availability and shelf location.

---

## Data Source

**File:** `data/seeds/GJU_TITLES.xlsx` — Sheet1 only (Sheets 2 & 3 are empty)  
**Columns:** BARCODE, Title, AUTHOR, CALL_NBR, PUBDATE  
**Row count:** ~43,079 physical book records  
**Language:** All metadata is in English

---

## Architecture

### Approach: One passage per book (Approach A)

Each book record becomes a `Passage` in the existing `passages` table — no schema changes required. This follows the identical contract used by `databases_loader.py` and `faq_loader.py`.

---

## Components

### 1. `ingest/titles_loader.py` (new)

Reads the Excel and returns a list of `Passage` objects.

**Passage fields per book:**

| Field | Value |
|---|---|
| `source` | `"catalog"` |
| `source_ref` | `"book:{BARCODE}"` (e.g. `book:GJU027763`) |
| `lang` | `"en"` |
| `title` | Book title, cleaned — strip trailing ` / author…` noise |
| `body` | `"Author: {author}. Call Number: {call_nbr}. Year: {year}. Available at GJU Library physical collection."` |
| `subjects` | Derived from LC call number prefix (see mapping below) |

**LC class → subjects mapping (26 entries):**

| Prefix | Subject |
|---|---|
| A | General Works |
| B | Philosophy & Religion |
| C–D | History |
| E–F | American History |
| G | Geography & Anthropology |
| H | Social Sciences |
| J | Political Science |
| K | Law |
| L | Education |
| M | Music |
| N | Fine Arts |
| P | Language & Literature |
| Q | Science |
| R | Medicine |
| S | Agriculture |
| T | Technology & Engineering |
| U–V | Military & Naval Science |
| Z | Library Science |

Rows with null or unrecognised call numbers get `subjects = []`.

**Signature:**
```python
def load_titles_xlsx(path: str | Path) -> list[Passage]
```

Skips rows where both Title and CALL_NBR are null. Logs skipped count.

### 2. `ingest/run.py` (modified)

Add call to `load_titles_xlsx` after existing loaders. Append returned passages to the shared passage list before the embed step. Add progress log line: `"Catalog: loaded {n} title passages"`.

### 3. `app/llm/prompts.py` (modified)

**New constant:**
```python
GJU_OPAC_URL = "http://hip.jopuls.org.jo/web/gju"
```

**New routing rule added to system prompt (all 3 languages — en/ar/de):**

> When a passage comes from `source=catalog` (i.e. a physical book in the GJU collection), include the call number in your answer and direct the user to check availability and shelf location at the GJU Library Catalog: http://hip.jopuls.org.jo/web/gju

**Example answer the AI should produce:**
> "Yes, GJU holds *The Seduction of Unreason* by Richard Wolin [P42]. Call number: `JC481.W65 2004`. Check availability and location at the GJU Library Catalog: http://hip.jopuls.org.jo/web/gju"

The existing `[P{id}]` citation format requires no changes.

### 4. `data/seeds/GJU_TITLES.xlsx` (new seed file)

Copy the Excel to `data/seeds/GJU_TITLES.xlsx`. Committed to git (~3 MB, acceptable).

---

## Testing

### `tests/unit/test_titles_loader.py` (new)

Uses `DATA` env var (same pattern as `test_databases_loader.py`).

**Assertions:**
- Record count ≥ 43,000
- A known barcode has the correct call number
- `subjects` list is non-empty for a record with a recognised LC prefix
- `body` contains `"Call Number:"` and `"Available at GJU Library"`
- `source` == `"catalog"` and `source_ref` starts with `"book:"`

---

## Out of Scope

- Arabic or German translations of catalog metadata (all records are English)
- Real-time OPAC availability check (link only)
- Deduplication of duplicate barcodes (none observed in sample)
- Sheets 2 and 3 (empty)

---

## Success Criteria

1. `pytest tests/unit/test_titles_loader.py` passes outside Docker
2. After `docker compose exec backend python3 ingest/run.py`, the `passages` table gains ~43k catalog rows
3. Asking the AI "does GJU have [known title]?" returns the correct call number and OPAC link
4. Asking "what engineering books does GJU have?" surfaces relevant titles via semantic retrieval
