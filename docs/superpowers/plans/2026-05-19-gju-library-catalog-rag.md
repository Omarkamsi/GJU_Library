# GJU Library Catalog RAG Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ingest 43,079 physical book records from `GJU_TITLES.xlsx` into the RAG pipeline so the AI can answer book availability questions with call numbers and an OPAC link.

**Architecture:** One `Passage` per book row, stored in the existing `passages` table via `ingest/titles_loader.py`. The loader follows the same interface as `databases_loader.py`. The LLM system prompt gains a catalog routing rule pointing to the GJU OPAC URL.

**Tech Stack:** Python 3.11, openpyxl, SQLAlchemy 2, pgvector, existing `Passage` dataclass, pytest

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `data/seeds/GJU_TITLES.xlsx` | Seed data — copy from `/root/GJU TITLES.xlsx` |
| Create | `backend/ingest/titles_loader.py` | Read Excel → list[Passage] |
| Modify | `backend/ingest/run.py` | Call titles loader, append to all_passages |
| Modify | `backend/app/llm/prompts.py` | Add OPAC URL constant + catalog routing rule |
| Create | `backend/tests/unit/test_titles_loader.py` | Unit test for titles_loader |

---

## Task 1: Copy seed file into the repo

**Files:**
- Create: `data/seeds/GJU_TITLES.xlsx`

- [ ] **Step 1: Copy the Excel file**

```bash
cp "/root/GJU TITLES.xlsx" /root/gju-library-ai/data/seeds/GJU_TITLES.xlsx
```

- [ ] **Step 2: Verify the copy**

```bash
python3 -c "
import openpyxl
wb = openpyxl.load_workbook('/root/gju-library-ai/data/seeds/GJU_TITLES.xlsx', read_only=True, data_only=True)
ws = wb.active
print('Rows:', ws.max_row, 'Cols:', ws.max_column)
"
```

Expected output: `Rows: 43080 Cols: 5`

- [ ] **Step 3: Commit**

```bash
git -C /root/gju-library-ai add data/seeds/GJU_TITLES.xlsx
git -C /root/gju-library-ai commit -m "seed: add GJU_TITLES.xlsx physical catalog (43k titles)"
```

---

## Task 2: Write the failing unit test

**Files:**
- Create: `backend/tests/unit/test_titles_loader.py`

- [ ] **Step 1: Write the test**

Create `/root/gju-library-ai/backend/tests/unit/test_titles_loader.py`:

```python
import os
from pathlib import Path

import pytest

from ingest.titles_loader import load_titles_xlsx

_DATA = Path(os.environ.get("DATA", "/data"))


def test_loads_all_records():
    passages = load_titles_xlsx(_DATA / "seeds/GJU_TITLES.xlsx")
    assert len(passages) >= 43000


def test_known_barcode_call_number():
    passages = load_titles_xlsx(_DATA / "seeds/GJU_TITLES.xlsx")
    p = next(p for p in passages if p.source_ref == "book:GJU027771")
    assert "JC481" in p.body
    assert "Wolin" in p.body


def test_passage_fields():
    passages = load_titles_xlsx(_DATA / "seeds/GJU_TITLES.xlsx")
    p = passages[0]
    assert p.source == "catalog"
    assert p.source_ref.startswith("book:")
    assert p.lang == "en"
    assert "Call Number:" in p.body
    assert "Available at GJU Library" in p.body


def test_subjects_from_lc_prefix():
    passages = load_titles_xlsx(_DATA / "seeds/GJU_TITLES.xlsx")
    # GJU027771 has call JC481.W65 2004 → J prefix → Political Science
    p = next(p for p in passages if p.source_ref == "book:GJU027771")
    assert "Political Science" in p.subjects


def test_title_stripped_of_author_noise():
    passages = load_titles_xlsx(_DATA / "seeds/GJU_TITLES.xlsx")
    # GJU027763: raw title ends with " / Ivo Andric ; edited by..."
    p = next(p for p in passages if p.source_ref == "book:GJU027763")
    assert " / " not in p.title
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
cd /root/gju-library-ai/backend
PYTHONPATH=/root/gju-library-ai/backend DATA=/root/gju-library-ai/data \
  python3 -m pytest tests/unit/test_titles_loader.py -v
```

Expected: `ModuleNotFoundError: No module named 'ingest.titles_loader'`

---

## Task 3: Implement `ingest/titles_loader.py`

**Files:**
- Create: `backend/ingest/titles_loader.py`

- [ ] **Step 1: Create the loader**

Create `/root/gju-library-ai/backend/ingest/titles_loader.py`:

```python
import re
from pathlib import Path

import openpyxl

from .canonical import Passage

_LC_SUBJECTS: dict[str, str] = {
    "A": "General Works",
    "B": "Philosophy & Religion",
    "C": "History",
    "D": "History",
    "E": "American History",
    "F": "American History",
    "G": "Geography & Anthropology",
    "H": "Social Sciences",
    "J": "Political Science",
    "K": "Law",
    "L": "Education",
    "M": "Music",
    "N": "Fine Arts",
    "P": "Language & Literature",
    "Q": "Science",
    "R": "Medicine",
    "S": "Agriculture",
    "T": "Technology & Engineering",
    "U": "Military Science",
    "V": "Naval Science",
    "Z": "Library Science",
}

_YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")


def _clean_title(raw: str) -> str:
    """Strip ' / author...' noise appended by cataloguing systems."""
    idx = raw.find(" / ")
    return raw[:idx].strip(" .:") if idx != -1 else raw.strip(" .:")


def _extract_year(pubdate) -> str:
    if pubdate is None:
        return "Unknown"
    m = _YEAR_RE.search(str(pubdate))
    return m.group(1) if m else "Unknown"


def _subjects_from_call(call_nbr: str | None) -> list[str]:
    if not call_nbr:
        return []
    prefix = re.match(r"^([A-Z]+)", call_nbr.strip())
    if not prefix:
        return []
    # Try longest prefix first, fall back to first letter
    letters = prefix.group(1)
    subject = _LC_SUBJECTS.get(letters[0])
    return [subject] if subject else []


def load_titles_xlsx(path: str | Path) -> list[Passage]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]  # Sheet1 only
    out: list[Passage] = []
    skipped = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        barcode, raw_title, author, call_nbr, pubdate = row[:5]
        if not raw_title and not call_nbr:
            skipped += 1
            continue
        title = _clean_title(str(raw_title)) if raw_title else ""
        author_str = str(author).strip(" .") if author else "Unknown"
        call_str = str(call_nbr).strip() if call_nbr else "Unknown"
        year = _extract_year(pubdate)
        body = (
            f"Author: {author_str}. "
            f"Call Number: {call_str}. "
            f"Year: {year}. "
            "Available at GJU Library physical collection."
        )
        out.append(
            Passage(
                source="catalog",
                source_ref=f"book:{barcode}",
                lang="en",
                title=title,
                body=body,
                subjects=_subjects_from_call(call_nbr),
            )
        )
    if skipped:
        print(f"Catalog: skipped {skipped} rows with no title or call number")
    print(f"Catalog: loaded {len(out)} title passages")
    return out
```

- [ ] **Step 2: Run the tests**

```bash
cd /root/gju-library-ai/backend
PYTHONPATH=/root/gju-library-ai/backend DATA=/root/gju-library-ai/data \
  python3 -m pytest tests/unit/test_titles_loader.py -v
```

Expected: all 5 tests `PASSED`

- [ ] **Step 3: Commit**

```bash
git -C /root/gju-library-ai add backend/ingest/titles_loader.py backend/tests/unit/test_titles_loader.py
git -C /root/gju-library-ai commit -m "feat: titles_loader — ingest GJU physical catalog into passages"
```

---

## Task 4: Wire loader into `ingest/run.py`

**Files:**
- Modify: `backend/ingest/run.py`

- [ ] **Step 1: Add the import and loader call**

In `/root/gju-library-ai/backend/ingest/run.py`, add the import at the top with the other loader imports:

```python
from .titles_loader import load_titles_xlsx
```

Then inside `main()`, after the `load_library_facts_yaml` call and before the `TRUNCATE` statement, add:

```python
        catalog_passages = load_titles_xlsx(f"{DATA}/seeds/GJU_TITLES.xlsx")
        all_passages += catalog_passages
```

The full `main()` function after the edit should look like:

```python
def main() -> None:
    s = get_settings()
    with SessionLocal() as db:
        all_passages = []
        all_passages += load_faq_xlsx(f"{DATA}/source/faq_general.xlsx", source="faq_general")
        all_passages += load_faq_xlsx(f"{DATA}/source/faq_databases.xlsx", source="faq_databases")
        all_passages += load_docx_prose(f"{DATA}/source/services.docx", source="services")
        all_passages += load_docx_prose(f"{DATA}/source/library_info.docx", source="library_info")
        records, db_passages = load_databases_yaml(
            f"{DATA}/seeds/subscription_databases.yaml"
        )
        all_passages += db_passages
        all_passages += load_library_facts_yaml(
            f"{DATA}/seeds/library_facts.yaml"
        )
        all_passages += load_titles_xlsx(f"{DATA}/seeds/GJU_TITLES.xlsx")

        db.execute(text("TRUNCATE passages RESTART IDENTITY"))
        db.commit()
        n_dbs = upsert_databases(db, records)
        n_pas = upsert_passages(db, all_passages, model_name=s.embedding_model)
        print(f"databases: {n_dbs} rows; passages: {n_pas} rows")
```

- [ ] **Step 2: Verify the import resolves (dry-run, no DB)**

```bash
cd /root/gju-library-ai/backend
PYTHONPATH=/root/gju-library-ai/backend python3 -c "
from ingest.run import main
print('import OK')
"
```

Expected: `import OK`

- [ ] **Step 3: Commit**

```bash
git -C /root/gju-library-ai add backend/ingest/run.py
git -C /root/gju-library-ai commit -m "feat: wire titles_loader into ingest/run.py"
```

---

## Task 5: Update `prompts.py` with OPAC routing rule

**Files:**
- Modify: `backend/app/llm/prompts.py`

- [ ] **Step 1: Add the OPAC constant and routing rule**

In `/root/gju-library-ai/backend/app/llm/prompts.py`, add this constant near the top of the file, before the `SYSTEM` dict:

```python
GJU_OPAC_URL = "http://hip.jopuls.org.jo/web/gju"
```

Then in the English system prompt string (inside `SYSTEM["en"]`), append the following sentence to the `ROUTING RULES` section (after the Turnitin rule, before the freshness note):

```
" - When a passage is from the physical catalog (source=catalog), include the "
"call number in your answer and tell the user to check availability and shelf "
f"location at the GJU Library Catalog: {GJU_OPAC_URL}\n"
```

For the Arabic system prompt (`SYSTEM["ar"]`), append to the routing rules section:

```
" - عند الإجابة عن كتاب من المجموعة الفعلية للمكتبة (المصدر: catalog)، أذكر رقم "
"التصنيف وأَحِل المستخدم للتحقق من توفر الكتاب وموقعه على الرف عبر فهرس مكتبة "
f"الجامعة الألمانية الأردنية: {GJU_OPAC_URL}\n"
```

For the German system prompt (`SYSTEM["de"]`), append to the routing rules section:

```
" - Bei einem Katalogeintrag aus dem physischen Bestand (source=catalog) nenne "
"die Signatur und verweise den Nutzer auf den GJU-Bibliothekskatalog zur "
f"Verfügbarkeits- und Standortprüfung: {GJU_OPAC_URL}\n"
```

- [ ] **Step 2: Verify the module still imports cleanly**

```bash
cd /root/gju-library-ai/backend
PYTHONPATH=/root/gju-library-ai/backend python3 -c "
from app.llm.prompts import SYSTEM, GJU_OPAC_URL
assert 'hip.jopuls.org.jo' in SYSTEM['en']
assert 'hip.jopuls.org.jo' in SYSTEM['ar']
assert 'hip.jopuls.org.jo' in SYSTEM['de']
assert GJU_OPAC_URL == 'http://hip.jopuls.org.jo/web/gju'
print('OK')
"
```

Expected: `OK`

- [ ] **Step 3: Run the full unit test suite to check nothing broke**

```bash
cd /root/gju-library-ai/backend
PYTHONPATH=/root/gju-library-ai/backend DATA=/root/gju-library-ai/data \
  python3 -m pytest tests/unit/ -v
```

Expected: all tests `PASSED` (now includes the 5 new titles_loader tests)

- [ ] **Step 4: Commit**

```bash
git -C /root/gju-library-ai add backend/app/llm/prompts.py
git -C /root/gju-library-ai commit -m "feat: add catalog routing rule + OPAC URL to LLM prompts"
```

---

## Task 6: Run ingest inside Docker to populate the DB

> This task embeds ~43k passages via bge-m3. Expect 30–60 minutes on CPU. Run it and let it finish before testing the chat.

**Files:** none — runtime operation only

- [ ] **Step 1: Confirm the Docker stack is up**

```bash
docker compose -f /root/gju-library-ai/docker-compose.yml ps
```

Expected: `backend` and `db` services showing `Up`.

- [ ] **Step 2: Copy the seed file into the container**

The `data/` directory should already be mounted. Confirm:

```bash
docker compose -f /root/gju-library-ai/docker-compose.yml exec backend \
  ls /data/seeds/GJU_TITLES.xlsx
```

Expected: `/data/seeds/GJU_TITLES.xlsx`

If the file is not there, the `data/` volume may need a restart:

```bash
docker compose -f /root/gju-library-ai/docker-compose.yml restart backend
```

- [ ] **Step 3: Run the ingest**

```bash
docker compose -f /root/gju-library-ai/docker-compose.yml exec backend \
  python3 -m ingest.run
```

Expected final line: `databases: 15 rows; passages: ~43200 rows` (exact count depends on skipped rows)

- [ ] **Step 4: Verify catalog passages are in the DB**

```bash
docker compose -f /root/gju-library-ai/docker-compose.yml exec backend \
  python3 -c "
from app.db import SessionLocal
from sqlalchemy import text
with SessionLocal() as db:
    n = db.execute(text(\"SELECT count(*) FROM passages WHERE source='catalog'\")).scalar()
    print('Catalog passages:', n)
"
```

Expected: `Catalog passages: 43000+`

---

## Task 7: Smoke-test the chat

- [ ] **Step 1: Ask about a known book**

Open the chatbot at `http://localhost:3000` and send:

> "Does GJU library have The Seduction of Unreason by Richard Wolin?"

Expected response should mention:
- The book title
- Call number `JC481.W65 2004`
- A link or reference to `http://hip.jopuls.org.jo/web/gju`

- [ ] **Step 2: Ask a subject-level question**

> "What engineering books does GJU have?"

Expected response should surface multiple titles with `T` or `Q` call numbers.

- [ ] **Step 3: Final commit if any tweaks were made**

```bash
git -C /root/gju-library-ai add -A
git -C /root/gju-library-ai commit -m "chore: post-smoke-test adjustments (if any)"
```
