import asyncio
from typing import Any

class Hub:
    """In-process fanout. Each subscriber gets its own unbounded queue;
    slow consumers (queue size >= maxsize) drop messages rather than
    blocking the publisher."""
    def __init__(self, maxsize: int = 256) -> None:
        self._subs: set[asyncio.Queue] = set()
        self._maxsize = maxsize

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subs.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subs.discard(q)

    async def publish(self, msg: Any) -> None:
        for q in list(self._subs):
            if q.qsize() > self._maxsize:
                # slow consumer: drop rather than block
                pass
            else:
                q.put_nowait(msg)
