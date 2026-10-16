import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal, Protocol

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Uuid,
    insert,
    select,
)
from sqlalchemy.ext.asyncio import AsyncEngine

metadata = MetaData()

cost_event_table = Table(
    "cost_event",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("run_id", String(64), nullable=False, index=True),
    Column("channel_id", String(64), nullable=True),
    Column("role", String(64), nullable=False),
    Column("kind", String(16), nullable=False),
    Column("provider", String(32), nullable=False),
    Column("model", String(128), nullable=False),
    Column("input_tokens", Integer, nullable=False, default=0),
    Column("output_tokens", Integer, nullable=False, default=0),
    Column("characters", Integer, nullable=False, default=0),
    Column("cost_usd", Numeric(12, 6), nullable=False),
    Column("priced", Boolean, nullable=False, default=True),
)


@dataclass(frozen=True)
class CostEvent:
    run_id: str
    role: str
    kind: Literal["chat", "tts"]
    provider: str
    model: str
    cost_usd: Decimal
    channel_id: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    characters: int = 0
    priced: bool = True
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class CostLedger(Protocol):
    async def record(self, event: CostEvent) -> None: ...

    async def total_for_run(self, run_id: str) -> Decimal: ...


class InMemoryCostLedger:
    def __init__(self) -> None:
        self.events: list[CostEvent] = []

    async def record(self, event: CostEvent) -> None:
        self.events.append(event)

    async def total_for_run(self, run_id: str) -> Decimal:
        return sum((e.cost_usd for e in self.events if e.run_id == run_id), Decimal(0))


class SqlCostLedger:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def record(self, event: CostEvent) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(insert(cost_event_table).values(**vars(event)))

    async def events_for_run(self, run_id: str) -> list[CostEvent]:
        stmt = (
            select(cost_event_table)
            .where(cost_event_table.c.run_id == run_id)
            .order_by(cost_event_table.c.created_at)
        )
        async with self._engine.connect() as conn:
            rows = (await conn.execute(stmt)).mappings().all()
        return [CostEvent(**{**row, "cost_usd": Decimal(row["cost_usd"])}) for row in rows]

    async def total_for_run(self, run_id: str) -> Decimal:
        return sum((e.cost_usd for e in await self.events_for_run(run_id)), Decimal(0))
