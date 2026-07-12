#!/usr/bin/env bash
# Restore non-catalog passages and subscription_databases into a running PostgreSQL container.
# Usage: bash data/restore_non_catalog.sh
# Run from the project root after: docker compose up -d postgres && alembic upgrade head

set -e
COMPOSE="docker.exe compose -f docker-compose.yml"
DB="gju_library"
USER="gju"

echo "==> Copying CSVs into postgres container..."
$COMPOSE cp data/passages_non_catalog.csv postgres:/tmp/passages_non_catalog.csv
$COMPOSE cp data/subscription_databases.csv postgres:/tmp/subscription_databases.csv

echo "==> Restoring subscription_databases (15 rows)..."
$COMPOSE exec postgres psql -U $USER -d $DB -c "
  TRUNCATE subscription_databases CASCADE;
  \COPY subscription_databases FROM '/tmp/subscription_databases.csv' CSV HEADER;
"

echo "==> Restoring non-catalog passages (149 rows)..."
$COMPOSE exec postgres psql -U $USER -d $DB -c "
  DELETE FROM passages WHERE source != 'catalog';
  \COPY passages FROM '/tmp/passages_non_catalog.csv' CSV HEADER;
"

echo "==> Row counts:"
$COMPOSE exec postgres psql -U $USER -d $DB -c "
  SELECT source, count(*) FROM passages GROUP BY source ORDER BY count DESC;
"

echo "==> Done. Re-run the ingest pipeline to reload catalog + embeddings:"
echo "    docker.exe compose exec backend python -m ingest.run"
