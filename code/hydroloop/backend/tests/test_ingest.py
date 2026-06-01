import asyncio
from datetime import datetime, timezone
from ingest.main import handle_message
from ingest.pubsub import Hub

async def test_handle_message_writes_and_publishes(pool):
    hub = Hub()
    sub = hub.subscribe()
    await handle_message(
        pool, hub,
        topic="hydroloop/flow/flow-lib/flow",
        raw=b'{"ts":"2026-05-08T10:00:00+00:00","lpm":4.2,"total_l":100.0}',
    )
    msg = await asyncio.wait_for(sub.get(), 0.5)
    assert msg["device_id"] == "flow-lib"
    assert msg["metric"] == "flow"
    assert msg["payload"]["lpm"] == 4.2

async def test_ignores_malformed_topic(pool):
    hub = Hub()
    sub = hub.subscribe()
    await handle_message(pool, hub, topic="garbage/topic", raw=b"{}")
    assert sub.empty()
