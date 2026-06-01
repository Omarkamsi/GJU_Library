import asyncio, json
from ingest.main import HUB
from api.routes_stream import stream

async def test_stream_pushes_published_messages():
    """Test SSE route by calling the event generator directly."""
    # Call the route handler directly to get the EventSourceResponse
    response = await stream()

    # The body_iterator is the event_gen async generator inside EventSourceResponse
    gen = response.body_iterator

    msg = {"device_id": "flow-lib", "metric": "flow",
           "ts": "2026-05-08T10:00:00+00:00",
           "payload": {"lpm": 4.2, "total_l": 100.0}}

    # Schedule the publish to happen after the generator starts waiting
    async def _publish():
        await asyncio.sleep(0.05)
        await HUB.publish(msg)

    publish_task = asyncio.create_task(_publish())

    # Collect the first event from the generator
    event = await asyncio.wait_for(gen.__anext__(), timeout=3)
    await publish_task

    # event is a dict: {"event": "reading", "data": "<json>"}
    assert event["event"] == "reading"
    body = json.loads(event["data"])
    assert body["device_id"] == "flow-lib"

    # Clean up: cancel generator
    await gen.aclose()
