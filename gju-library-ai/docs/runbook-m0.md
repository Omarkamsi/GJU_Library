# Runbook (M0)

## Reset corpus

```bash
docker compose exec backend python -m ingest.run
```

`ingest.run` truncates `passages`, re-loads all five source files +
the YAML database seed, and re-embeds with bge-m3.

## Add a database

Edit `data/seeds/subscription_databases.yaml`, then re-run ingestion.

## Inspect query log

```bash
docker compose exec postgres psql -U gju -d gju_library -c \
  "SELECT created_at, lang, raw_query, model_name, latency_ms
     FROM query_log ORDER BY id DESC LIMIT 20;"
```

## Click-through analytics (renewal study)

```bash
docker compose exec postgres psql -U gju -d gju_library -c "
SELECT target_ref AS db,
       count(*) FILTER (WHERE clicked_at IS NOT NULL) AS clicked,
       count(*)                                       AS shown,
       round(100.0 * count(*) FILTER (WHERE clicked_at IS NOT NULL)
             / nullif(count(*),0), 1)                 AS ctr_pct
  FROM click_events
 WHERE target_type = 'database'
 GROUP BY 1
 ORDER BY shown DESC;"
```

## Feedback summary

```bash
docker compose exec postgres psql -U gju -d gju_library -c "
SELECT scope, count(*), avg(rating)::numeric(5,2) AS avg_rating
  FROM feedback_events GROUP BY 1;"
```

## Wipe + re-bootstrap

```bash
docker compose down -v
docker compose up -d postgres ollama
docker compose up -d backend
docker compose exec backend alembic upgrade head
docker compose exec backend python -m ingest.run
```
