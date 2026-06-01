# HydroLoop Architecture

See `docs/superpowers/specs/2026-05-08-hydroloop-m0-implementation-design.md`
for the full design. This file is the short version pinned to the repo.

## Components
- **mosquitto** — MQTT broker, port 1883/8883
- **timescaledb** — Postgres 16 + Timescale, port 5432
- **ingest** — aiomqtt subscriber, writes to DB, fans out to in-memory hub
- **api** — FastAPI on :8000, REST + SSE
- **web** — Next.js on :3000
- **caddy** — :80/:443 reverse proxy with auto-TLS

## Data flow
ESP32 → MQTT → ingest → TimescaleDB hypertables (+ in-memory hub) → FastAPI SSE → Next.js
