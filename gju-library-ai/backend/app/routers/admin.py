from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.admin import require_admin
from app.deps import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def stats(_uid: str = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    totals = db.execute(
        text(
            """
            SELECT
              COUNT(*)                            AS queries,
              COUNT(DISTINCT user_id)             AS users,
              ROUND(AVG(latency_ms))::int         AS avg_latency_ms,
              ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms))::int
                                                  AS p50_latency_ms,
              ROUND(percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms))::int
                                                  AS p95_latency_ms
            FROM query_log
            """
        )
    ).mappings().one()

    by_lang = [
        dict(r)
        for r in db.execute(
            text(
                "SELECT lang, COUNT(*) AS n FROM query_log "
                "GROUP BY lang ORDER BY n DESC"
            )
        ).mappings()
    ]

    # CTR per database (target_type='database'): a database is "shown" once
    # per click_event row; "clicked" when clicked_at is non-null.
    db_ctr = [
        dict(r)
        for r in db.execute(
            text(
                """
                SELECT
                  ce.target_ref AS slug,
                  COALESCE(sd.name, ce.target_ref) AS name,
                  COUNT(*)                                AS shown,
                  COUNT(*) FILTER (WHERE ce.clicked_at IS NOT NULL) AS clicked,
                  ROUND(
                    100.0 * COUNT(*) FILTER (WHERE ce.clicked_at IS NOT NULL)
                    / NULLIF(COUNT(*), 0), 1
                  )                                       AS ctr_pct
                FROM click_events ce
                LEFT JOIN subscription_databases sd ON sd.slug = ce.target_ref
                WHERE ce.target_type = 'database'
                GROUP BY ce.target_ref, sd.name
                ORDER BY shown DESC, slug
                LIMIT 50
                """
            )
        ).mappings()
    ]

    external = db.execute(
        text(
            """
            SELECT
              COUNT(*)                                            AS shown,
              COUNT(*) FILTER (WHERE clicked_at IS NOT NULL)      AS clicked
            FROM click_events
            WHERE target_type = 'external'
            """
        )
    ).mappings().one()

    feedback = db.execute(
        text(
            """
            SELECT
              scope,
              COUNT(*)                                                AS n,
              COUNT(*) FILTER (WHERE rating = 1)                      AS up,
              COUNT(*) FILTER (WHERE rating = -1)                     AS down,
              COUNT(*) FILTER (WHERE rating IS NULL)                  AS skip,
              ROUND(AVG(rating)::numeric, 2)                          AS avg_rating
            FROM feedback_events
            GROUP BY scope
            ORDER BY scope
            """
        )
    ).mappings().all()

    recent = [
        dict(r)
        for r in db.execute(
            text(
                """
                SELECT id, lang, latency_ms, raw_query,
                       LEFT(answer_text, 140) AS answer_excerpt,
                       created_at
                FROM query_log
                ORDER BY created_at DESC
                LIMIT 20
                """
            )
        ).mappings()
    ]

    return {
        "totals": dict(totals),
        "by_lang": by_lang,
        "database_ctr": db_ctr,
        "external_clicks": dict(external),
        "feedback": [dict(r) for r in feedback],
        "recent_queries": recent,
    }
