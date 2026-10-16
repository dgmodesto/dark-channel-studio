import pytest
from httpx import ASGITransport, AsyncClient

from dcs_api.main import create_app
from dcs_common.health import ComponentHealth


class Probes:
    def __init__(self, db="healthy", redis="healthy", worker="healthy"):
        self.db, self.redis, self.worker = db, redis, worker

    def _r(self, v):
        if v == "healthy":
            return ComponentHealth(status="healthy", latency_ms=1)
        return ComponentHealth(status="unhealthy", reason=v)

    async def database(self):
        return self._r(self.db)

    async def redis_(self):
        return self._r(self.redis)

    async def worker_(self):
        if self.worker == "healthy":
            return ComponentHealth(status="healthy", last_heartbeat="2026-10-16T14:00:00+00:00")
        return ComponentHealth(status="unhealthy", reason="no_heartbeat")


@pytest.fixture
def make_client():
    def _make(probes):
        app = create_app(probes=probes)
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    return _make


async def test_all_healthy(make_client):
    async with make_client(Probes()) as c:
        r = await c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert set(body["components"]) == {"api", "database", "redis", "worker"}


async def test_database_down_is_503_with_complete_body(make_client):
    async with make_client(Probes(db="connection_refused")) as c:
        r = await c.get("/health")
    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "unhealthy"
    assert body["components"]["database"] == {"status": "unhealthy", "reason": "connection_refused"}
    assert body["components"]["redis"]["status"] == "healthy"
    assert set(body["components"]) == {"api", "database", "redis", "worker"}


async def test_worker_missing_is_informational(make_client):
    async with make_client(Probes(worker="no_heartbeat")) as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json()["components"]["worker"]["reason"] == "no_heartbeat"


async def test_error_envelope_has_code_and_params(make_client):
    async with make_client(Probes()) as c:
        r = await c.get("/does-not-exist")
    assert r.status_code == 404
    assert r.json() == {"code": "http.not_found", "params": {}}
