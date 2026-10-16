import structlog
from arq import cron
from arq.connections import RedisSettings
from redis.asyncio import Redis

from dcs_common.logging import configure_logging
from dcs_common.settings import load_settings
from dcs_worker.jobs.heartbeat import heartbeat

_settings = load_settings()
configure_logging(_settings.log_level)


async def startup(ctx: dict) -> None:
    ctx["redis_client"] = Redis.from_url(_settings.redis_url)
    await heartbeat(ctx)
    structlog.get_logger().info("worker.started")


async def shutdown(ctx: dict) -> None:
    await ctx["redis_client"].aclose()


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(_settings.redis_url)
    on_startup = startup
    on_shutdown = shutdown
    functions: list = []
    cron_jobs = [cron(heartbeat, second={0, 10, 20, 30, 40, 50}, run_at_startup=True)]
