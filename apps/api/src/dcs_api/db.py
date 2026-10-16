from dcs_common.health import (
    ComponentHealth,
    probe_database,
    probe_redis,
    probe_worker,
)


class LiveProbes:
    """Probes backed by the real database engine and Redis client."""

    def __init__(self, engine, redis_client):
        self._engine = engine
        self._redis = redis_client

    async def database(self) -> ComponentHealth:
        return await probe_database(self._engine)

    async def redis_(self) -> ComponentHealth:
        return await probe_redis(self._redis)

    async def worker_(self) -> ComponentHealth:
        return await probe_worker(self._redis)
