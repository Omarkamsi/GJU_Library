from datetime import datetime, timezone
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

async def test_summary_aggregates(app, pool):
    now = datetime.now(timezone.utc)
    await insert_reading(pool, "flow-lib", "flow", now, {"lpm": 5.0, "total_l": 100.0})
    await insert_reading(pool, "wheel-01", "power", now, {"v":420,"i":1.9,"p":800,"e":12.0,"pf":0.97})
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/api/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["devices_online"] >= 2
    assert "kwh_today" in body and "liters_today" in body

async def test_events_empty_by_default(app, pool):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/api/events")
    assert r.status_code == 200
    assert r.json() == []
