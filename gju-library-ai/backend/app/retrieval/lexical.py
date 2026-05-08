from sqlalchemy import text
from sqlalchemy.orm import Session

from .interface import PassageHit

LEXICAL_SQL = text(
    """
    SELECT id, source, source_ref, lang, title, body, subjects,
           ts_rank_cd(search_vector, plainto_tsquery('simple', f_unaccent(:q))) AS score
    FROM passages
    WHERE search_vector @@ plainto_tsquery('simple', f_unaccent(:q))
    ORDER BY score DESC
    LIMIT :k
    """
)


def lexical_search(db: Session, query: str, k: int = 50) -> list[PassageHit]:
    rows = db.execute(LEXICAL_SQL, {"q": query, "k": k}).all()
    return [
        PassageHit(
            id=r.id,
            source=r.source,
            source_ref=r.source_ref,
            lang=r.lang,
            title=r.title,
            body=r.body,
            subjects=r.subjects or [],
            score=float(r.score),
        )
        for r in rows
    ]
