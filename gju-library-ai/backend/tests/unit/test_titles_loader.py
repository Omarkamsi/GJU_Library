import os
from pathlib import Path

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
