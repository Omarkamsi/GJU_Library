import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
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


@router.post("/clear")
def clear_history(
    _uid: str = Depends(require_admin), db: Session = Depends(get_db)
) -> dict:
    """Wipe all activity tables (queries, clicks, feedback). Keeps users."""
    counts = {
        "query_log": db.execute(text("SELECT COUNT(*) FROM query_log")).scalar_one(),
        "click_events": db.execute(text("SELECT COUNT(*) FROM click_events")).scalar_one(),
        "feedback_events": db.execute(text("SELECT COUNT(*) FROM feedback_events")).scalar_one(),
    }
    # Order matters: feedback FK → clicks/queries; clicks FK → queries.
    db.execute(text("TRUNCATE feedback_events, click_events RESTART IDENTITY"))
    db.execute(text("TRUNCATE query_log RESTART IDENTITY CASCADE"))
    db.commit()
    return {"deleted": counts}


@router.get("/export.csv")
def export_csv(
    _uid: str = Depends(require_admin), db: Session = Depends(get_db)
):
    """Stream query_log joined with click/feedback summaries as CSV."""
    rows = db.execute(
        text(
            """
            SELECT
              q.id, q.created_at, q.lang, q.user_id, q.raw_query,
              q.answer_text, q.model_name, q.latency_ms,
              array_to_string(q.shown_database_slugs, '|') AS shown_databases,
              COALESCE(c.shown, 0)             AS clicks_shown,
              COALESCE(c.clicked, 0)           AS clicks_clicked,
              COALESCE(f.up, 0)                AS feedback_up,
              COALESCE(f.down, 0)              AS feedback_down,
              f.avg_rating                     AS feedback_avg
            FROM query_log q
            LEFT JOIN (
              SELECT query_id,
                     COUNT(*)                                            AS shown,
                     COUNT(*) FILTER (WHERE clicked_at IS NOT NULL)      AS clicked
              FROM click_events GROUP BY query_id
            ) c ON c.query_id = q.id
            LEFT JOIN (
              SELECT query_id,
                     COUNT(*) FILTER (WHERE rating = 1)                  AS up,
                     COUNT(*) FILTER (WHERE rating = -1)                 AS down,
                     ROUND(AVG(rating)::numeric, 2)                      AS avg_rating
              FROM feedback_events GROUP BY query_id
            ) f ON f.query_id = q.id
            ORDER BY q.created_at DESC
            """
        )
    ).mappings().all()

    def _safe(val: str) -> str:
        """Prevent CSV formula injection: prefix cells that Excel treats as formulas."""
        if val and val[0] in ("=", "+", "-", "@", "\t", "\r"):
            return "'" + val
        return val

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([
        "id", "created_at", "lang", "user_id_hash", "query",
        "answer", "model", "latency_ms", "shown_databases",
        "clicks_shown", "clicks_clicked",
        "feedback_up", "feedback_down", "feedback_avg",
    ])
    for r in rows:
        w.writerow([
            r["id"],
            r["created_at"].isoformat() if r["created_at"] else "",
            r["lang"] or "",
            r["user_id"] or "",
            _safe((r["raw_query"] or "").replace("\n", " ")),
            _safe((r["answer_text"] or "").replace("\n", " ")),
            _safe(r["model_name"] or ""),
            r["latency_ms"] if r["latency_ms"] is not None else "",
            _safe(r["shown_databases"] or ""),
            r["clicks_shown"],
            r["clicks_clicked"],
            r["feedback_up"],
            r["feedback_down"],
            r["feedback_avg"] if r["feedback_avg"] is not None else "",
        ])
    csv_bytes = buf.getvalue().encode("utf-8-sig")  # BOM so Excel reads UTF-8
    fname = f"gju-library-ai-queries-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.csv"
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
