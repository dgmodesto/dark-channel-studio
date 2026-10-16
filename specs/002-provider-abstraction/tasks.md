# Tasks: Provider Abstraction and Cost Tracking

**Tests**: Required and written first (constitution V).

## Phase 1: Setup
- [x] T001 Create `packages/providers` workspace package; register in root `pyproject.toml` (members, testpaths, isort); add `aiosqlite` dev dependency

## Phase 2: Tests first (must fail)
- [x] T002 [P] `test_pricing.py` — chat token and TTS character cost, unknown model unpriced
- [x] T003 [P] `test_fakes.py` — deterministic fakes with usage
- [x] T004 [P] `test_metering.py` — one cost_event per call, none on failure
- [x] T005 [P] `test_budget.py` — cap blocks further calls, runs independent
- [x] T006 [P] `test_registry.py` — role→adapter selection, error codes
- [x] T007 [P] `test_openai_chat.py`, `test_elevenlabs_tts.py` — mocked HTTP, secrets not leaked in errors
- [x] T008 [P] `test_sql_ledger.py` — persistence round-trip and run total

## Phase 3: Implementation
- [x] T009 protocols, errors, pricing
- [x] T010 ledger (+ Alembic `0002_cost_event`), budget, metering
- [x] T011 fakes, config, registry
- [x] T012 OpenAI and ElevenLabs adapters

## Phase 4: Close-out
- [x] T013 Lint + full test run; save evidence under `evidence/`
- [x] T014 Code review; update board; single commit; PR stacked on US-001
