from pathlib import Path
from typing import Any

import yaml

from .canonical import Passage

REQUIRED = ["slug", "name", "url"]


def load_databases_yaml(path: str | Path) -> tuple[list[dict[str, Any]], list[Passage]]:
    with open(path, encoding="utf-8") as f:
        rows: list[dict[str, Any]] = yaml.safe_load(f)
    out_records: list[dict[str, Any]] = []
    out_passages: list[Passage] = []
    seen: set[str] = set()
    for r in rows:
        for k in REQUIRED:
            if not r.get(k):
                raise ValueError(f"Database row missing {k!r}: {r}")
        if r["slug"] in seen:
            raise ValueError(f"Duplicate slug: {r['slug']}")
        seen.add(r["slug"])
        out_records.append(r)
        for lang in ("en", "ar", "de"):
            desc = r.get(f"description_{lang}")
            if not desc:
                continue
            out_passages.append(
                Passage(
                    source="databases",
                    source_ref=f"db:{r['slug']}",
                    lang=lang,
                    title=r["name"],
                    body=desc,
                    subjects=r.get("subjects", []) or [],
                )
            )
    return out_records, out_passages
