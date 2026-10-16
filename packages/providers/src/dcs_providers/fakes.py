import hashlib

from dcs_providers.protocols import ChatMessage, ChatResult, TTSResult, Usage


class FakeChatModel:
    """Deterministic offline chat model; echoes a digest of the last message."""

    def __init__(self, reply: str | None = None):
        self._reply = reply

    async def complete(self, messages: list[ChatMessage]) -> ChatResult:
        prompt = "\n".join(m.content for m in messages)
        text = self._reply or f"fake-reply:{hashlib.sha256(prompt.encode()).hexdigest()[:8]}"
        return ChatResult(
            text=text,
            usage=Usage(
                input_tokens=max(1, len(prompt) // 4), output_tokens=max(1, len(text) // 4)
            ),
        )


class FakeTTS:
    """Deterministic offline TTS; audio bytes are a digest of the text."""

    async def synthesize(self, text: str, *, voice: str | None = None) -> TTSResult:
        audio = b"FAKEAUDIO" + hashlib.sha256(text.encode()).digest()
        return TTSResult(audio=audio, usage=Usage(characters=len(text)))
