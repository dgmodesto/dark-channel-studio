import json

import httpx
import pytest

from dcs_providers.adapters.elevenlabs_tts import ElevenLabsTTS
from dcs_providers.adapters.openai_chat import OpenAIChatModel
from dcs_providers.errors import ProviderCallError
from dcs_providers.protocols import ChatMessage


def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_openai_chat_parses_content_and_usage():
    seen = {}

    def handler(request: httpx.Request):
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Hi!"}}],
                "usage": {"prompt_tokens": 7, "completion_tokens": 3},
            },
        )

    chat = OpenAIChatModel("gpt-4o-mini", "sk-secret", client=_client(handler))
    result = await chat.complete([ChatMessage(role="user", content="hello")])
    assert result.text == "Hi!"
    assert (result.usage.input_tokens, result.usage.output_tokens) == (7, 3)
    assert seen["auth"] == "Bearer sk-secret"
    assert seen["body"]["model"] == "gpt-4o-mini"


async def test_openai_error_has_code_and_no_secret():
    chat = OpenAIChatModel(
        "m", "sk-secret", client=_client(lambda r: httpx.Response(401, json={"error": "x"}))
    )
    with pytest.raises(ProviderCallError) as exc:
        await chat.complete([ChatMessage(role="user", content="hello")])
    assert exc.value.code == "provider.call_failed"
    assert exc.value.params["status"] == 401
    assert "sk-secret" not in str(exc.value)


async def test_elevenlabs_returns_audio_and_char_usage():
    seen = {}

    def handler(request: httpx.Request):
        seen["key"] = request.headers["xi-api-key"]
        seen["path"] = request.url.path
        return httpx.Response(200, content=b"MP3DATA")

    tts = ElevenLabsTTS("voice-1", "el-secret", client=_client(handler))
    result = await tts.synthesize("hello")
    assert result.audio == b"MP3DATA" and result.usage.characters == 5
    assert seen["key"] == "el-secret" and seen["path"].endswith("/voice-1")


async def test_elevenlabs_error_has_code_and_no_secret():
    tts = ElevenLabsTTS("v", "el-secret", client=_client(lambda r: httpx.Response(500)))
    with pytest.raises(ProviderCallError) as exc:
        await tts.synthesize("hello")
    assert exc.value.params["status"] == 500 and "el-secret" not in str(exc.value)
