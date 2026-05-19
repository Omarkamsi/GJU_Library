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
    idx = raw.find(" / ")
    return raw[:idx].strip(" .:") if idx != -1 else raw.strip(" .:")


def _extract_year(pubdate) -> str:
    if pubdate is None:
        return "Unknown"
    m = _YEAR_RE.search(str(pubdate))
    return m.group(1) if m else "Unknown"


def _subjects_from_call(call_nbr) -> list[str]:
    if not call_nbr:
        return []
    prefix = re.match(r"^([A-Z]+)", str(call_nbr).strip())
    if not prefix:
        return []
    subject = _LC_SUBJECTS.get(prefix.group(1)[0])
    return [subject] if subject else []


def load_titles_xlsx(path: str | Path) -> list[Passage]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
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
