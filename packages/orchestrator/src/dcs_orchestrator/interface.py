from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable

from dcs_niche_templates import NicheTemplate

ScriptStatus = Literal["in_progress", "approved", "rejected_max_iterations"]


class ScriptPipelineError(Exception):
    """Pipeline error carrying a stable code (never a localized message)."""

    def __init__(self, code: str, **params: str):
        self.code = code
        self.params = params
        super().__init__(code)


@dataclass(frozen=True)
class ScriptLine:
    section: str
    text: str


@dataclass(frozen=True)
class ScriptRequest:
    run_id: str
    topic: str
    template: NicheTemplate
    max_iterations: int = 3
    channel_id: str | None = None

    def __post_init__(self) -> None:
        if self.max_iterations < 1 or not self.topic.strip() or not self.run_id.strip():
            raise ScriptPipelineError("script.invalid_request")


@dataclass(frozen=True)
class ScriptResult:
    run_id: str
    status: ScriptStatus
    idea: str = ""
    lines: list[ScriptLine] = field(default_factory=list)
    iterations: int = 0
    notes: list[str] = field(default_factory=list)


@runtime_checkable
class ScriptOrchestrator(Protocol):
    """Engine-agnostic script pipeline; callers never see LangGraph."""

    async def start(self, request: ScriptRequest) -> ScriptResult: ...

    async def resume(self, run_id: str) -> ScriptResult: ...

    async def get_result(self, run_id: str) -> ScriptResult | None: ...
