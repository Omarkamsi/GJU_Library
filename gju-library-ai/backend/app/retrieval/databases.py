from sqlalchemy import text
from sqlalchemy.orm import Session

from .interface import DatabaseHit, PassageHit

SQL = text(
    "SELECT slug, name, url, subjects, languages, "
    "description_en, description_ar, description_de "
    "FROM subscription_databases WHERE enabled = true"
)


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def match_databases(
    db: Session,
    query_subjects: list[str],
    passages: list[PassageHit],
    lang: str,
    max_results: int = 3,
) -> list[DatabaseHit]:
    rows = db.execute(SQL).mappings().all()
    union = {s.lower() for s in query_subjects}
    for p in passages:
        union |= {s.lower() for s in (p.subjects or [])}
    general_query = "general" in {s.lower() for s in query_subjects}
    out: list[DatabaseHit] = []
    for r in rows:
        db_subjects = {s.lower() for s in (r["subjects"] or [])}
        score = _jaccard(union, db_subjects)
        # For general resource/database queries, give every database a base score
        if general_query and score <= 0:
            score = 0.1
        if lang in (r["languages"] or []):
            score += 0.05
        if score <= 0:
            continue
        desc = r.get(f"description_{lang}") or r.get("description_en") or ""
        out.append(
            DatabaseHit(
                slug=r["slug"],
                name=r["name"],
                url=r["url"],
                subjects=r["subjects"] or [],
                description=desc,
                score=score,
            )
        )
    out.sort(key=lambda d: d.score, reverse=True)
    return out[:max_results]
