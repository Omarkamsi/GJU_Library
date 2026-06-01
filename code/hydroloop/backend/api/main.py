from contextlib import asynccontextmanager
import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from .deps import limiter, _dsn
from . import routes_health, routes_devices, routes_summary, routes_stream

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(_dsn(), min_size=1, max_size=10)
    try:
        yield
    finally:
        await app.state.pool.close()

def create_app() -> FastAPI:
    app = FastAPI(title="HydroLoop API", version="0.1.0", lifespan=lifespan)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])
    app.include_router(routes_health.router, prefix="/api")
    app.include_router(routes_devices.router, prefix="/api")
    app.include_router(routes_summary.router, prefix="/api")
    app.include_router(routes_stream.router, prefix="/api")
    return app

app = create_app()
