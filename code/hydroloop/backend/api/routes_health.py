from fastapi import APIRouter, Depends
from .deps import get_pool

router = APIRouter()

@router.get("/health")
async def health(pool=Depends(get_pool)):
    db_ok = True
    try:
        async with pool.acquire() as c:
            await c.fetchval("SELECT 1")
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": db_ok}
