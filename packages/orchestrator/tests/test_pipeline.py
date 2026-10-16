from decimal import Decimal

import pytest
from script_helpers import GOOD, ScriptedChat, draft, make, request, verdict

from dcs_orchestrator.interface import ScriptPipelineError, ScriptRequest
from dcs_providers.budget import RunBudget
from dcs_providers.errors import BudgetExceededError
from dcs_providers.ledger import InMemoryCostLedger
from dcs_providers.metering import MeteredChatModel, RunContext


async def test_approved_on_first_draft():
    writer = ScriptedChat(["Coffee shop angle", GOOD])
    reviewer = ScriptedChat([verdict(True)])
    result = await make(writer, reviewer).start(request())
    assert result.status == "approved"
    assert result.iterations == 1
    assert result.idea == "Coffee shop angle"
    assert [line.section for line in result.lines] == ["hook", "key_phrases"]


async def test_writer_receives_reviewer_notes_on_revision():
    writer = ScriptedChat(["idea", GOOD, GOOD])
    reviewer = ScriptedChat([verdict(False, "Add a polite greeting"), verdict(True)])
    result = await make(writer, reviewer).start(request())
    assert result.status == "approved" and result.iterations == 2
    assert "Add a polite greeting" in writer.prompts[2]
    assert "Add a polite greeting" not in writer.prompts[1]


async def test_template_violation_skips_reviewer_and_feeds_back():
    too_long = draft(("hook", " ".join(["word"] * 13)))
    writer = ScriptedChat(["idea", too_long, GOOD])
    reviewer = ScriptedChat([verdict(True)])
    result = await make(writer, reviewer).start(request())
    assert result.status == "approved" and result.iterations == 2
    assert len(reviewer.prompts) == 1
    assert "draft.line_too_long" in writer.prompts[2]


async def test_invalid_json_is_retried():
    writer = ScriptedChat(["idea", "oops", GOOD])
    reviewer = ScriptedChat([verdict(True)])
    result = await make(writer, reviewer).start(request())
    assert result.status == "approved" and result.iterations == 2


async def test_max_iterations_never_reports_approval():
    writer = ScriptedChat(["idea", GOOD, GOOD])
    reviewer = ScriptedChat([verdict(False, "n1"), verdict(False, "n2")])
    result = await make(writer, reviewer).start(request(max_iterations=2))
    assert result.status == "rejected_max_iterations"
    assert result.iterations == 2
    assert result.notes == ["n1", "n2"]
    assert len(result.lines) == 2  # last draft kept for the human


async def test_unparsable_reviewer_output_is_not_approval():
    writer = ScriptedChat(["idea", GOOD])
    reviewer = ScriptedChat(["looks great!"])
    result = await make(writer, reviewer).start(request(max_iterations=1))
    assert result.status == "rejected_max_iterations"


async def test_rejected_result_reflects_last_draft_not_a_stale_one():
    writer = ScriptedChat(["idea", GOOD, "not json"])
    reviewer = ScriptedChat([verdict(False, "n1")])
    result = await make(writer, reviewer).start(request(max_iterations=2))
    assert result.status == "rejected_max_iterations"
    assert result.lines == []


async def test_invalid_request_is_rejected():
    with pytest.raises(ScriptPipelineError) as exc:
        ScriptRequest(run_id="r", topic="t", template=request().template, max_iterations=0)
    assert exc.value.code == "script.invalid_request"
    with pytest.raises(ScriptPipelineError):
        ScriptRequest(run_id="r", topic="  ", template=request().template)


async def test_budget_error_propagates_and_is_metered():
    ledger = InMemoryCostLedger()
    ctx = RunContext(run_id="run-1", role="writer", budget=RunBudget(cap_usd=Decimal("0")))
    metered = MeteredChatModel(
        ScriptedChat(["idea"]), ledger, ctx, provider="openai", model="gpt-4o-mini"
    )
    with pytest.raises(BudgetExceededError):
        await make(metered, ScriptedChat([])).start(request())
