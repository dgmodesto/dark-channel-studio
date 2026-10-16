from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from dcs_providers.ledger import CostEvent, SqlCostLedger, metadata


@pytest.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(metadata.create_all)
    yield eng
    await eng.dispose()


def _event(run_id, cost):
    return CostEvent(
        run_id=run_id,
        role="narrator",
        kind="tts",
        provider="elevenlabs",
        model="v",
        characters=10,
        cost_usd=Decimal(cost),
    )


async def test_round_trip_and_run_total(engine):
    ledger = SqlCostLedger(engine)
    await ledger.record(_event("r1", "0.25"))
    await ledger.record(_event("r1", "0.50"))
    await ledger.record(_event("r2", "9"))
    assert await ledger.total_for_run("r1") == Decimal("0.75")
    assert await ledger.total_for_run("none") == Decimal(0)
    events = await ledger.events_for_run("r1")
    assert len(events) == 2 and events[0].provider == "elevenlabs"
