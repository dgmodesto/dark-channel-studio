# Feature Specification: Provider Abstraction and Cost Tracking

**Feature Branch**: `002-provider-abstraction` (board story US-002)

**Created**: 2026-10-16

**Status**: Implemented

**Input**: "Provider abstraction + cost tracking: `ChatModel`/`TTS` protocols, OpenAI + ElevenLabs adapters, fakes, `cost_event`"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pipelines call providers by role (Priority: P1)

As a pipeline author, I request a chat model or TTS voice by role (for example `script_writer`) and get an object satisfying our own `ChatModel` / `TTS` protocol, so vendors can be swapped by configuration only (ADR-0003).

**Independent Test**: Build adapters from configuration with fake credentials and verify the right class is returned per role; an unknown provider fails with a clear error code.

**Acceptance Scenarios**:

1. **Given** config maps `script_writer` to `openai/gpt-4o-mini`, **When** a chat model is built for that role, **Then** an OpenAI chat adapter for that model is returned.
2. **Given** config maps `narrator` to `elevenlabs/<voice>`, **When** a TTS is built for that role, **Then** an ElevenLabs adapter is returned.
3. **Given** config maps a role to `fake/...`, **When** built, **Then** a deterministic fake is returned and no network is used.
4. **Given** a role is unmapped or the provider is unknown, **Then** a configuration error with a stable code is raised.

### User Story 2 - Every call is costed (Priority: P1)

As the owner, I can see what each run spent: every chat/TTS call writes a `cost_event` with run, role, provider, model, usage units and cost in USD.

**Acceptance Scenarios**:

1. **Given** a metered chat call, **When** it completes, **Then** one `cost_event` exists with token usage and computed cost.
2. **Given** a metered TTS call, **When** it completes, **Then** one `cost_event` exists with character usage and computed cost.
3. **Given** a provider call fails, **Then** no cost is recorded and the error propagates.

### User Story 3 - Per-run budget cap (Priority: P1)

As the owner, I set a per-run budget; once spend reaches the cap, further calls are refused before reaching the provider.

**Acceptance Scenarios**:

1. **Given** a run with spend below the cap, **When** a call is made, **Then** it proceeds and its cost counts against the budget.
2. **Given** a run whose spend has reached the cap, **When** another call is made, **Then** `budget.exceeded` is raised and the provider is not called.
3. **Given** two runs, **Then** their budgets are tracked independently.

## Requirements *(mandatory)*

- **FR-001**: `ChatModel` and `TTS` are structural protocols returning results that include usage.
- **FR-002**: Adapters are selected by role from configuration (`provider/model`); pipelines never import vendor adapters.
- **FR-003**: OpenAI chat adapter and ElevenLabs TTS adapter talk to vendor HTTP APIs; API keys are `SecretStr` and never logged or put in errors.
- **FR-004**: Deterministic fakes exist for both protocols; tests never call real providers.
- **FR-005**: A metering decorator writes one `cost_event` per successful call via a `CostLedger` (in-memory and SQL implementations).
- **FR-006**: `cost_event` is persisted in Postgres via migration `0002`.
- **FR-007**: A `RunBudget` blocks calls once recorded spend >= cap, raising `BudgetExceededError` (`budget.exceeded`). The call that crosses the cap is recorded (cost was incurred); subsequent calls are blocked.
- **FR-008**: Errors expose stable codes and parameters, never localized strings.

## Success Criteria

- **SC-001**: All provider tests pass offline.
- **SC-002**: Swapping a role's provider requires only a config change.
- **SC-003**: Lint and full test suite pass in CI.

## Assumptions

- Price table is static and versioned in code; unknown models cost 0 and are flagged `priced=false` on the event.
- Out of scope: image generation, per-channel budgets, UI for costs (US-011), live-provider tests (opt-in later).
