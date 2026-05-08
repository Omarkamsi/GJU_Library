#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8080}"
EMAIL="${EMAIL:-smoke@gju.edu.jo}"
COOKIE=$(mktemp)

cleanup() { rm -f "$COOKIE"; }
trap cleanup EXIT

curl -sf -c "$COOKIE" -H 'content-type: application/json' \
     -d "{\"email\":\"$EMAIL\"}" "$BASE/auth/login" >/dev/null
echo "✓ login"

QUERIES=(
  "What are the library hours?"
  "ما هي ساعات الدوام؟"
  "Wie greife ich von zu Hause auf Datenbanken zu?"
  "I need IEEE engineering papers on robotics"
)

for Q in "${QUERIES[@]}"; do
  RES=$(curl -sf -b "$COOKIE" -H 'content-type: application/json' \
        -d "$(jq -nc --arg q "$Q" '{query:$q}')" "$BASE/chat")
  LAT=$(echo "$RES" | jq -r .latency_ms)
  N=$(echo "$RES" | jq '.segments | length')
  QID=$(echo "$RES" | jq -r .query_id)
  echo "✓ chat ($LAT ms, $N segments, query_id=$QID): $Q"

  CID=$(echo "$RES" | jq -r '[.segments[] | select(.type=="link")][0].click_id // empty')
  if [[ -n "${CID:-}" ]]; then
    LOC=$(curl -sf -b "$COOKIE" -o /dev/null -w '%{redirect_url}' "$BASE/go/$CID")
    echo "  → click → $LOC"
  fi

  curl -sf -b "$COOKIE" -H 'content-type: application/json' \
       -d "$(jq -nc --argjson qid "$QID" '{scope:"answer",query_id:$qid,rating:1}')" \
       "$BASE/feedback" >/dev/null
  echo "  → feedback ✓"
done

echo "all ✓"
