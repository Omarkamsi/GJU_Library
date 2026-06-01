#!/usr/bin/env bash
# infra/scripts/backup.sh
# Run nightly via cron on the VPS.
set -euo pipefail
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="/home/hydroloop/backups"
mkdir -p "$OUT"
docker compose -f /home/hydroloop/hydroloop/docker-compose.yml exec -T timescaledb \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  | gzip > "$OUT/hydroloop-$TS.sql.gz"

# Retention: keep 30 days
find "$OUT" -name 'hydroloop-*.sql.gz' -mtime +30 -delete
