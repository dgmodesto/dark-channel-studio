import asyncio

from dcs_common.health import (
    HEARTBEAT_KEY,
    ComponentHealth,
    probe_database,
    probe_redis,
    probe_worker,
)


class OkConn:
    async def execute(self, *_):
        return None


class OkEngine:
    def connect(self):
        return self

    async def __aenter__(self):
        return OkConn()

    async def __aexit__(self, *a):
        return False


class SlowEngine(OkEngine):
    async def __aenter__(self):
        await asyncio.sleep(5)


class RefusedEngine(OkEngine):
    async def __aenter__(self):
        raise ConnectionRefusedError()


class BrokenEngine(OkEngine):
    async def __aenter__(self):
        raise RuntimeError("boom")


class FakeRedis:
    def __init__(self, value=None, error=None, delay=0):
        self.value, self.error, self.delay = value, error, delay

    async def ping(self):
        await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return True

    async def get(self, key):
        assert key == HEARTBEAT_KEY
        return self.value


async def test_database_healthy():
    r = await probe_database(OkEngine())
    assert r.status == "healthy" and r.latency_ms is not None


async def test_database_timeout_reason():
    r = await probe_database(SlowEngine(), timeout=0.05)
    assert r == ComponentHealth(status="unhealthy", reason="timeout")


async def test_database_refused_reason():
    r = await probe_database(RefusedEngine())
    assert r.reason == "connection_refused"


async def test_database_other_error_reason():
    r = await probe_database(BrokenEngine())
    assert r.reason == "error"


async def test_redis_healthy_and_failures():
    assert (await probe_redis(FakeRedis())).status == "healthy"
    assert (await probe_redis(FakeRedis(delay=1), timeout=0.05)).reason == "timeout"
    assert (await probe_redis(FakeRedis(error=ConnectionError()))).reason == "connection_refused"
    assert (await probe_redis(FakeRedis(error=ValueError()))).reason == "error"


async def test_worker_heartbeat():
    ok = await probe_worker(FakeRedis(value=b"2026-10-16T14:00:00+00:00"))
    assert ok.status == "healthy" and ok.last_heartbeat == "2026-10-16T14:00:00+00:00"
    missing = await probe_worker(FakeRedis(value=None))
    assert missing.status == "unhealthy" and missing.reason == "no_heartbeat"
