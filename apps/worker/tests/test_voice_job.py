from dcs_providers.fakes import FakeTTS
from dcs_worker.jobs.voice import synthesize_voice_job
from dcs_worker.voice.store import InMemoryAudioStore

PAYLOAD = {
    "run_id": "run-j",
    "template_id": "english-a1-a2-br",
    "lines": [
        {"section": "hook", "text": "Hello!"},
        {"section": "dialogue", "text": "How are you?"},
    ],
    "voice": None,
}


def make_ctx():
    seen = []

    def factory(run_id, channel_id):
        seen.append((run_id, channel_id))
        return FakeTTS(), "fake", "voice-a"

    return {"tts_factory": factory, "audio_store": InMemoryAudioStore(), "seen": seen}


async def test_job_returns_serializable_manifest():
    ctx = make_ctx()
    result = await synthesize_voice_job(ctx, {**PAYLOAD, "channel_id": "ch-1"})
    assert result["run_id"] == "run-j"
    assert [e["pause_after_seconds"] for e in result["entries"]] == [0, 2.0]
    assert ctx["seen"] == [("run-j", "ch-1")]


async def test_job_second_run_is_cached():
    ctx = make_ctx()
    await synthesize_voice_job(ctx, PAYLOAD)
    again = await synthesize_voice_job(ctx, PAYLOAD)
    assert all(e["cached"] for e in again["entries"])


def test_job_is_registered_in_worker_settings(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    from dcs_worker.settings import WorkerSettings

    assert synthesize_voice_job in WorkerSettings.functions
