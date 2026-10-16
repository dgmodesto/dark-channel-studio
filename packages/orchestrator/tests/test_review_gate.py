import pytest
from langgraph.checkpoint.memory import MemorySaver

from dcs_orchestrator.adapters.review_gate import LangGraphReviewGate
from dcs_orchestrator.review import ReviewGateError, ReviewRequest


async def test_review_interrupt_resumes_with_approval():
    saver = MemorySaver()
    gate = LangGraphReviewGate(saver)
    waiting = await gate.start(
        ReviewRequest(run_id="review-1", video_key="run/video.mp4", audio_keys=["run/voice.mp3"])
    )
    assert waiting.status == "awaiting_review"
    result = await LangGraphReviewGate(saver).decide("review-1", "approve")
    assert result.status == "approved"
    assert result.notes == ""
    assert (await gate.get_result("review-1")) == result


async def test_request_changes_resumes_with_required_notes():
    gate = LangGraphReviewGate(MemorySaver())
    await gate.start(ReviewRequest(run_id="review-2", video_key="run/video.mp4"))
    result = await gate.decide("review-2", "request_changes", "Fix the subtitle timing.")
    assert result.status == "changes_requested"
    assert result.notes == "Fix the subtitle timing."


async def test_invalid_and_repeated_decisions_are_rejected():
    gate = LangGraphReviewGate(MemorySaver())
    await gate.start(ReviewRequest(run_id="review-3", video_key="run/video.mp4"))
    with pytest.raises(ReviewGateError) as exc:
        await gate.decide("review-3", "request_changes", " ")
    assert exc.value.code == "review.notes_required"
    await gate.decide("review-3", "approve")
    with pytest.raises(ReviewGateError) as exc:
        await gate.decide("review-3", "approve")
    assert exc.value.code == "review.already_decided"
