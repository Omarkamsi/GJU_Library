from pathlib import Path

import openpyxl

from .canonical import Passage

HEADER_ALIASES = {
    "q (en)": "q_en", "q": "q_en",
    "q (ar)": "q_ar", "س": "q_ar",
    "q (de)": "q_de",
    "a (en)": "a_en", "a": "a_en",
    "a (ar)": "a_ar", "ج": "a_ar",
    "a (de)": "a_de",
    "category": "category",
}


def _norm_header(v) -> str | None:
    return HEADER_ALIASES.get(str(v).strip().lower()) if v is not None else None


def load_faq_xlsx(path: str | Path, source: str) -> list[Passage]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out: list[Passage] = []
    for sheet in wb.worksheets:
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            continue
        header = [_norm_header(c) for c in rows[0]]
        for ri, row in enumerate(rows[1:], start=2):
            mapped = {h: row[i] for i, h in enumerate(header) if h is not None and i < len(row)}
            category = mapped.get("category")
            category = str(category).strip() if category is not None else None
            for lang in ("en", "ar", "de"):
                q = mapped.get(f"q_{lang}")
                a = mapped.get(f"a_{lang}")
                if not q or not a:
                    continue
                out.append(
                    Passage(
                        source=source,
                        source_ref=f"{sheet.title}:row{ri}:{lang}",
                        lang=lang,
                        title=str(q).strip(),
                        body=str(a).strip(),
                        subjects=[category] if category else [],
                    )
                )
    return out
