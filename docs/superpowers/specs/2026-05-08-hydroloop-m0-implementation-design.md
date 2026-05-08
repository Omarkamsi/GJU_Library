---
title: HydroLoop M0 — Implementation Design
project: HydroLoop (IEEE R8 Sustainable Universities Program)
institution: German Jordanian University
date: 2026-05-08
funding: $1,400 USD (awarded)
duration: 3 months
status: design-approved
---

# HydroLoop M0 — Implementation Design

## 1. Purpose & Scope

Move HydroLoop from approved proposal to working implementation. M0 covers the
software stack (cloud, ingest, API, public dashboard) plus a complete hardware
specification handed off to the hardware team.

**In scope (M0):**
- Monorepo scaffold, Docker-compose stack, single-VPS deployment
- MQTT broker, ingest worker, TimescaleDB schema, FastAPI service, Next.js public dashboard
- Firmware skeletons for wheel-observatory and building-flow nodes
- Hardware BOM and per-node specs sufficient for the team to procure and bench-build
- Mock data generator so frontend/UX work is not blocked on physical sensors

**Out of scope (deferred):**
- MoU and physical mounting near the water wheel (separate workstream)
- Admin authentication and write APIs
- Arabic localization
- ML beyond classical baselines (reserved for M2)
- Loki/Grafana observability stack

## 2. Architecture Overview

```
ESP32 nodes  ──Wi-Fi/LoRa──►  VPS (single Docker host)
  PZEM-004T                     Mosquitto ─► Ingest worker ─► TimescaleDB
  JSN-SR04T                                                       │
  BME280                                                           ▼
  Flow sensors                                                  FastAPI (REST + SSE)
  ESP32-CAM                                                        │
                                                                   ▼
                                                            Next.js dashboard
                                                            (public, SSE-driven)
```

Six containers on one VPS — five app services plus a Caddy reverse proxy with
automatic TLS: **mosquitto**, **timescaledb**, **ingest**, **api**, **web**, **caddy**.

The ingest worker is decoupled from the API. Sensors continue streaming and
data is durable even if the web layer is down. Server-Sent Events (one-way,
HTTP-native) is used instead of WebSockets — matches the read-only dashboard
need and is simpler to operate behind Caddy.

## 3. Hardware (Handoff to Hardware Team)

### 3.1 Node A — Wheel Observatory (×1)

| Component | Part | Role |
|---|---|---|
| MCU | ESP32 DevKit-C | Wi-Fi, MQTT publisher |
| Power | PZEM-004T v3 (clamp CT) | Motor V/I/P/kWh |
| Water level | JSN-SR04T waterproof ultrasonic + IP65 mount | Refill/evaporation detection |
| Weather | BME280 (I2C) | Temp/RH/pressure for evaporation model |
| Occupancy | ESP32-CAM (separate node, publishes boolean only) | Person-near-wheel flag, no raw images leave the device |
| Enclosure | IP65 ABS box, cable glands, DIN clips | Outdoor mount on lamppost |
| Power supply | 5V/2A weatherproof PSU tapped from existing pole circuit | — |

### 3.2 Node B — Building Flow Meter (×6)

| Component | Part | Role |
|---|---|---|
| MCU | ESP32 DevKit-C | Wi-Fi, MQTT publisher |
| Flow | YF-S201 ½″ Hall-effect flow sensor (or G1″ depending on pipe) | L/min via pulse counting |
| Enclosure | IP54 box, cable glands | Indoor utility cupboard |
| Power | 5V/1A USB PSU | — |

### 3.3 Gateway / Public Display (×1 each)

| Component | Part | Role |
|---|---|---|
| Gateway | TTGO LoRa32 + outdoor antenna | Bridges LoRa frames from Wi-Fi-dead nodes to MQTT |
| Public display | 10″ Android tablet + lockable wall mount | Kiosk near wheel, runs `/?kiosk=1` |

### 3.4 Sourcing rules

- Prefer regional suppliers (Ram Electronics Amman, ASK Jordan) for ESP32 + common sensors.
- AliExpress only for items unavailable locally.
- All orders placed in Week 1; $260 contingency absorbs customs delays.

### 3.5 Responsibility split

| Hardware team | Software team (you + me) |
|---|---|
| Procurement, customs | Firmware (we ship `.bin`, they flash) |
| Bench assembly per node spec | Cloud stack, ingest, DB, API, dashboard |
| Site mounting (post-MoU) | Cloud deploy, OTA updates |
| Power tap, weatherproofing | Per-device provisioning script |

### 3.6 Handoff artifacts (in repo)

- `firmware/node_a_wheel/` — PlatformIO project, bench-tested
- `firmware/node_b_flow/` — same
- `docs/hardware/node-a-spec.md`, `node-b-spec.md` — wiring + photos
- `docs/hardware/bom.csv` — orderable
- `docs/hardware/provisioning.md` — flash + assign device ID

## 4. MQTT Contract

Topic structure: `hydroloop/{node_type}/{node_id}/{metric}`

- `node_type` ∈ `wheel`, `flow`, `gateway`
- `node_id` — short slug (`wheel-01`, `flow-eng-bldg`, `flow-lib`)
- `metric` ∈ `power`, `level`, `weather`, `flow`, `presence`, `status`

**Sample payloads (JSON, ISO-8601 UTC, 10 s cadence; status at 60 s):**

```
hydroloop/wheel/wheel-01/power     {"ts":"...","v":420.5,"i":1.9,"p":798.0,"e":12.43,"pf":0.97}
hydroloop/wheel/wheel-01/level     {"ts":"...","cm":42.1}
hydroloop/wheel/wheel-01/weather   {"ts":"...","t":28.3,"rh":31.0,"p":1011.2}
hydroloop/flow/flow-eng-bldg/flow  {"ts":"...","lpm":4.2,"total_l":1842.5}
hydroloop/+/+/status               {"ts":"...","rssi":-62,"uptime_s":4321,"fw":"0.1.0"}
```

**Rules:**
- QoS 1, retained=false except `status` (retained so dashboards know last-seen on reload)
- Per-node MQTT username + password set during provisioning
- TLS on 8883 in prod; 1883 only on local Wi-Fi for bench testing

## 5. Database Schema (TimescaleDB)

```sql
CREATE TABLE devices (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,              -- 'wheel'|'flow'|'gateway'
  label TEXT NOT NULL,
  location JSONB,                  -- {lat, lng, building}
  installed_at TIMESTAMPTZ,
  last_seen TIMESTAMPTZ
);

CREATE TABLE readings (
  ts TIMESTAMPTZ NOT NULL,
  device_id TEXT REFERENCES devices(id),
  metric TEXT NOT NULL,
  payload JSONB NOT NULL
);
SELECT create_hypertable('readings', 'ts');
CREATE INDEX ON readings (device_id, metric, ts DESC);

CREATE TABLE events (
  ts TIMESTAMPTZ NOT NULL,
  device_id TEXT,
  kind TEXT NOT NULL,              -- 'refill'|'leak_suspect'|'anomaly'|'offline'
  severity TEXT,                   -- 'info'|'warn'|'critical'
  details JSONB
);
```

JSONB payloads (instead of wide columns per metric) let new sensor types land
without schema migrations.

## 6. REST + SSE API (FastAPI)

| Method | Path | Returns |
|---|---|---|
| GET | `/api/devices` | list of devices + last_seen |
| GET | `/api/devices/{id}` | device meta + most recent reading per metric |
| GET | `/api/devices/{id}/series?metric=&from=&to=&bucket=1m` | downsampled series via `time_bucket` |
| GET | `/api/summary` | campus aggregates: kWh today, liters today, active alerts |
| GET | `/api/events?since=` | recent anomalies/leaks |
| GET | `/api/stream` | **SSE** live push from in-memory pub/sub |
| GET | `/api/health` | uptime + broker reachable + DB reachable |

Read-only. Rate-limited 60 req/min/IP via slowapi. OpenAPI auto-exported to `docs/api/`.

### End-to-end data flow

1. ESP32 publishes to `hydroloop/...` on Mosquitto
2. Ingest worker (`aiomqtt`) validates + writes to `readings`, fans out to in-memory channel
3. SSE subscribers on `/api/stream` receive the same message
4. Browser updates the corresponding chart in <500 ms

## 7. Frontend (Next.js, App Router)

**Stack:** Next.js 15 + Tailwind + shadcn/ui + Recharts + Leaflet (OSM tiles).

### Pages

| Route | Purpose |
|---|---|
| `/` | Hero overview — campus map with live device pins, three big-number tiles, 24h trend strip |
| `/wheel` | Wheel deep-dive — power gauge, water-level chart, refill timeline, weather overlay, monthly cost counter |
| `/buildings` | Grid of building cards — current L/min + sparkline |
| `/buildings/[id]` | Per-building flow over 1h/24h/7d/30d, anomaly markers |
| `/about` | Project + IEEE branding, methodology, GitHub link |

### Components

`<LiveTile>`, `<SeriesChart>`, `<DeviceMap>`, `<AlertList>`, `<StatusBadge>`, `<KioskMode>`.

### Visual direction

- Dark high-contrast theme (legible on outdoor kiosk)
- Accent: water-blue → energy-amber gradient
- Inter for UI, JetBrains Mono for big numbers
- Subtle water-droplet ripple on hero whenever a refill event lands
- Bilingual-ready copy; ship English first, Arabic in M2

### Kiosk mode

`/?kiosk=1` activates `<KioskMode />`: hides nav, enlarges fonts, auto-rotates `/`, `/wheel`, `/buildings` every 30 s. Same codebase, same deploy.

### Data fetching

SSR shell on first paint → hydrate → `EventSource('/api/stream')` for live edge. React Query (stale-while-revalidate) for historical-range queries. Reconnect with exponential backoff on disconnect.

## 8. Deployment & Infrastructure

- **VPS:** Hetzner CX22 (~$4.50/mo) or DigitalOcean Basic (~$6/mo). EU region.
- **Domain:** `hydroloop.gju-projects.com` or `hydroloop.app`.
- **Reverse proxy:** Caddy with auto Let's Encrypt TLS.

### docker-compose services

```
mosquitto    # MQTT broker (1883 LAN, 8883 TLS)
timescaledb  # Postgres 16 + Timescale extension, named volume
ingest       # aiomqtt subscriber → DB
api          # FastAPI + uvicorn, :8000
web          # Next.js standalone build, :3000
caddy        # :80 + :443, reverse proxy
```

### Caddyfile

```
hydroloop.example.com {
  reverse_proxy /api/* api:8000
  reverse_proxy /* web:3000
}
```

### Secrets

- `.env` per service, never committed; `.env.example` in repo
- Per-device MQTT credentials generated by `scripts/provision-device.sh <node_id>` → produces `device.env` for the hardware team to flash
- DB password, JWT secret (future), SSH key — in user's password manager

### CI/CD

```
git push main
  → GitHub Actions:
      build firmware → attach to GitHub release
      build + push Docker images to GHCR
      SSH to VPS → docker compose pull && docker compose up -d
  → Caddy hot-reloads, zero downtime
```

### Backups & observability

- Nightly `pg_dump` → Hetzner Storage Box (€1/mo), 30-day retention; restore tested monthly
- Logs: `docker compose logs` for M0; Loki+Grafana deferred
- Uptime: UptimeRobot free tier pings `/api/health` every 5 min
- Device health: `last_seen` column + `/health` page; no extra monitoring stack at this scale

### Local dev parity

```
git clone hydroloop
cp .env.example .env
docker compose up
# all services on localhost; hardware team can point ESP32s at the dev broker
```

## 9. Repository Layout

```
hydroloop/
├── README.md
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── Caddyfile
├── backend/
│   ├── ingest/         # aiomqtt subscriber
│   ├── api/            # FastAPI
│   └── pyproject.toml
├── frontend/           # Next.js 15
├── firmware/
│   ├── node_a_wheel/   # PlatformIO
│   └── node_b_flow/
├── infra/
│   ├── mosquitto/      # config, ACLs
│   └── scripts/        # provision-device.sh, backup.sh
├── docs/
│   ├── hardware/
│   ├── api/
│   └── architecture.md
└── .github/workflows/
```

## 10. M0 Ship Order

Five tracks; tracks 1–4 run mostly in parallel after track 1 lands.

1. **Repo skeleton** — monorepo, docker-compose, `.env.example`, README quickstart, all six services boot locally with `docker compose up`.
2. **Backend** — TimescaleDB schema + migrations, ingest worker subscribed to `hydroloop/#`, FastAPI endpoints, mock-data generator (`MOCK=1` mode).
3. **Frontend** — `/` and `/wheel` first, then `/buildings*`. Develops against mock API while sensors are en route.
4. **Firmware** — PlatformIO projects for Node A and Node B that publish the contracted MQTT payloads against a local Mosquitto.
5. **Deploy** — Provision VPS, point domain, install Caddy + Docker, GitHub Actions deploy pipeline, UptimeRobot monitor, first nightly backup verified.

## 11. Decisions Log

| Decision | Choice | Why |
|---|---|---|
| Data path | MQTT (Mosquitto) | Standard for ESP32, robust to flaky Wi-Fi, decouples ingest from API |
| Live push | Server-Sent Events | One-way matches read-only dashboard, simpler than WebSockets behind Caddy |
| Database | TimescaleDB | Hypertables + `time_bucket` give us native time-series at SQL prices |
| Schema shape | JSONB payload | New sensor types without migrations |
| Frontend | Next.js + shadcn | SSR, polished components, same code drives kiosk |
| Repo | New monorepo | Versioned firmware/backend/frontend together; clean GitHub deliverable for IEEE |
| Auth | None in M0 | Public dashboard is the deliverable; auth is M2 if facilities asks |
| MoU/wheel-mounting | Deferred | Bench-first development with mock data unblocks 80% of work |

## 12. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Customs delays on imported parts | Medium | Medium | Order Week 1, regional sourcing first, $260 contingency |
| Hardware team blocked on cloud | Low | Medium | Local Mosquitto + mock generator means they develop against laptop, not VPS |
| Frontend blocked on hardware | Low | Medium | `MOCK=1` API serves synthetic data from day one |
| MoU never lands | Medium | High | Whole campus-flow layer (6 buildings) is independent of wheel access; wheel work converts to retrofit-proposal track if needed |
| VPS provider downtime | Low | Low | UptimeRobot alerting, nightly off-host backups, can rehydrate to a new VPS in <1 hour |
| MQTT credentials leaked | Low | High | Per-device credentials, ACLs scoped to `hydroloop/<type>/<id>/#`, TLS on 8883 |

## 13. Out-of-Scope (Future Milestones)

- **M1:** Layer-1 wheel sensors physically mounted (post-MoU); refill detection from level data; evaporation regression model
- **M2:** Admin auth, write API, Arabic localization, Loki+Grafana observability
- **M3:** Anomaly detection rollout (Isolation Forest), email/SMS alerts, IEEE final report generation

## Appendix A — Open Items Before Plan Phase

None. All decisions captured. Ready for `writing-plans` skill.
