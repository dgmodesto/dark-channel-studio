from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScriptStructure(_Strict):
    sections: list[str] = Field(min_length=1)
    max_lines: int = Field(gt=0)
    max_words_per_line: int = Field(gt=0)


class VoiceConfig(_Strict):
    role: str
    speed: float = Field(gt=0)
    shadowing_pause_seconds: float = Field(ge=0)


class SubtitleConfig(_Strict):
    primary: str
    secondary: str | None = None
    style: str


class SeoRules(_Strict):
    title_max_chars: int = Field(gt=0)
    max_tags: int = Field(gt=0)
    description_cta: str


class Gates(_Strict):
    human_approval: Literal[True]
    synthetic_disclosure: Literal[True]


class Cadence(_Strict):
    videos_per_week: int = Field(gt=0)


class NicheTemplate(_Strict):
    id: str
    version: int = Field(gt=0)
    name: str
    content_language: str
    level: str
    script: ScriptStructure
    voice: VoiceConfig
    subtitles: SubtitleConfig
    seo: SeoRules
    gates: Gates
    cadence: Cadence
