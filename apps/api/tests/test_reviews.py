from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from dcs_api.channels import metadata
from dcs_api.main import create_app
from dcs_orchestrator.adapters.review_gate import LangGraphReviewGate


@pytest.fixture
async def client(tmp_path: Path):
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    app = create_app(
        probes=object(),
        engine=engine,
        review_gate=LangGraphReviewGate(MemorySaver()),
        media_storage_dir=tmp_path,
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    await engine.dispose()


async def _create(client, run_id="render-1"):
    return await client.post(
        "/reviews",
        json={
            "run_id": run_id,
            "title": "Coffee episode",
            "video_key": f"{run_id}/render.mp4",
            "audio_keys": [f"{run_id}/voice.mp3"],
        },
    )


async def test_review_queue_and_approval_resume(client):
    created = await _create(client)
    assert created.status_code == 201
    assert created.json()["status"] == "awaiting_review"
    assert (await client.get("/reviews")).json()[0]["run_id"] == "render-1"
    approved = await client.post(
        "/reviews/render-1/decision", json={"decision": "approve", "notes": ""}
    )
    assert approved.status_code == 200 and approved.json()["status"] == "approved"
    repeated = await client.post(
        "/reviews/render-1/decision", json={"decision": "approve", "notes": ""}
    )
    assert repeated.status_code == 200 and repeated.json()["status"] == "approved"


async def test_repeated_submission_is_idempotent(client):
    first = await _create(client)
    second = await _create(client)
    assert second.status_code == 201
    assert second.json()["run_id"] == first.json()["run_id"]
    conflict = await client.post(
        "/reviews",
        json={
            "run_id": "render-1",
            "title": "Different content",
            "video_key": "render-1/other.mp4",
        },
    )
    assert conflict.status_code == 409


async def test_media_key_traversal_is_rejected(client):
    response = await client.post(
        "/reviews",
        json={
            "run_id": "traversal",
            "title": "Unsafe",
            "video_key": "../secret.mp4",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "http.invalid_request"


async def test_request_changes_needs_notes_and_resumes_graph(client):
    await _create(client, "render-2")
    invalid = await client.post(
        "/reviews/render-2/decision", json={"decision": "request_changes", "notes": " "}
    )
    assert invalid.status_code == 422
    changed = await client.post(
        "/reviews/render-2/decision",
        json={"decision": "request_changes", "notes": "Correct the subtitle timing."},
    )
    assert changed.status_code == 200
    assert changed.json()["status"] == "changes_requested"
    assert changed.json()["notes"] == "Correct the subtitle timing."


async def test_media_is_streamed_only_from_safe_review_keys(client, tmp_path):
    await _create(client)
    (tmp_path / "render-1").mkdir()
    (tmp_path / "render-1" / "render.mp4").write_bytes(b"video")
    (tmp_path / "render-1" / "voice.mp3").write_bytes(b"audio")
    video = await client.get("/reviews/render-1/media/video")
    audio = await client.get("/reviews/render-1/media/audio/0")
    assert video.content == b"video" and video.headers["content-type"] == "video/mp4"
    assert audio.content == b"audio" and audio.headers["content-type"] == "audio/mpeg"
    missing = await client.get("/reviews/render-1/media/audio/1")
    assert missing.status_code == 404
