import fakeredis.aioredis

from dcs_common.health import HEARTBEAT_KEY, HEARTBEAT_TTL_SECONDS
from dcs_worker.jobs.heartbeat import heartbeat


async def test_heartbeat_writes_timestamp_with_ttl():
    redis = fakeredis.aioredis.FakeRedis()
    await heartbeat({"redis_client": redis})
    value = await redis.get(HEARTBEAT_KEY)
    assert value is not None and b"T" in value
    ttl = await redis.ttl(HEARTBEAT_KEY)
    assert 0 < ttl <= HEARTBEAT_TTL_SECONDS == 30
