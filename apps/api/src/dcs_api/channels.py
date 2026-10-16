import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Uuid,
    delete,
    insert,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncEngine

metadata = MetaData()

channel_table = Table(
    "channel",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("name", String(100), nullable=False),
    Column("template_id", String(64), nullable=False),
    Column("template_version", Integer, nullable=False),
    Column("content_language", String(16), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


@dataclass(frozen=True)
class Channel:
    id: uuid.UUID
    name: str
    template_id: str
    template_version: int
    content_language: str
    created_at: datetime
    updated_at: datetime


def _row(row) -> Channel:
    data = dict(row)
    # SQLite drops tzinfo; values are always stored as UTC.
    for key in ("created_at", "updated_at"):
        if data[key].tzinfo is None:
            data[key] = data[key].replace(tzinfo=UTC)
    return Channel(**data)


class ChannelRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def create(
        self, *, name: str, template_id: str, template_version: int, content_language: str
    ) -> Channel:
        now = datetime.now(UTC)
        values = {
            "id": uuid.uuid4(),
            "name": name,
            "template_id": template_id,
            "template_version": template_version,
            "content_language": content_language,
            "created_at": now,
            "updated_at": now,
        }
        async with self._engine.begin() as conn:
            await conn.execute(insert(channel_table).values(**values))
        return Channel(**values)

    async def get(self, channel_id: uuid.UUID) -> Channel | None:
        async with self._engine.connect() as conn:
            row = (
                (await conn.execute(select(channel_table).where(channel_table.c.id == channel_id)))
                .mappings()
                .first()
            )
        return _row(row) if row else None

    async def list(self) -> list[Channel]:
        stmt = select(channel_table).order_by(
            channel_table.c.created_at.desc(), channel_table.c.id.desc()
        )
        async with self._engine.connect() as conn:
            rows = (await conn.execute(stmt)).mappings().all()
        return [_row(r) for r in rows]

    async def update(self, channel_id: uuid.UUID, **changes) -> Channel | None:
        values = {**changes, "updated_at": datetime.now(UTC)}
        async with self._engine.begin() as conn:
            result = await conn.execute(
                update(channel_table).where(channel_table.c.id == channel_id).values(**values)
            )
        return await self.get(channel_id) if result.rowcount else None

    async def delete(self, channel_id: uuid.UUID) -> bool:
        async with self._engine.begin() as conn:
            result = await conn.execute(
                delete(channel_table).where(channel_table.c.id == channel_id)
            )
        return result.rowcount > 0
