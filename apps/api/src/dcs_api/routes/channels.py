import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, StringConstraints

from dcs_api.channels import Channel, ChannelRepository
from dcs_api.errors import ApiError
from dcs_niche_templates import NicheTemplate, TemplateNotFoundError, get_template

router = APIRouter()

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class ChannelCreate(BaseModel):
    name: Name
    template_id: str
    template_version: int | None = None


class ChannelUpdate(BaseModel):
    name: Name | None = None
    template_id: str | None = None
    template_version: int | None = None


class ChannelOut(BaseModel):
    id: uuid.UUID
    name: str
    template_id: str
    template_version: int
    content_language: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, channel: Channel) -> "ChannelOut":
        return cls(**vars(channel))


def _repo(request: Request) -> ChannelRepository:
    return ChannelRepository(request.app.state.engine)


def _resolve(template_id: str, version: int | None) -> NicheTemplate:
    try:
        return get_template(template_id, version)
    except TemplateNotFoundError:
        raise ApiError(422, "channel.template_unknown", template_id=template_id) from None


def _not_found() -> ApiError:
    return ApiError(404, "channel.not_found")


@router.post("/channels", status_code=201)
async def create_channel(body: ChannelCreate, request: Request) -> ChannelOut:
    template = _resolve(body.template_id, body.template_version)
    channel = await _repo(request).create(
        name=body.name,
        template_id=template.id,
        template_version=template.version,
        content_language=template.content_language,
    )
    return ChannelOut.of(channel)


@router.get("/channels")
async def list_channels(request: Request) -> list[ChannelOut]:
    return [ChannelOut.of(c) for c in await _repo(request).list()]


@router.get("/channels/{channel_id}")
async def get_channel(channel_id: uuid.UUID, request: Request) -> ChannelOut:
    channel = await _repo(request).get(channel_id)
    if channel is None:
        raise _not_found()
    return ChannelOut.of(channel)


@router.patch("/channels/{channel_id}")
async def update_channel(
    channel_id: uuid.UUID, body: ChannelUpdate, request: Request
) -> ChannelOut:
    repo = _repo(request)
    current = await repo.get(channel_id)
    if current is None:
        raise _not_found()
    changes: dict[str, object] = {}
    if body.name is not None:
        changes["name"] = body.name
    if body.template_id is not None or body.template_version is not None:
        template = _resolve(body.template_id or current.template_id, body.template_version)
        changes.update(
            template_id=template.id,
            template_version=template.version,
            content_language=template.content_language,
        )
    updated = await repo.update(channel_id, **changes)
    if updated is None:
        raise _not_found()
    return ChannelOut.of(updated)


@router.delete("/channels/{channel_id}", status_code=204)
async def delete_channel(channel_id: uuid.UUID, request: Request) -> Response:
    if not await _repo(request).delete(channel_id):
        raise _not_found()
    return Response(status_code=204)
