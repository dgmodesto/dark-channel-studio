import hashlib
from pathlib import Path

import pytest

from dcs_niche_templates import get_template
from dcs_worker.jobs.render import render_video_job
from dcs_worker.render.models import RenderError
from dcs_worker.voice.store import InMemoryAudioStore


class FakeTools:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.runs: list[list[str]] = []

    async def probe_duration(self, path: Path) -> float:
        return 1.5

    async def run(self, args: list[str], cwd: Path) -> None:
        self.runs.append(args)
        if self.fail:
            raise RenderError("render.ffmpeg_failed")
        assert (cwd / "subs.ass").is_file() and (cwd / "a000.mp3").is_file()
        (cwd / args[-1]).write_bytes(b"VIDEO")


MANIFEST = {
    "run_id": "run-r",
    "entries": [
        {"index": 0, "section": "hook", "text": "Hello!", "audio_key": "run-r/000-a.mp3",
         "pause_after_seconds": 0.0, "cached": False},
        {"index": 1, "section": "dialogue", "text": "How are you?", "audio_key": "run-r/001-b.mp3",
         "pause_after_seconds": 2.0, "cached": False},
    ],
}  # fmt: skip

PAYLOAD = {
    "run_id": "run-r",
    "template_id": "english-a1-a2-br",
    "manifest": MANIFEST,
    "translations": ["Ola!", "Como vai?"],
    "background": {"kind": "color", "value": "101418"},
}


async def make_ctx(tools=None):
    store = InMemoryAudioStore()
    await store.put("run-r/000-a.mp3", b"a")
    await store.put("run-r/001-b.mp3", b"b")
    return {"audio_store": store, "media_tools": tools or FakeTools()}


async def test_job_renders_and_stores_video():
    ctx = await make_ctx()
    result = await render_video_job(ctx, PAYLOAD)
    assert result["cached"] is False
    assert result["duration_seconds"] == 5.0
    assert await ctx["audio_store"].get(result["video_key"]) == b"VIDEO"
    assert (await ctx["audio_store"].get(result["thumbnail_key"])).startswith(b"<svg")
    assert result["seo"]["synthetic_content_disclosed"] is True
    assert "AI-generated synthetic media" in result["seo"]["description"]
    assert get_template("english-a1-a2-br")  # template resolved by id


async def test_job_submits_rendered_media_to_review_gate():
    ctx = await make_ctx()
    submissions = []

    async def submit_review(payload):
        submissions.append(payload)

    ctx["review_submitter"] = submit_review
    result = await render_video_job(ctx, {**PAYLOAD, "review_title": "Coffee episode"})
    assert submissions == [
        {
            "run_id": "run-r",
            "title": "Coffee episode",
            "video_key": result["video_key"],
            "audio_keys": ["run-r/000-a.mp3", "run-r/001-b.mp3"],
            "thumbnail_key": result["thumbnail_key"],
            "description": result["seo"]["description"],
            "tags": result["seo"]["tags"],
            "synthetic_content_disclosed": True,
        }
    ]


async def test_second_run_is_cached_without_ffmpeg():
    ctx = await make_ctx()
    first = await render_video_job(ctx, PAYLOAD)
    again = await render_video_job(ctx, PAYLOAD)
    assert again["cached"] is True and again["video_key"] == first["video_key"]
    assert len(ctx["media_tools"].runs) == 1


async def test_changed_translation_rerenders():
    ctx = await make_ctx()
    first = await render_video_job(ctx, PAYLOAD)
    second = await render_video_job(ctx, {**PAYLOAD, "translations": ["Oi!", "Como vai?"]})
    assert second["cached"] is False and second["video_key"] != first["video_key"]


async def test_failure_leaves_no_output():
    ctx = await make_ctx(FakeTools(fail=True))
    with pytest.raises(RenderError) as e:
        await render_video_job(ctx, PAYLOAD)
    assert e.value.code == "render.ffmpeg_failed"
    assert not [k for k in ctx["audio_store"].keys() if k.endswith(".mp4")]


async def test_missing_translation_fails_before_ffmpeg():
    ctx = await make_ctx()
    with pytest.raises(RenderError) as e:
        await render_video_job(ctx, {**PAYLOAD, "translations": ["Ola!"]})
    assert e.value.code == "render.missing_translation"
    assert ctx["media_tools"].runs == []


async def test_input_hash_uses_audio_content():
    ctx = await make_ctx()
    first = await render_video_job(ctx, PAYLOAD)
    await ctx["audio_store"].put("run-r/000-a.mp3", b"changed")
    second = await render_video_job(ctx, PAYLOAD)
    assert second["input_hash"] != first["input_hash"]
    assert hashlib.sha256(b"x").hexdigest()  # sanity


def test_job_is_registered_in_worker_settings(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    from dcs_worker.settings import WorkerSettings

    assert render_video_job in WorkerSettings.functions


async def test_missing_input_is_a_coded_error():
    ctx = await make_ctx()
    await ctx["audio_store"].delete("run-r/001-b.mp3")
    with pytest.raises(RenderError) as e:
        await render_video_job(ctx, PAYLOAD)
    assert e.value.code == "render.input_missing"
