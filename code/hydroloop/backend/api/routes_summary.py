import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from .deps import get_pool

router = APIRouter()

@router.get("/summary")
async def summary(pool=Depends(get_pool)):
    async with pool.acquire() as c:
        online = await c.fetchval(
            "SELECT count(*) FROM devices WHERE last_seen > now() - interval '5 minutes'"
        )
        kwh = await c.fetchval(
            """SELECT max((payload->>'e')::float) - min((payload->>'e')::float)
               FROM readings
               WHERE device_id='wheel-01' AND metric='power'
                 AND ts >= date_trunc('day', now())"""
        ) or 0.0
        liters = await c.fetchval(
            """SELECT sum(latest.total_l - earliest.total_l) FROM (
                 SELECT device_id,
                        max((payload->>'total_l')::float) AS total_l
                 FROM readings WHERE metric='flow'
                   AND ts >= date_trunc('day', now())
                 GROUP BY device_id
               ) latest
               JOIN (
                 SELECT device_id,
                        min((payload->>'total_l')::float) AS total_l
                 FROM readings WHERE metric='flow'
                   AND ts >= date_trunc('day', now())
                 GROUP BY device_id
               ) earliest USING (device_id)"""
        ) or 0.0
        alerts = await c.fetchval(
            "SELECT count(*) FROM events WHERE severity IN ('warn','critical') AND ts >= now() - interval '24 hours'"
        )
    return {
        "devices_online": online,
        "kwh_today":      round(float(kwh), 2),
        "liters_today":   round(float(liters), 1),
        "active_alerts":  alerts,
        "as_of":          datetime.now(timezone.utc).isoformat(),
    }

@router.get("/events")
async def events(
    since: datetime | None = Query(None),
    limit: int = Query(100, le=500),
    pool = Depends(get_pool),
):
    async with pool.acquire() as c:
        rows = await c.fetch(
            """SELECT ts, device_id, kind, severity, details FROM events
               WHERE ($1::timestamptz IS NULL OR ts >= $1)
               ORDER BY ts DESC LIMIT $2""",
            since, limit,
        )
    def _coerce(v):
        if v is None: return None
        if isinstance(v, str): return json.loads(v)
        return v
    return [
        {"ts": r["ts"].isoformat(), "device_id": r["device_id"],
         "kind": r["kind"], "severity": r["severity"],
         "details": _coerce(r["details"])}
        for r in rows
    ]
