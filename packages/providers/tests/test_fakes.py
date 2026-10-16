from dcs_providers.fakes import FakeChatModel, FakeTTS
from dcs_providers.protocols import TTS, ChatMessage, ChatModel


async def test_fake_chat_is_deterministic_with_usage():
    chat = FakeChatModel()
    assert isinstance(chat, ChatModel)
    msgs = [ChatMessage(role="user", content="hello there")]
    a, b = await chat.complete(msgs), await chat.complete(msgs)
    assert a == b
    assert a.usage.input_tokens > 0 and a.usage.output_tokens > 0


async def test_fake_tts_returns_audio_and_char_usage():
    tts = FakeTTS()
    assert isinstance(tts, TTS)
    result = await tts.synthesize("hello")
    assert result.audio and result.usage.characters == 5
    assert result == await tts.synthesize("hello")
