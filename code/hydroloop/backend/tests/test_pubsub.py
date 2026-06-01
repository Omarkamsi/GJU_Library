import asyncio
import pytest
from ingest.pubsub import Hub

async def test_hub_fans_out_to_all_subscribers():
    hub = Hub()
    a = hub.subscribe()
    b = hub.subscribe()
    await hub.publish({"hello": "world"})
    assert await asyncio.wait_for(a.get(), 0.1) == {"hello": "world"}
    assert await asyncio.wait_for(b.get(), 0.1) == {"hello": "world"}

async def test_unsubscribe_removes_queue():
    hub = Hub()
    a = hub.subscribe()
    hub.unsubscribe(a)
    await hub.publish({"x": 1})
    assert a.empty()

async def test_full_subscriber_does_not_block_others():
    hub = Hub(maxsize=1)
    slow = hub.subscribe()
    fast = hub.subscribe()
    await hub.publish({"n": 1})
    await hub.publish({"n": 2})
    assert await asyncio.wait_for(fast.get(), 0.1) == {"n": 1}
    assert await asyncio.wait_for(fast.get(), 0.1) == {"n": 2}
