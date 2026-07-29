#!/usr/bin/env bash
# Dump the full passages + subscription_databases tables (with pre-computed embeddings)
# to a compressed SQL file so future cold starts skip the 3-hour embedding step.
#
# Usage: bash data/dump_all.sh
# Run from the project root AFTER a successful ingest.
# Output: data/passages_full.sql.gz  (~500MB compressed)

set -e
COMPOSE="docker compose"
DB="gju_library"
USER="gju"
OUT="data/passages_full.sql.gz"

echo "==> Checking passage count..."
COUNT=$($COMPOSE exec -T postgres psql -U $USER -d $DB -t -c "SELECT count(*) FROM passages;")
echo "    passages: $COUNT"

if [ "$(echo $COUNT | tr -d ' ')" -lt "100" ]; then
  echo "ERROR: Too few passages ($COUNT). Is the ingest complete?"
  exit 1
fi

echo "==> Dumping passages + subscription_databases..."
$COMPOSE exec -T postgres pg_dump \
  -U $USER $DB \
  --data-only \
  --table=passages \
  --table=subscription_databases \
  | gzip > "$OUT"

SIZE=$(du -sh "$OUT" | cut -f1)
echo "==> Done. Saved to $OUT ($SIZE)"
echo "    Restore with: bash data/restore_all.sh"
