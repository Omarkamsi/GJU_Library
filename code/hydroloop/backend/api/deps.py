import os
from functools import lru_cache
from typing import AsyncIterator
import asyncpg
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address,
                  default_limits=[os.environ.get("API_RATE_LIMIT", "60/minute")])

@lru_cache(maxsize=1)
def _dsn() -> str:
    return (
        f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )

async def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool

async def lifespan_pool() -> AsyncIterator[asyncpg.Pool]:
    pool = await asyncpg.create_pool(_dsn(), min_size=1, max_size=10)
    try:
        yield pool
    finally:
        await pool.close()
