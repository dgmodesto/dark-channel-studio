from dcs_niche_templates import get_template
from dcs_providers.fakes import FakeTTS
from dcs_worker.voice.models import VoiceLine, VoiceRequest
from dcs_worker.voice.store import InMemoryAudioStore
from dcs_worker.voice.synthesize import synthesize_voice

LINES = [
    VoiceLine("hook", "Hi!"),
    VoiceLine("key_phrases", "How are you?"),
    VoiceLine("dialogue", "I am fine."),
    VoiceLine("call_to_action", "Subscribe."),
]


def req(template) -> VoiceRequest:
    return VoiceRequest("run-p", LINES, template, "fake", "voice-a")


async def test_english_template_pauses_only_in_practice_sections():
    template = get_template("english-a1-a2-br")
    manifest = await synthesize_voice(req(template), FakeTTS(), InMemoryAudioStore())
    assert [e.pause_after_seconds for e in manifest.entries] == [0, 2.0, 2.0, 0]


async def test_custom_pause_comes_from_template():
    template = get_template("english-a1-a2-br")
    voice = template.voice.model_copy(update={"shadowing_pause_seconds": 3.5})
    custom = template.model_copy(update={"voice": voice})
    manifest = await synthesize_voice(req(custom), FakeTTS(), InMemoryAudioStore())
    assert [e.pause_after_seconds for e in manifest.entries] == [0, 3.5, 3.5, 0]


async def test_zero_pause_or_no_sections_disables_pauses():
    template = get_template("english-a1-a2-br")
    for update in ({"shadowing_pause_seconds": 0.0}, {"shadowing_sections": []}):
        custom = template.model_copy(update={"voice": template.voice.model_copy(update=update)})
        manifest = await synthesize_voice(req(custom), FakeTTS(), InMemoryAudioStore())
        assert {e.pause_after_seconds for e in manifest.entries} == {0}


async def test_changing_pause_does_not_resynthesize():
    store = InMemoryAudioStore()
    template = get_template("english-a1-a2-br")
    await synthesize_voice(req(template), FakeTTS(), store)
    voice = template.voice.model_copy(update={"shadowing_pause_seconds": 1.0})
    again = await synthesize_voice(
        req(template.model_copy(update={"voice": voice})), FakeTTS(), store
    )
    assert all(e.cached for e in again.entries)
    assert [e.pause_after_seconds for e in again.entries] == [0, 1.0, 1.0, 0]
