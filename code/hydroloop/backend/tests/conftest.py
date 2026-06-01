import os
os.environ.setdefault("POSTGRES_USER", "hydroloop")
os.environ.setdefault("POSTGRES_PASSWORD", "changeme")
os.environ.setdefault("POSTGRES_DB", "hydroloop")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5433")

import pytest_asyncio
import asyncpg

DB_URL = os.environ.get(
    "TEST_DB_URL",
    "postgresql://hydroloop:changeme@localhost:5433/hydroloop",
)

@pytest_asyncio.fixture
async def pool():
    p = await asyncpg.create_pool(DB_URL, min_size=1, max_size=2)
    async with p.acquire() as c:
        await c.execute("TRUNCATE readings, events RESTART IDENTITY")
    try:
        yield p
    finally:
        await p.close()
