from httpx import AsyncClient, ASGITransport
from api.main import create_app
from api.deps import get_pool

class _FakePool:
    class _Conn:
        async def fetchval(self, *_): return 1
    def acquire(self):
        class _CM:
            async def __aenter__(s): return _FakePool._Conn()
            async def __aexit__(s, *a): return None
        return _CM()

async def test_health_ok():
    app = create_app()
    app.dependency_overrides[get_pool] = lambda: _FakePool()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
