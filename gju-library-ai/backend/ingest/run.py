"""Run all loaders and embed into the DB.

Usage: docker compose exec backend python -m ingest.run
"""
from sqlalchemy import text

from app.config import get_settings
from app.db import SessionLocal

from .databases_loader import load_databases_yaml
from .docx_loader import load_docx_prose
from .embed_index import upsert_passages
from .faq_loader import load_faq_xlsx

DATA = "/data"


def upsert_databases(db, records: list[dict]) -> int:
    n = 0
    for r in records:
        db.execute(
            text(
                """
                INSERT INTO subscription_databases
                  (slug, name, vendor, url, content_types, subjects, languages,
                   access_method, description_en, description_ar, description_de, enabled)
                VALUES
                  (:slug, :name, :vendor, :url, :content_types, :subjects, :languages,
                   :access_method, :description_en, :description_ar, :description_de, true)
                ON CONFLICT (slug) DO UPDATE SET
                  name=EXCLUDED.name, vendor=EXCLUDED.vendor, url=EXCLUDED.url,
                  content_types=EXCLUDED.content_types, subjects=EXCLUDED.subjects,
                  languages=EXCLUDED.languages, access_method=EXCLUDED.access_method,
                  description_en=EXCLUDED.description_en,
                  description_ar=EXCLUDED.description_ar,
                  description_de=EXCLUDED.description_de
                """
            ),
            {
                k: r.get(k)
                for k in (
                    "slug",
                    "name",
                    "vendor",
                    "url",
                    "content_types",
                    "subjects",
                    "languages",
                    "access_method",
                    "description_en",
                    "description_ar",
                    "description_de",
                )
            },
        )
        n += 1
    db.commit()
    return n


def main() -> None:
    s = get_settings()
    with SessionLocal() as db:
        all_passages = []
        all_passages += load_faq_xlsx(f"{DATA}/source/faq_general.xlsx", source="faq_general")
        all_passages += load_faq_xlsx(f"{DATA}/source/faq_databases.xlsx", source="faq_databases")
        all_passages += load_docx_prose(f"{DATA}/source/services.docx", source="services")
        all_passages += load_docx_prose(f"{DATA}/source/library_info.docx", source="library_info")
        records, db_passages = load_databases_yaml(
            f"{DATA}/seeds/subscription_databases.yaml"
        )
        all_passages += db_passages

        db.execute(text("TRUNCATE passages RESTART IDENTITY"))
        db.commit()
        n_dbs = upsert_databases(db, records)
        n_pas = upsert_passages(db, all_passages, model_name=s.embedding_model)
        print(f"databases: {n_dbs} rows; passages: {n_pas} rows")


if __name__ == "__main__":
    main()
