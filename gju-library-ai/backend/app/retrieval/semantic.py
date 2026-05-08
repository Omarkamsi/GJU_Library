from sqlalchemy import text
from sqlalchemy.orm import Session

from ingest.embed_index import embed_texts

from .interface import PassageHit

SEMANTIC_SQL = text(
    """
    SELECT id, source, source_ref, lang, title, body, subjects,
           1 - (embedding <=> CAST(:vec AS vector)) AS score
    FROM passages
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> CAST(:vec AS vector) ASC
    LIMIT :k
    """
)


def semantic_search(
    db: Session,
    query: str,
    k: int = 50,
    model_name: str = "BAAI/bge-m3",
) -> list[PassageHit]:
    [vec] = embed_texts([query], model_name=model_name)
    rows = db.execute(SEMANTIC_SQL, {"vec": vec, "k": k}).all()
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
