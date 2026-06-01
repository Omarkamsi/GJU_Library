from datetime import datetime, timezone
from ingest.db import insert_reading, recent_for_device

async def test_insert_and_read_back(pool):
    ts = datetime(2026, 5, 8, 10, 0, tzinfo=timezone.utc)
    await insert_reading(pool, "flow-lib", "flow", ts, {"lpm": 4.2, "total_l": 100.0})
    rows = await recent_for_device(pool, "flow-lib", "flow", limit=10)
    assert len(rows) == 1
    assert rows[0]["payload"]["lpm"] == 4.2
