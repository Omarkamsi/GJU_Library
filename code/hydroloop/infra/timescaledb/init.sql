-- infra/timescaledb/init.sql
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS devices (
  id           TEXT PRIMARY KEY,
  type         TEXT NOT NULL CHECK (type IN ('wheel','flow','gateway')),
  label        TEXT NOT NULL,
  location     JSONB,
  installed_at TIMESTAMPTZ DEFAULT now(),
  last_seen    TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS readings (
  ts        TIMESTAMPTZ NOT NULL,
  device_id TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  metric    TEXT NOT NULL,
  payload   JSONB NOT NULL
);
SELECT create_hypertable('readings', 'ts', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS readings_device_metric_ts
  ON readings (device_id, metric, ts DESC);

CREATE TABLE IF NOT EXISTS events (
  ts        TIMESTAMPTZ NOT NULL,
  device_id TEXT,
  kind      TEXT NOT NULL,
  severity  TEXT CHECK (severity IN ('info','warn','critical')),
  details   JSONB
);
CREATE INDEX IF NOT EXISTS events_ts ON events (ts DESC);

-- Seed devices used by the mock generator and demo.
-- Coordinates are within GJU's campus bounding box at Mushaqar, Madaba St,
-- Amman, Jordan (OSM way 588418001). Centroid: 31.7770N, 35.8014E.
-- Replace with actual per-building locations once a campus map is available.
INSERT INTO devices (id, type, label, location) VALUES
  ('wheel-01',       'wheel', 'Central Water Wheel',
     '{"lat":31.7770,"lng":35.8014,"building":"Plaza"}'),
  ('flow-eng-bldg',  'flow',  'Engineering Building',
     '{"lat":31.7775,"lng":35.8020,"building":"Engineering"}'),
  ('flow-lib',       'flow',  'Library',
     '{"lat":31.7765,"lng":35.8010,"building":"Library"}'),
  ('flow-cs',        'flow',  'Computer Science',
     '{"lat":31.7780,"lng":35.8030,"building":"CS"}'),
  ('flow-arch',      'flow',  'Architecture',
     '{"lat":31.7762,"lng":35.8025,"building":"Architecture"}'),
  ('flow-business',  'flow',  'Business School',
     '{"lat":31.7785,"lng":35.8005,"building":"Business"}'),
  ('flow-medical',   'flow',  'Medical Sciences',
     '{"lat":31.7758,"lng":35.8035,"building":"Medical"}')
ON CONFLICT (id) DO NOTHING;
