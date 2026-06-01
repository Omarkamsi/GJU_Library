import asyncio, json
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from ingest.main import HUB

router = APIRouter()

@router.get("/stream")
async def stream():
    queue = HUB.subscribe()
    async def event_gen():
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=15)
                    yield {"event": "reading", "data": json.dumps(msg)}
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": ""}
        finally:
            HUB.unsubscribe(queue)
    return EventSourceResponse(event_gen())
