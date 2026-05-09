from pathlib import Path

import yaml

from .canonical import Passage


def load_library_facts_yaml(path: str | Path) -> list[Passage]:
    """Each entry yields up to 3 Passages (en/ar/de) sharing a key."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    out: list[Passage] = []
    for entry in raw:
        key = entry["key"]
        subjects = entry.get("subjects", []) or []
        for lang in ("en", "ar", "de"):
            block = entry.get(lang)
            if not block:
                continue
            body = (block.get("body") or "").strip()
            if not body:
                continue
            out.append(
                Passage(
                    source="library_facts",
                    source_ref=f"facts:{key}:{lang}",
                    lang=lang,
                    title=(block.get("title") or "").strip() or None,
                    body=body,
                    subjects=subjects,
                )
            )
    return out
