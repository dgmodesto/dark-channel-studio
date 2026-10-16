from decimal import Decimal

import pytest

from dcs_providers.fakes import FakeChatModel, FakeTTS
from dcs_providers.ledger import InMemoryCostLedger
from dcs_providers.metering import MeteredChatModel, MeteredTTS, RunContext
from dcs_providers.protocols import ChatMessage, Usage

MSG = [ChatMessage(role="user", content="hi")]


def _ctx(run_id="run-1"):
    return RunContext(run_id=run_id, role="script_writer", channel_id="ch-1")


async def test_chat_call_writes_one_cost_event():
    ledger = InMemoryCostLedger()
    chat = MeteredChatModel(FakeChatModel(), ledger, _ctx(), provider="openai", model="gpt-4o-mini")
    await chat.complete(MSG)
    [event] = ledger.events
    assert (event.run_id, event.role, event.kind) == ("run-1", "script_writer", "chat")
    assert (event.provider, event.model, event.priced) == ("openai", "gpt-4o-mini", True)
    assert event.input_tokens > 0 and event.cost_usd > 0


async def test_tts_call_writes_one_cost_event():
    ledger = InMemoryCostLedger()
    tts = MeteredTTS(FakeTTS(), ledger, _ctx(), provider="elevenlabs", model="v")
    await tts.synthesize("hello")
    [event] = ledger.events
    assert event.kind == "tts" and event.characters == 5
    assert event.cost_usd == Decimal("0.00090")


async def test_failed_call_records_nothing():
    class Boom:
        async def complete(self, messages):
            raise RuntimeError("down")

    ledger = InMemoryCostLedger()
    chat = MeteredChatModel(Boom(), ledger, _ctx(), provider="openai", model="gpt-4o-mini")
    with pytest.raises(RuntimeError):
        await chat.complete(MSG)
    assert ledger.events == []


async def test_usage_defaults():
    assert Usage().input_tokens == 0
