import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from .deps import get_pool
from .time_bucket import safe_bucket

router = APIRouter()

def _coerce_location(loc):
    if loc is None: return None
    if isinstance(loc, str): return json.loads(loc)
    return loc

@router.get("/devices")
async def list_devices(pool=Depends(get_pool)):
    async with pool.acquire() as c:
        rows = await c.fetch(
            "SELECT id, type, label, location, last_seen FROM devices ORDER BY id"
        )
    return [
        {"id": r["id"], "type": r["type"], "label": r["label"],
         "location": _coerce_location(r["location"]),
         "last_seen": r["last_seen"].isoformat() if r["last_seen"] else None}
        for r in rows
    ]

@router.get("/devices/{device_id}")
async def device_detail(device_id: str, pool=Depends(get_pool)):
    async with pool.acquire() as c:
        meta = await c.fetchrow(
            "SELECT id, type, label, location, last_seen FROM devices WHERE id=$1",
            device_id,
        )
        if meta is None:
            raise HTTPException(404, "device not found")
        latest = await c.fetch(
            """SELECT DISTINCT ON (metric) metric, ts, payload
               FROM readings WHERE device_id=$1
               ORDER BY metric, ts DESC""",
            device_id,
        )
    return {
        "id": meta["id"], "type": meta["type"], "label": meta["label"],
        "location": _coerce_location(meta["location"]),
        "last_seen": meta["last_seen"].isoformat() if meta["last_seen"] else None,
        "latest": {
            r["metric"]: {"ts": r["ts"].isoformat(),
                          "payload": json.loads(r["payload"]) if isinstance(r["payload"], str) else r["payload"]}
            for r in latest
        },
    }

@router.get("/devices/{device_id}/series")
async def device_series(
    device_id: str,
    metric: str = Query(...),
    bucket: str = Query("1m"),
    from_: Optional[datetime] = Query(None, alias="from"),
    to:    Optional[datetime] = Query(None),
    pool = Depends(get_pool),
):
    try:
        b = safe_bucket(bucket)
    except ValueError as e:
        raise HTTPException(400, str(e))
    async with pool.acquire() as c:
        rows = await c.fetch(
            f"""
            SELECT time_bucket('{b}', ts) AS bucket, payload
            FROM readings
            WHERE device_id=$1 AND metric=$2
              AND ($3::timestamptz IS NULL OR ts >= $3)
              AND ($4::timestamptz IS NULL OR ts <= $4)
            ORDER BY bucket
            """,
            device_id, metric, from_, to,
        )
    grouped: dict = {}
    for r in rows:
        bkt = r["bucket"].isoformat()
        p = r["payload"] if not isinstance(r["payload"], str) else json.loads(r["payload"])
        agg = grouped.setdefault(bkt, {"_n": 0})
        agg["_n"] += 1
        for k, v in p.items():
            if isinstance(v, (int, float)):
                agg[k] = agg.get(k, 0.0) + v
    points = []
    for bkt, agg in grouped.items():
        n = agg.pop("_n")
        points.append({"ts": bkt, **{k: round(v/n, 3) for k, v in agg.items()}})
    return {"device_id": device_id, "metric": metric, "bucket": b, "points": points}
