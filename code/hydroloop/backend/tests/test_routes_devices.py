from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient, ASGITransport
from api.main import create_app
from api.deps import get_pool
from ingest.db import insert_reading

@pytest.fixture
async def app(pool):
    a = create_app()
    a.dependency_overrides[get_pool] = lambda: pool
    return a

async def test_list_devices(app, pool):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/api/devices")
    assert r.status_code == 200
    ids = [d["id"] for d in r.json()]
    assert "wheel-01" in ids
    assert "flow-lib" in ids

async def test_device_detail_returns_recent_per_metric(app, pool):
    ts = datetime.now(timezone.utc)
    await insert_reading(pool, "flow-lib", "flow", ts, {"lpm": 4.2, "total_l": 100.0})
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/api/devices/flow-lib")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "flow-lib"
    assert body["latest"]["flow"]["payload"]["lpm"] == 4.2

async def test_series_downsamples(app, pool):
    base = datetime.now(timezone.utc) - timedelta(minutes=10)
    for i in range(20):
        await insert_reading(pool, "flow-lib", "flow",
                             base + timedelta(seconds=i*30),
                             {"lpm": float(i), "total_l": float(i)})
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/api/devices/flow-lib/series",
                         params={"metric": "flow", "bucket": "1m",
                                 "from": base.isoformat(),
                                 "to":   datetime.now(timezone.utc).isoformat()})
    assert r.status_code == 200
    points = r.json()["points"]
    assert 5 <= len(points) <= 15
    assert "ts" in points[0] and "lpm" in points[0]
