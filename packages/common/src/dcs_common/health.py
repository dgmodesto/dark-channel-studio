import asyncio
import time
from typing import Any, Literal

from pydantic import BaseModel
from sqlalchemy import text

HEARTBEAT_KEY = "dcs:worker:heartbeat"
HEARTBEAT_TTL_SECONDS = 30
PROBE_TIMEOUT_SECONDS = 1.0

Status = Literal["healthy", "unhealthy"]


class ComponentHealth(BaseModel):
    status: Status
    reason: str | None = None
    latency_ms: int | None = None
    last_heartbeat: str | None = None

    def public(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


def _reason(exc: BaseException) -> str:
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return "timeout"
    if isinstance(exc, (ConnectionError, OSError)):
        return "connection_refused"
    return "error"


async def _timed(coro_fn, timeout: float) -> ComponentHealth:
    start = time.perf_counter()
    try:
        await asyncio.wait_for(coro_fn(), timeout)
    except Exception as exc:  # noqa: BLE001 - every failure maps to a reason code
        return ComponentHealth(status="unhealthy", reason=_reason(exc))
    return ComponentHealth(status="healthy", latency_ms=round((time.perf_counter() - start) * 1000))


async def probe_database(engine, timeout: float = PROBE_TIMEOUT_SECONDS) -> ComponentHealth:
    async def run():
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    return await _timed(run, timeout)


async def probe_redis(client, timeout: float = PROBE_TIMEOUT_SECONDS) -> ComponentHealth:
    return await _timed(client.ping, timeout)


async def probe_worker(client, timeout: float = PROBE_TIMEOUT_SECONDS) -> ComponentHealth:
    try:
        value = await asyncio.wait_for(client.get(HEARTBEAT_KEY), timeout)
    except Exception as exc:  # noqa: BLE001
        return ComponentHealth(status="unhealthy", reason=_reason(exc))
    if value is None:
        return ComponentHealth(status="unhealthy", reason="no_heartbeat")
    if isinstance(value, bytes):
        value = value.decode()
    return ComponentHealth(status="healthy", last_heartbeat=value)
