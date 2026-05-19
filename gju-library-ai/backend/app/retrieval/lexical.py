import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from .interface import PassageHit

# Words that appear in questions but not in passage content — AND logic fails when they're present
_FUNCTION_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "not",
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did",
    "will", "would", "could", "should", "can", "may", "might", "must", "shall",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they", "their",
    "this", "that", "these", "those",
    "in", "on", "at", "by", "for", "with", "of", "to", "from", "into", "about",
    "what", "which", "who", "whom", "where", "when", "why", "how",
})

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


def _strip_function_words(query: str) -> str:
    tokens = [t for t in re.split(r"\s+", query.strip().lower()) if t and t not in _FUNCTION_WORDS]
    return " ".join(tokens) if tokens else query


def lexical_search(db: Session, query: str, k: int = 50) -> list[PassageHit]:
    rows = db.execute(LEXICAL_SQL, {"q": _strip_function_words(query), "k": k}).all()
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
