from decimal import Decimal

import pytest

from dcs_providers.budget import RunBudget
from dcs_providers.errors import BudgetExceededError
from dcs_providers.ledger import InMemoryCostLedger
from dcs_providers.metering import MeteredTTS, RunContext
from dcs_providers.protocols import TTSResult, Usage


class SpyTTS:
    def __init__(self):
        self.calls = 0

    async def synthesize(self, text, *, voice=None):
        self.calls += 1
        return TTSResult(audio=b"a", usage=Usage(characters=len(text)))


def _tts(inner, ledger, budget, run_id):
    ctx = RunContext(run_id=run_id, role="narrator", budget=budget)
    return MeteredTTS(inner, ledger, ctx, provider="elevenlabs", model="v")


async def test_cap_blocks_after_reached_without_calling_provider():
    ledger, inner = InMemoryCostLedger(), SpyTTS()
    tts = _tts(inner, ledger, RunBudget(cap_usd=Decimal("0.18")), "r1")
    await tts.synthesize("x" * 1000)  # costs exactly 0.18, reaching the cap
    with pytest.raises(BudgetExceededError) as exc:
        await tts.synthesize("again")
    assert exc.value.code == "budget.exceeded"
    assert inner.calls == 1
    assert len(ledger.events) == 1


async def test_call_below_cap_proceeds():
    tts = _tts(SpyTTS(), InMemoryCostLedger(), RunBudget(cap_usd=Decimal("1")), "r1")
    await tts.synthesize("x" * 1000)
    await tts.synthesize("x" * 1000)


async def test_runs_have_independent_budgets():
    ledger = InMemoryCostLedger()
    a = _tts(SpyTTS(), ledger, RunBudget(cap_usd=Decimal("0.01")), "a")
    b = _tts(SpyTTS(), ledger, RunBudget(cap_usd=Decimal("0.01")), "b")
    await a.synthesize("x" * 1000)
    with pytest.raises(BudgetExceededError):
        await a.synthesize("x")
    await b.synthesize("x")


def test_budget_remaining():
    budget = RunBudget(cap_usd=Decimal("1"))
    budget.add(Decimal("0.25"))
    assert budget.spent_usd == Decimal("0.25") and budget.remaining_usd == Decimal("0.75")
