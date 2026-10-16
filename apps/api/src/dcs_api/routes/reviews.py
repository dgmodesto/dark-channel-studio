import asyncio
import re
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Annotated, Literal

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field, StringConstraints, field_validator
from sqlalchemy import JSON, Boolean, Column, DateTime, String, Table, insert, select, update

from dcs_api.channels import metadata
from dcs_api.errors import ApiError
from dcs_orchestrator.review import ReviewGateError, ReviewRequest

router = APIRouter()
_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
ReviewRunId = Annotated[str, StringConstraints(pattern=_RUN_ID.pattern, max_length=64)]

review_table = Table(
    "review_item",
    metadata,
    Column("run_id", String(64), primary_key=True),
    Column("title", String(200), nullable=False),
    Column("video_key", String(512), nullable=False),
    Column("audio_keys", JSON, nullable=False),
    Column("thumbnail_key", String(512), nullable=False),
    Column("description", String(5000), nullable=False),
    Column("tags", JSON, nullable=False),
    Column("synthetic_content_disclosed", Boolean, nullable=False),
    Column("status", String(32), nullable=False),
    Column("notes", String(4000), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


class ReviewCreate(BaseModel):
    run_id: ReviewRunId
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    video_key: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)
    ]
    audio_keys: list[Annotated[str, StringConstraints(min_length=1, max_length=512)]] = Field(
        default_factory=list, max_length=100
    )
    thumbnail_key: Annotated[str, StringConstraints(min_length=1, max_length=512)]
    description: Annotated[str, StringConstraints(max_length=5000)] = ""
    tags: list[Annotated[str, StringConstraints(min_length=1, max_length=100)]] = Field(
        default_factory=list, max_length=30
    )
    synthetic_content_disclosed: bool = True

    @field_validator("video_key")
    @classmethod
    def validate_video_key(cls, key: str) -> str:
        if not _valid_media_key(key):
            raise ValueError("invalid media key")
        return key

    @field_validator("audio_keys")
    @classmethod
    def validate_audio_keys(cls, keys: list[str]) -> list[str]:
        if any(not _valid_media_key(key) for key in keys):
            raise ValueError("invalid media key")
        return keys

    @field_validator("thumbnail_key")
    @classmethod
    def validate_thumbnail_key(cls, key: str) -> str:
        if not _valid_media_key(key):
            raise ValueError("invalid media key")
        return key

    @field_validator("synthetic_content_disclosed")
    @classmethod
    def require_disclosure(cls, disclosed: bool) -> bool:
        if not disclosed:
            raise ValueError("synthetic disclosure is required")
        return disclosed


class ReviewDecisionBody(BaseModel):
    decision: Literal["approve", "request_changes"]
    notes: Annotated[str, StringConstraints(max_length=4000)] = ""


def _output(row: dict) -> dict:
    return {
        "run_id": row["run_id"],
        "title": row["title"],
        "video_url": f"/reviews/{row['run_id']}/media/video",
        "audio_urls": [
            f"/reviews/{row['run_id']}/media/audio/{i}" for i, _ in enumerate(row["audio_keys"])
        ],
        "thumbnail_url": (
            f"/api/reviews/{row['run_id']}/media/thumbnail" if row["thumbnail_key"] else None
        ),
        "description": row["description"],
        "tags": row["tags"],
        "synthetic_content_disclosed": row["synthetic_content_disclosed"],
        "status": row["status"],
        "notes": row["notes"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


async def _fetch(request: Request, run_id: str) -> dict:
    async with request.app.state.engine.connect() as conn:
        row = (
            (await conn.execute(select(review_table).where(review_table.c.run_id == run_id)))
            .mappings()
            .first()
        )
    if row is None:
        raise ApiError(404, "review.not_found", run_id=run_id)
    return dict(row)


def _gate_error(error: ReviewGateError) -> ApiError:
    status = 404 if error.code == "review.run_not_found" else 409
    if error.code in {"review.invalid_request", "review.invalid_decision", "review.notes_required"}:
        status = 422
    return ApiError(status, error.code, **error.params)


def _valid_media_key(key: str) -> bool:
    posix, windows = PurePosixPath(key), PureWindowsPath(key)
    return (
        bool(key.strip())
        and "\\" not in key
        and not posix.is_absolute()
        and not windows.drive
        and (".." not in posix.parts)
    )


@router.post("/reviews", status_code=201)
async def create_review(body: ReviewCreate, request: Request) -> dict:
    async with request.app.state.engine.connect() as conn:
        existing = (
            (await conn.execute(select(review_table).where(review_table.c.run_id == body.run_id)))
            .mappings()
            .first()
        )
    if existing is not None:
        row = dict(existing)
        if (
            row["title"] == body.title
            and row["video_key"] == body.video_key
            and row["audio_keys"] == body.audio_keys
            and row["thumbnail_key"] == body.thumbnail_key
            and row["description"] == body.description
            and row["tags"] == body.tags
        ):
            return _output(row)
        raise ApiError(409, "review.run_exists", run_id=body.run_id)
    gate = request.app.state.review_gate
    try:
        result = await gate.start(
            ReviewRequest(run_id=body.run_id, video_key=body.video_key, audio_keys=body.audio_keys)
        )
    except ReviewGateError as e:
        if e.code != "review.run_exists":
            raise _gate_error(e) from e
        result = await gate.get_result(body.run_id)
        if (
            result is None
            or result.video_key != body.video_key
            or result.audio_keys != body.audio_keys
        ):
            raise _gate_error(e) from e
    now = datetime.now(UTC)
    row = {
        "run_id": body.run_id,
        "title": body.title,
        "video_key": body.video_key,
        "audio_keys": body.audio_keys,
        "thumbnail_key": body.thumbnail_key,
        "description": body.description,
        "tags": body.tags,
        "synthetic_content_disclosed": body.synthetic_content_disclosed,
        "status": result.status,
        "notes": result.notes,
        "created_at": now,
        "updated_at": now,
    }
    async with request.app.state.engine.begin() as conn:
        await conn.execute(insert(review_table).values(**row))
    return _output(row)


@router.get("/reviews")
async def list_reviews(request: Request) -> list[dict]:
    async with request.app.state.engine.connect() as conn:
        rows = (
            (
                await conn.execute(
                    select(review_table).order_by(
                        review_table.c.created_at.desc(), review_table.c.run_id
                    )
                )
            )
            .mappings()
            .all()
        )
    return [_output(dict(row)) for row in rows]


@router.get("/reviews/{run_id}")
async def get_review(run_id: ReviewRunId, request: Request) -> dict:
    return _output(await _fetch(request, run_id))


@router.post("/reviews/{run_id}/decision")
async def decide_review(run_id: ReviewRunId, body: ReviewDecisionBody, request: Request) -> dict:
    row = await _fetch(request, run_id)
    if body.decision == "approve" and not row["synthetic_content_disclosed"]:
        raise ApiError(409, "review.synthetic_disclosure_required")
    expected_status = "approved" if body.decision == "approve" else "changes_requested"
    cleaned_notes = body.notes.strip()
    if row["status"] == expected_status and row["notes"] == cleaned_notes:
        return _output(row)
    try:
        result = await request.app.state.review_gate.decide(run_id, body.decision, cleaned_notes)
    except ReviewGateError as e:
        if e.code != "review.already_decided":
            raise _gate_error(e) from e
        result = await request.app.state.review_gate.get_result(run_id)
        if result is None or result.status != expected_status or result.notes != cleaned_notes:
            raise _gate_error(e) from e
    async with request.app.state.engine.begin() as conn:
        await conn.execute(
            update(review_table)
            .where(review_table.c.run_id == run_id)
            .values(status=result.status, notes=result.notes, updated_at=datetime.now(UTC))
        )
    row.update(status=result.status, notes=result.notes, updated_at=datetime.now(UTC))
    return _output(row)


async def _media_file(request: Request, run_id: str, kind: str, index: int = 0) -> Response:
    row = await _fetch(request, run_id)
    if kind == "video":
        key = row["video_key"]
        media_type = "video/mp4"
    elif kind == "thumbnail":
        key = row["thumbnail_key"]
        media_type = "image/svg+xml"
    else:
        keys = row["audio_keys"]
        if index < 0 or index >= len(keys):
            raise ApiError(404, "review.media_not_found")
        key = keys[index]
        media_type = "audio/mpeg"

    def safe_file() -> Path | None:
        root = Path(request.app.state.media_storage_dir).resolve()
        if not _valid_media_key(key):
            return None
        posix = PurePosixPath(key)
        path = (root / Path(*posix.parts)).resolve()
        return path if path.is_relative_to(root) and path.is_file() else None

    path = await asyncio.to_thread(safe_file)
    if path is None:
        raise ApiError(404, "review.media_not_found")
    return FileResponse(path, media_type=media_type)


@router.get("/reviews/{run_id}/media/video")
async def review_video(run_id: ReviewRunId, request: Request) -> Response:
    return await _media_file(request, run_id, "video")


@router.get("/reviews/{run_id}/media/thumbnail")
async def review_thumbnail(run_id: ReviewRunId, request: Request) -> Response:
    return await _media_file(request, run_id, "thumbnail")


@router.get("/reviews/{run_id}/media/audio/{index}")
async def review_audio(run_id: ReviewRunId, index: int, request: Request) -> Response:
    return await _media_file(request, run_id, "audio", index)
