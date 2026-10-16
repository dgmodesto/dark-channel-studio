# Implementation Plan: Provider Abstraction and Cost Tracking

**Spec**: [spec.md](spec.md) · **Constitution check**: III (pluggable providers), V (test-first, fakes), VI (cost awareness), VII (keys as secrets), VIII (error codes) — all satisfied.

## Technical Context

- Python 3.12, new workspace package `packages/providers` (`dcs-providers`), depends on `dcs-common`, `httpx`, `sqlalchemy[asyncio]`, `pydantic`.
- Vendor access via plain `httpx` REST calls (no vendor SDK, no LangChain yet: keeps the adapter layer small; LangChain may be added inside chat adapters later per ADR-0003). `httpx.AsyncClient` is injectable so tests use `httpx.MockTransport`.
- Storage: `cost_event` table (Alembic `0002`); tests use SQLite via `aiosqlite`.

## Structure

```text
packages/providers/src/dcs_providers/
  protocols.py   # Usage, ChatMessage, ChatResult, TTSResult, ChatModel, TTS
  errors.py      # ProviderError subclasses with stable codes
  pricing.py     # static price table, cost computation (Decimal)
  ledger.py      # CostEvent, CostLedger, InMemoryCostLedger, SqlCostLedger, cost_event table
  budget.py      # RunBudget
  metering.py    # RunContext, MeteredChatModel, MeteredTTS
  fakes.py       # FakeChatModel, FakeTTS
  config.py      # ProviderConfig (roles -> provider/model, secret keys)
  registry.py    # build_chat / build_tts
  adapters/openai_chat.py, adapters/elevenlabs_tts.py
apps/api/alembic/versions/0002_cost_event.py
```

## Key decisions

- Budget check happens before the call (spent >= cap blocks); the crossing call is recorded. Exact pre-call estimation is out of scope.
- Cost stored as `Numeric(12, 6)` USD; unknown models record cost 0 with `priced=false`.
- Failed provider calls record nothing.

## Complexity Tracking

None.
