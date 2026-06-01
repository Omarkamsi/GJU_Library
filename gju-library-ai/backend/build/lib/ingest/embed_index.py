from typing import Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

_model = None


def get_model(model_name: str = "BAAI/bge-m3"):
    global _model
    if _model is None:
        from FlagEmbedding import BGEM3FlagModel  # imported lazily; requires `[ml]` extra

        _model = BGEM3FlagModel(model_name, use_fp16=False)
    return _model


def embed_texts(texts: list[str], model_name: str = "BAAI/bge-m3") -> list[list[float]]:
    model = get_model(model_name)
    out = model.encode(texts, batch_size=16, max_length=2048)["dense_vecs"]
    return [v.tolist() for v in out]


def upsert_passages(db: Session, passages: Iterable, model_name: str = "BAAI/bge-m3") -> int:
    items = list(passages)
    if not items:
        return 0
    vectors = embed_texts([p.embedding_text() for p in items], model_name=model_name)
    n = 0
    for p, vec in zip(items, vectors):
        db.execute(
            text(
                """
                INSERT INTO passages
                  (source, source_ref, lang, title, body, subjects, embedding)
                VALUES
                  (:source, :source_ref, :lang, :title, :body, :subjects, :embedding)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "source": p.source,
                "source_ref": p.source_ref,
                "lang": p.lang,
                "title": p.title,
                "body": p.body,
                "subjects": p.subjects,
                "embedding": vec,
            },
        )
        n += 1
    db.commit()
    return n
