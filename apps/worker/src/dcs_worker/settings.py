import os
from decimal import Decimal

import structlog
from arq import cron
from arq.connections import RedisSettings
from redis.asyncio import Redis

from dcs_common.logging import configure_logging
from dcs_common.settings import load_settings
from dcs_providers.budget import RunBudget
from dcs_providers.config import ProviderConfig
from dcs_providers.ledger import SqlCostLedger
from dcs_providers.metering import MeteredTTS, RunContext
from dcs_providers.registry import build_tts
from dcs_worker.jobs.heartbeat import heartbeat
from dcs_worker.jobs.render import render_video_job
from dcs_worker.jobs.voice import synthesize_voice_job
from dcs_worker.voice.store import LocalAudioStore

_settings = load_settings()
configure_logging(_settings.log_level)


def make_tts_factory(engine_holder: dict):
    """Build a per-run metered TTS; the DB engine is created lazily on first use."""

    def factory(run_id: str, channel_id: str | None):
        cfg = ProviderConfig()
        tts, provider, model = build_tts(cfg, "tts")
        if "engine" not in engine_holder:
            from sqlalchemy.ext.asyncio import create_async_engine

            engine_holder["engine"] = create_async_engine(_settings.database_url)
        ctx = RunContext(
            run_id=run_id,
            role="tts",
            channel_id=channel_id,
            budget=RunBudget(cap_usd=Decimal(str(cfg.run_budget_usd))),
        )
        ledger = SqlCostLedger(engine_holder["engine"])
        return MeteredTTS(tts, ledger, ctx, provider=provider, model=model), provider, model

    return factory


async def startup(ctx: dict) -> None:
    ctx["redis_client"] = Redis.from_url(_settings.redis_url)
    ctx["engine_holder"] = {}
    ctx["audio_store"] = LocalAudioStore(os.environ.get("VOICE_STORAGE_DIR", "storage/audio"))
    ctx["tts_factory"] = make_tts_factory(ctx["engine_holder"])
    await heartbeat(ctx)
    structlog.get_logger().info("worker.started")


async def shutdown(ctx: dict) -> None:
    await ctx["redis_client"].aclose()
    if "engine" in ctx["engine_holder"]:
        await ctx["engine_holder"]["engine"].dispose()


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(_settings.redis_url)
    on_startup = startup
    on_shutdown = shutdown
    functions = [synthesize_voice_job, render_video_job]
    cron_jobs = [cron(heartbeat, second={0, 10, 20, 30, 40, 50}, run_at_startup=True)]
