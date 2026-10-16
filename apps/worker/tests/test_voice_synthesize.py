from decimal import Decimal

import pytest

from dcs_niche_templates import get_template
from dcs_providers.budget import RunBudget
from dcs_providers.errors import BudgetExceededError, ProviderCallError
from dcs_providers.fakes import FakeTTS
from dcs_providers.ledger import InMemoryCostLedger
from dcs_providers.metering import MeteredTTS, RunContext
from dcs_providers.protocols import TTSResult
from dcs_worker.voice.models import VoiceError, VoiceLine, VoiceRequest
from dcs_worker.voice.store import InMemoryAudioStore
from dcs_worker.voice.synthesize import synthesize_voice


class CountingTTS(FakeTTS):
    def __init__(self):
        self.calls: list[str] = []

    async def synthesize(self, text, *, voice=None) -> TTSResult:
        self.calls.append(text)
        return await super().synthesize(text, voice=voice)


class FlakyTTS(CountingTTS):
    def __init__(self, failures: int, fail_text: str | None = None):
        super().__init__()
        self.failures, self.fail_text = failures, fail_text

    async def synthesize(self, text, *, voice=None) -> TTSResult:
        if (self.fail_text is None or text == self.fail_text) and self.failures > 0:
            self.failures -= 1
            raise ProviderCallError("boom")
        return await super().synthesize(text, voice=voice)


def request(lines=None, **kw) -> VoiceRequest:
    lines = lines or [
        VoiceLine("hook", "Hello there!"),
        VoiceLine("key_phrases", "Nice to meet you."),
        VoiceLine("recap", "See you soon."),
    ]
    return VoiceRequest(
        run_id=kw.pop("run_id", "run-1"),
        lines=lines,
        template=get_template("english-a1-a2-br"),
        provider=kw.pop("provider", "fake"),
        model=kw.pop("model", "voice-a"),
        **kw,
    )


async def run(req, tts, store, **kw):
    return await synthesize_voice(req, tts, store, base_delay=0, **kw)


async def test_one_clip_per_line_and_manifest():
    store, tts = InMemoryAudioStore(), CountingTTS()
    manifest = await run(request(), tts, store)
    assert [e.index for e in manifest.entries] == [0, 1, 2]
    assert [e.section for e in manifest.entries] == ["hook", "key_phrases", "recap"]
    assert tts.calls == ["Hello there!", "Nice to meet you.", "See you soon."]
    for e in manifest.entries:
        assert await store.exists(e.audio_key)
    assert not any(e.cached for e in manifest.entries)
    assert await store.exists("run-1/manifest.json")


async def test_rerun_is_idempotent_and_makes_no_calls():
    store, tts = InMemoryAudioStore(), CountingTTS()
    await run(request(), tts, store)
    again = await run(request(), tts, store)
    assert len(tts.calls) == 3
    assert all(e.cached for e in again.entries)


async def test_resume_only_synthesizes_missing_lines():
    store = InMemoryAudioStore()
    first = await run(request(), CountingTTS(), store)
    await store.delete(first.entries[1].audio_key)
    tts = CountingTTS()
    again = await run(request(), tts, store)
    assert tts.calls == ["Nice to meet you."]
    assert [e.cached for e in again.entries] == [True, False, True]


async def test_transient_failure_is_retried():
    tts = FlakyTTS(failures=2)
    manifest = await run(request(), tts, InMemoryAudioStore(), attempts=3)
    assert len(manifest.entries) == 3


async def test_retries_exhausted_keeps_completed_lines():
    store = InMemoryAudioStore()
    tts = FlakyTTS(failures=99, fail_text="Nice to meet you.")
    with pytest.raises(VoiceError) as exc:
        await run(request(), tts, store, attempts=2)
    assert exc.value.code == "voice.line_failed" and exc.value.params["index"] == "1"
    assert len([k for k in store.keys() if k.endswith(".mp3")]) == 1
    healthy = CountingTTS()
    await run(request(), healthy, store)
    assert healthy.calls == ["Nice to meet you.", "See you soon."]


async def test_budget_error_is_not_retried():
    ledger = InMemoryCostLedger()
    budget = RunBudget(cap_usd=Decimal("0"))
    inner = CountingTTS()
    tts = MeteredTTS(
        inner,
        ledger,
        RunContext(run_id="run-1", role="voice", budget=budget),
        provider="fake",
        model="voice-a",
    )
    with pytest.raises(BudgetExceededError):
        await run(request(), tts, InMemoryAudioStore(), attempts=5)
    assert inner.calls == []


async def test_cost_event_recorded_only_for_new_lines():
    ledger, store = InMemoryCostLedger(), InMemoryAudioStore()
    ctx = RunContext(run_id="run-1", role="voice")
    tts = MeteredTTS(FakeTTS(), ledger, ctx, provider="fake", model="voice-a")
    await run(request(), tts, store)
    await run(request(), tts, store)
    assert len(ledger.events) == 3 and {e.kind for e in ledger.events} == {"tts"}


@pytest.mark.parametrize("change", [{"voice": "alt"}, {"model": "voice-b"}, {"provider": "other"}])
async def test_key_changes_with_voice_provider_model(change):
    store = InMemoryAudioStore()
    base = await run(request(), CountingTTS(), store)
    other = await run(request(**change), CountingTTS(), store)
    assert {e.audio_key for e in base.entries}.isdisjoint(e.audio_key for e in other.entries)


async def test_empty_line_fails_before_any_call():
    tts = CountingTTS()
    with pytest.raises(VoiceError) as exc:
        await run(
            request([VoiceLine("hook", "ok"), VoiceLine("hook", "  ")]), tts, InMemoryAudioStore()
        )
    assert exc.value.code == "voice.empty_line" and tts.calls == []


@pytest.mark.parametrize("run_id", ["", "../evil", "a/b", "a\\b"])
async def test_unsafe_run_id_rejected(run_id):
    with pytest.raises(VoiceError) as exc:
        await run(request(run_id=run_id), CountingTTS(), InMemoryAudioStore())
    assert exc.value.code == "voice.invalid_run_id"


async def test_no_lines_rejected():
    with pytest.raises(VoiceError) as exc:
        await run(
            request([])
            if False
            else VoiceRequest("r", [], get_template("english-a1-a2-br"), "fake", "m"),
            CountingTTS(),
            InMemoryAudioStore(),
        )
    assert exc.value.code == "voice.no_lines"
