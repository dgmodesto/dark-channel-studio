from dataclasses import dataclass
from typing import Literal

from dcs_niche_templates import NicheTemplate


class RenderError(Exception):
    """Render error carrying a stable code (never a localized message)."""

    def __init__(self, code: str, **params: str):
        self.code = code
        self.params = params
        super().__init__(code)


@dataclass(frozen=True)
class RenderClip:
    index: int
    section: str
    text: str
    translation: str | None
    audio_key: str
    audio_sha256: str | None = None
    duration_seconds: float | None = None
    pause_after_seconds: float = 0.0


@dataclass(frozen=True)
class Background:
    """`color`: value is an RRGGBB hex string. `image`: value is a store key."""

    kind: Literal["color", "image"]
    value: str
    sha256: str | None = None


@dataclass(frozen=True)
class MusicSpec:
    key: str
    sha256: str | None = None
    base_db: float = -8.0
    duck_db: float = -20.0


@dataclass(frozen=True)
class RenderRequest:
    run_id: str
    template: NicheTemplate
    clips: list[RenderClip]
    background: Background
    music: MusicSpec | None = None
    width: int = 1280
    height: int = 720
    fps: int = 30


@dataclass(frozen=True)
class RenderPlan:
    args: list[str]
    ass: str
    inputs: list[tuple[str, str]]  # (local file name, store key)
    input_hash: str
    output_key: str
    duration_seconds: float


@dataclass(frozen=True)
class RenderResult:
    run_id: str
    video_key: str
    input_hash: str
    duration_seconds: float
    cached: bool

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "video_key": self.video_key,
            "input_hash": self.input_hash,
            "duration_seconds": self.duration_seconds,
            "cached": self.cached,
        }
