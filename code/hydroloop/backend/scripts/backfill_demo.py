"""Backfill 7 days of realistic synthetic data for the IEEE demo.

Replaces all rows in `readings` with a believable 7-day history at 1-minute
cadence. Patterns match real-world expectations so the dashboard looks alive
even before physical sensors ship:

  * Wheel power: weekdays 9:00-14:00 only; off weekends and overnight.
  * Wheel level: slow evaporation tied to temperature, daily refill at threshold.
  * Wheel weather: diurnal temp curve (Madaba in May), inverse humidity, stable pressure.
  * Building flows: per-building activity curves matching academic schedule.
  * Events: a few seeded refill events + one leak-suspect anomaly for the alert feed.

Idempotent: TRUNCATEs `readings` and `events` first, then inserts.

Usage:
    cd /root/code/hydroloop/backend
    python3 scripts/backfill_demo.py
"""
import json
import math
import os
import random
from datetime import datetime, timedelta, timezone

import psycopg2
import psycopg2.extras

DSN = os.environ.get(
    "BACKFILL_DSN",
    "postgresql://hydroloop:changeme@localhost:5433/hydroloop",
)

DAYS = 7
TICK_SECONDS = 60                          # 1-minute cadence
MINUTES_PER_DAY = 24 * 60
TOTAL_TICKS = DAYS * MINUTES_PER_DAY       # 10,080

WHEEL_ID = "wheel-01"
FLOW_DEVICES = [
    # (device_id, building_label, peak_lpm, schedule)
    ("flow-eng-bldg",  "Engineering",  6.0, "weekday-9to5"),
    ("flow-lib",       "Library",      8.0, "library-8to21"),
    ("flow-cs",        "CS",           5.5, "weekday-9to5"),
    ("flow-arch",      "Architecture", 4.5, "studio-late"),
    ("flow-business",  "Business",     4.0, "weekday-9to5"),
    ("flow-medical",   "Medical",      5.0, "steady-research"),
]


# ---------- weather model ----------

def weather_at(now: datetime) -> tuple[float, float, float]:
    """Madaba in early May: 12-30°C, 25-55% RH, 1010-1015 mbar.
    Returns (temp_c, rh_pct, pressure_mbar)."""
    h = now.hour + now.minute / 60.0
    # Diurnal sinusoid: min ~05:00, max ~14:00
    base_t = 21.0 + 9.0 * math.sin((h - 9) * math.pi / 12.0)
    # Day-of-week tweak: warmer mid-week (just for variety)
    dow_bump = 0.5 * math.sin(now.weekday() / 7 * 2 * math.pi)
    temp = base_t + dow_bump + random.gauss(0, 0.6)
    rh = max(15.0, min(65.0, 65.0 - 1.4 * (temp - 12.0) + random.gauss(0, 2.0)))
    pressure = 1013.0 + 1.5 * math.sin(h * math.pi / 12.0) + random.gauss(0, 0.5)
    return round(temp, 1), round(rh, 1), round(pressure, 1)


# ---------- wheel power model ----------

def wheel_power_at(now: datetime) -> tuple[float, float, float, float, float]:
    """Returns (v, i, p, pf, instantaneous_kwh_delta)."""
    weekday = now.weekday()                # Mon=0 ... Sun=6
    h = now.hour + now.minute / 60.0
    # Working hours: Sun-Thu 9-14 (Jordan workweek). Fri/Sat off.
    on = weekday in (6, 0, 1, 2, 3) and 9.0 <= h < 14.0
    if on:
        # Slight ramp-up, ramp-down at edges
        edge = min(h - 9.0, 14.0 - h)
        ramp = min(1.0, edge * 4.0)         # 0..1 over first/last 15 min
        p = 800.0 * ramp + random.gauss(0, 12)
        v = 419.0 + random.gauss(0, 1.0)
        pf = 0.96 + random.gauss(0, 0.005)
        i = max(0.0, p / max(1.0, v) / pf)
    else:
        p = max(0.0, 5.0 + random.gauss(0, 1.0))   # idle/standby
        v = 230.0 + random.gauss(0, 0.4)
        pf = 0.50 + random.gauss(0, 0.02)
        i = max(0.0, p / max(1.0, v) / pf)
    kwh_delta = (p / 1000.0) * (TICK_SECONDS / 3600.0)
    return round(v, 1), round(i, 2), round(p, 1), round(pf, 2), kwh_delta


# ---------- wheel level model ----------

class WheelLevel:
    """cm above sensor floor. Evaporates with temperature; refills near 35cm."""
    def __init__(self, start_cm: float = 48.0):
        self.cm = start_cm

    def step(self, temp_c: float) -> tuple[float, bool]:
        # ~0.04 cm/min loss at 25°C, scaled
        evap = max(0.0, 0.025 + (temp_c - 20.0) * 0.0025)
        self.cm -= evap + abs(random.gauss(0, 0.005))
        refilled = False
        if self.cm < 35.0:
            self.cm = 50.0
            refilled = True
        return round(self.cm, 1), refilled


# ---------- building flow models ----------

def flow_schedule_factor(now: datetime, schedule: str) -> float:
    """0..1 activity multiplier for this minute."""
    weekday = now.weekday()                # Mon=0 ... Sun=6 — Jordanian week: Sun=0 effectively, but stdlib uses Mon=0
    is_weekend = weekday in (4, 5)         # Fri (4), Sat (5) closed
    h = now.hour + now.minute / 60.0

    if schedule == "weekday-9to5":
        if is_weekend or not (8.5 <= h < 17.5):
            return 0.05
        # Two peaks: ~10 and ~14
        peak = 0.85 * math.exp(-((h - 10.5) ** 2) / 4.0) \
             + 1.0  * math.exp(-((h - 14.0) ** 2) / 4.0)
        return min(1.0, peak)

    if schedule == "library-8to21":
        if is_weekend:
            return 0.15 if 12 <= h < 18 else 0.05
        if not (8.0 <= h < 21.5):
            return 0.05
        # Steadier with a notable evening peak
        return min(1.0,
                   0.5 + 0.3 * math.sin((h - 8.0) * math.pi / 13.5)
                   + 0.4 * math.exp(-((h - 19.0) ** 2) / 6.0))

    if schedule == "studio-late":
        if is_weekend:
            return 0.10
        if 9.0 <= h < 22.0:
            return min(1.0, 0.4 + 0.5 * math.exp(-((h - 17.0) ** 2) / 8.0))
        return 0.04

    if schedule == "steady-research":
        if is_weekend:
            return 0.20
        if 8.0 <= h < 19.0:
            return 0.6 + 0.2 * math.sin((h - 8.0) * math.pi / 11.0)
        return 0.10

    return 0.1


# ---------- main ----------

def main() -> None:
    print(f"connecting to {DSN}")
    conn = psycopg2.connect(DSN)
    conn.autocommit = False

    end = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start = end - timedelta(days=DAYS)
    print(f"backfilling {start.isoformat()} → {end.isoformat()} ({TOTAL_TICKS} ticks)")

    with conn.cursor() as cur:
        cur.execute("TRUNCATE readings RESTART IDENTITY")
        cur.execute("TRUNCATE events RESTART IDENTITY")

    # Per-device running totals
    flow_total: dict[str, float] = {d[0]: 0.0 for d in FLOW_DEVICES}
    wheel_kwh = 0.0
    wheel_level = WheelLevel(start_cm=48.0)

    rows: list[tuple] = []
    events: list[tuple] = []

    # Pre-seed an alert event for the demo
    leak_at = end - timedelta(days=2, hours=4)
    events.append((leak_at, "flow-arch", "leak_suspect", "warn",
                   json.dumps({"reason": "sustained low flow during studio peak hours",
                               "lpm_observed": 0.05, "expected_min": 1.5})))

    refill_count = 0

    for tick in range(TOTAL_TICKS):
        now = start + timedelta(minutes=tick)

        # --- weather (one reading per tick) ---
        t, rh, pr = weather_at(now)
        rows.append((now, WHEEL_ID, "weather",
                     json.dumps({"t": t, "rh": rh, "p": pr})))

        # --- wheel power ---
        v, i, p, pf, kwh_delta = wheel_power_at(now)
        wheel_kwh += kwh_delta
        rows.append((now, WHEEL_ID, "power",
                     json.dumps({"v": v, "i": i, "p": p,
                                 "e": round(wheel_kwh, 3), "pf": pf})))

        # --- wheel level (with refill events) ---
        cm, refilled = wheel_level.step(t)
        rows.append((now, WHEEL_ID, "level", json.dumps({"cm": cm})))
        if refilled:
            refill_count += 1
            events.append((now, WHEEL_ID, "refill", "info",
                           json.dumps({"new_level_cm": cm,
                                       "since_last_refill_min": "auto"})))

        # --- building flows ---
        for device_id, _label, peak_lpm, sched in FLOW_DEVICES:
            factor = flow_schedule_factor(now, sched)
            lpm = max(0.0, factor * peak_lpm + random.gauss(0, 0.15))
            # Force the leak-suspect window to look broken
            if device_id == "flow-arch" and abs((now - leak_at).total_seconds()) < 1800:
                lpm = max(0.0, lpm * 0.05)
            flow_total[device_id] += lpm * (TICK_SECONDS / 60.0)
            rows.append((now, device_id, "flow",
                         json.dumps({"lpm": round(lpm, 2),
                                     "total_l": round(flow_total[device_id], 1)})))

        # Status heartbeat once an hour per device
        if now.minute == 0:
            for did in [WHEEL_ID] + [d[0] for d in FLOW_DEVICES]:
                rows.append((now, did, "status",
                             json.dumps({"rssi": -55 - random.randint(0, 25),
                                         "uptime_s": tick * TICK_SECONDS,
                                         "fw": "0.1.0"})))

    print(f"generated {len(rows)} reading rows, {len(events)} events, "
          f"{refill_count} refill events")

    # Bulk insert
    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur,
            "INSERT INTO readings (ts, device_id, metric, payload) "
            "VALUES (%s, %s, %s, %s::jsonb)",
            rows, page_size=2000)
        psycopg2.extras.execute_batch(cur,
            "INSERT INTO events (ts, device_id, kind, severity, details) "
            "VALUES (%s, %s, %s, %s, %s::jsonb)",
            events, page_size=200)
        cur.execute(
            "UPDATE devices SET last_seen = (SELECT max(ts) FROM readings r WHERE r.device_id = devices.id)"
        )

    conn.commit()
    conn.close()

    print("done. dashboard should now show 7 days of realistic patterns.")


if __name__ == "__main__":
    main()
