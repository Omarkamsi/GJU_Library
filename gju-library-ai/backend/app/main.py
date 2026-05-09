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
    from app.routers import chat as chat_router
    from app.routers import feedback as fb_router
    from app.routers import go as go_router

    app.include_router(auth_router.router)
    app.include_router(chat_router.router)
    app.include_router(go_router.router)
    app.include_router(fb_router.router)

    @app.on_event("startup")
    def _warm() -> None:
        import threading
        from app.deps import get_llm

        def warm_llm():
            llm = get_llm()
            fn = getattr(llm, "warmup", None)
            if callable(fn):
                fn()

        def warm_embedder():
            try:
                from ingest.embed_index import embed_texts
                embed_texts(["warmup"])
            except Exception:
                pass

        threading.Thread(target=warm_llm, daemon=True).start()
        threading.Thread(target=warm_embedder, daemon=True).start()

    return app

app = create_app()
