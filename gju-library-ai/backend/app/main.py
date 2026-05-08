from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(title="GJU Library AI", version="0.0.1")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}

    from app.routers import auth as auth_router
    app.include_router(auth_router.router)
    return app

app = create_app()
