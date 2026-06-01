import json
from datetime import datetime
from typing import Any
import asyncpg

async def make_pool(dsn: str) -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn, min_size=1, max_size=10)

async def insert_reading(
    pool: asyncpg.Pool, device_id: str, metric: str,
    ts: datetime, payload: dict[str, Any],
) -> None:
    async with pool.acquire() as c:
        await c.execute(
            """INSERT INTO readings (ts, device_id, metric, payload)
               VALUES ($1, $2, $3, $4::jsonb)""",
            ts, device_id, metric, json.dumps(payload),
        )
        await c.execute(
            "UPDATE devices SET last_seen = GREATEST(last_seen, $2) WHERE id = $1",
            device_id, ts,
        )

async def recent_for_device(
    pool: asyncpg.Pool, device_id: str, metric: str, limit: int = 100,
) -> list[dict]:
    async with pool.acquire() as c:
        rows = await c.fetch(
            """SELECT ts, payload FROM readings
               WHERE device_id = $1 AND metric = $2
               ORDER BY ts DESC LIMIT $3""",
            device_id, metric, limit,
        )
        return [{"ts": r["ts"], "payload": json.loads(r["payload"])} for r in rows]
