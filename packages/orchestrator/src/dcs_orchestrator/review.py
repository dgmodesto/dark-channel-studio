from dataclasses import dataclass
from typing import Literal, Protocol

ReviewStatus = Literal["awaiting_review", "approved", "changes_requested"]
ReviewDecision = Literal["approve", "request_changes"]


class ReviewGateError(Exception):
    """Review-gate error with a stable code."""

    def __init__(self, code: str, **params: str):
        self.code = code
        self.params = params
        super().__init__(code)


@dataclass(frozen=True)
class ReviewRequest:
    run_id: str
    video_key: str
    audio_keys: list[str] | None = None

    def __post_init__(self) -> None:
        if not self.run_id.strip() or not self.video_key.strip():
            raise ReviewGateError("review.invalid_request")


@dataclass(frozen=True)
class ReviewResult:
    run_id: str
    video_key: str
    audio_keys: list[str]
    status: ReviewStatus
    notes: str = ""


class ReviewGate(Protocol):
    async def start(self, request: ReviewRequest) -> ReviewResult: ...

    async def decide(
        self, run_id: str, decision: ReviewDecision, notes: str = ""
    ) -> ReviewResult: ...

    async def get_result(self, run_id: str) -> ReviewResult | None: ...
