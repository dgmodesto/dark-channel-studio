from dataclasses import dataclass

from dcs_providers.budget import RunBudget
from dcs_providers.ledger import CostEvent, CostLedger
from dcs_providers.pricing import chat_cost, tts_cost
from dcs_providers.protocols import TTS, ChatMessage, ChatModel, ChatResult, TTSResult


@dataclass
class RunContext:
    run_id: str
    role: str
    channel_id: str | None = None
    budget: RunBudget | None = None


async def _finish(ctx: RunContext, ledger: CostLedger, event: CostEvent) -> None:
    # Count spend first: the provider call is already billed even if the ledger write fails.
    if ctx.budget is not None:
        ctx.budget.add(event.cost_usd)
    await ledger.record(event)


class MeteredChatModel:
    def __init__(
        self, inner: ChatModel, ledger: CostLedger, ctx: RunContext, *, provider: str, model: str
    ):
        self._inner, self._ledger, self._ctx = inner, ledger, ctx
        self._provider, self._model = provider, model

    async def complete(self, messages: list[ChatMessage]) -> ChatResult:
        if self._ctx.budget is not None:
            self._ctx.budget.check(self._ctx.run_id)
        result = await self._inner.complete(messages)
        cost, priced = chat_cost(
            self._provider,
            self._model,
            input_tokens=result.usage.input_tokens,
            output_tokens=result.usage.output_tokens,
        )
        await _finish(
            self._ctx,
            self._ledger,
            CostEvent(
                run_id=self._ctx.run_id,
                channel_id=self._ctx.channel_id,
                role=self._ctx.role,
                kind="chat",
                provider=self._provider,
                model=self._model,
                input_tokens=result.usage.input_tokens,
                output_tokens=result.usage.output_tokens,
                cost_usd=cost,
                priced=priced,
            ),
        )
        return result


class MeteredTTS:
    def __init__(
        self, inner: TTS, ledger: CostLedger, ctx: RunContext, *, provider: str, model: str
    ):
        self._inner, self._ledger, self._ctx = inner, ledger, ctx
        self._provider, self._model = provider, model

    async def synthesize(self, text: str, *, voice: str | None = None) -> TTSResult:
        if self._ctx.budget is not None:
            self._ctx.budget.check(self._ctx.run_id)
        result = await self._inner.synthesize(text, voice=voice)
        cost, priced = tts_cost(self._provider, self._model, characters=result.usage.characters)
        await _finish(
            self._ctx,
            self._ledger,
            CostEvent(
                run_id=self._ctx.run_id,
                channel_id=self._ctx.channel_id,
                role=self._ctx.role,
                kind="tts",
                provider=self._provider,
                model=self._model,
                characters=result.usage.characters,
                cost_usd=cost,
                priced=priced,
            ),
        )
        return result
