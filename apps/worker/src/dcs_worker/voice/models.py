from dataclasses import asdict, dataclass

from dcs_niche_templates import NicheTemplate


class VoiceError(Exception):
    """Voice job error carrying a stable code (never a localized message)."""

    def __init__(self, code: str, **params: str):
        self.code = code
        self.params = params
        super().__init__(code)


@dataclass(frozen=True)
class VoiceLine:
    section: str
    text: str


@dataclass(frozen=True)
class VoiceRequest:
    run_id: str
    lines: list[VoiceLine]
    template: NicheTemplate
    provider: str
    model: str
    voice: str | None = None


@dataclass(frozen=True)
class ManifestEntry:
    index: int
    section: str
    text: str
    audio_key: str
    pause_after_seconds: float
    cached: bool


@dataclass(frozen=True)
class VoiceManifest:
    run_id: str
    entries: list[ManifestEntry]

    def to_dict(self) -> dict:
        return asdict(self)
