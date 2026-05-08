import re
from pathlib import Path

import docx

from .canonical import Passage

HEADING_RE = re.compile(r"^\s*\d+(\.\d+)*\.?\s+\S")


def _detect_lang(text: str) -> str:
    if not text:
        return "en"
    arabic = sum(1 for c in text if "؀" <= c <= "ۿ")
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    de_markers = sum(
        text.lower().count(k)
        for k in (" und ", " der ", " die ", " das ", "ß", "ü", "ö", "ä")
    )
    if arabic > latin:
        return "ar"
    if de_markers >= 2:
        return "de"
    return "en"


def _is_heading(p) -> bool:
    txt = (p.text or "").strip()
    if not txt:
        return False
    if HEADING_RE.match(txt):
        return True
    runs_bold = all((r.bold or False) for r in p.runs if r.text.strip())
    return bool(runs_bold and len(txt) <= 80 and txt[-1] not in ".!?")


def load_docx_prose(path: str | Path, source: str) -> list[Passage]:
    doc = docx.Document(path)
    sections: list[tuple[str | None, list[str]]] = []
    title: str | None = None
    body: list[str] = []
    for p in doc.paragraphs:
        txt = (p.text or "").strip()
        if not txt:
            continue
        if _is_heading(p):
            if title or body:
                sections.append((title, body))
            title, body = txt, []
        else:
            body.append(txt)
    if title or body:
        sections.append((title, body))

    out: list[Passage] = []
    for idx, (t, blines) in enumerate(sections):
        b = "\n".join(blines).strip()
        if not b and not t:
            continue
        if not b and t:
            b = t
        out.append(
            Passage(
                source=source,
                source_ref=f"section:{idx}",
                lang=_detect_lang((t or "") + " " + b),
                title=t,
                body=b,
                subjects=[],
            )
        )
    return out
