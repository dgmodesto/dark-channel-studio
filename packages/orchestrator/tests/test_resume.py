import pytest
from langgraph.checkpoint.memory import MemorySaver
from script_helpers import GOOD, ScriptedChat, make, request, verdict

from dcs_orchestrator.interface import ScriptPipelineError


async def test_resume_after_failure_does_not_repeat_idea():
    saver = MemorySaver()
    writer1 = ScriptedChat(["Coffee angle"], fail_at=2)  # idea ok, first draft fails
    with pytest.raises(RuntimeError):
        await make(writer1, ScriptedChat([]), saver).start(request())

    # "restart": brand-new orchestrator and models over the same checkpoint store
    writer2 = ScriptedChat([GOOD])
    reviewer2 = ScriptedChat([verdict(True)])
    result = await make(writer2, reviewer2, saver).resume("run-1")
    assert result.status == "approved"
    assert result.idea == "Coffee angle"
    assert len(writer2.prompts) == 1  # only the draft, no new idea call


async def test_finished_run_state_needs_no_model_calls():
    saver = MemorySaver()
    await make(ScriptedChat(["i", GOOD]), ScriptedChat([verdict(True)]), saver).start(request())
    writer, reviewer = ScriptedChat([]), ScriptedChat([])
    result = await make(writer, reviewer, saver).get_result("run-1")
    assert result is not None and result.status == "approved"
    assert writer.prompts == [] and reviewer.prompts == []


async def test_interrupted_run_reports_in_progress():
    saver = MemorySaver()
    with pytest.raises(RuntimeError):
        await make(ScriptedChat(["i"], fail_at=2), ScriptedChat([]), saver).start(request())
    result = await make(ScriptedChat([]), ScriptedChat([]), saver).get_result("run-1")
    assert result is not None and result.status == "in_progress"


async def test_unknown_run():
    orch = make(ScriptedChat([]), ScriptedChat([]))
    assert await orch.get_result("nope") is None
    with pytest.raises(ScriptPipelineError) as exc:
        await orch.resume("nope")
    assert exc.value.code == "script.run_not_found"


async def test_resume_of_finished_run_returns_result():
    saver = MemorySaver()
    await make(ScriptedChat(["i", GOOD]), ScriptedChat([verdict(True)]), saver).start(request())
    writer = ScriptedChat([])
    result = await make(writer, ScriptedChat([]), saver).resume("run-1")
    assert result.status == "approved" and writer.prompts == []
