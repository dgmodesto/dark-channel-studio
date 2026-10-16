from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    characters: int = 0


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class ChatResult:
    text: str
    usage: Usage


@dataclass(frozen=True)
class TTSResult:
    audio: bytes
    usage: Usage


@runtime_checkable
class ChatModel(Protocol):
    async def complete(self, messages: list[ChatMessage]) -> ChatResult: ...


@runtime_checkable
class TTS(Protocol):
    async def synthesize(self, text: str, *, voice: str | None = None) -> TTSResult: ...
