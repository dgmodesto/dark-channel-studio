from datetime import UTC, datetime

from dcs_common.health import HEARTBEAT_KEY, HEARTBEAT_TTL_SECONDS


async def heartbeat(ctx: dict) -> None:
    await ctx["redis_client"].set(
        HEARTBEAT_KEY, datetime.now(UTC).isoformat(), ex=HEARTBEAT_TTL_SECONDS
    )
