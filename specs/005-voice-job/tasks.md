# Tasks: Voice Job

**Tests**: written first and seen failing (constitution V); red-phase output in `evidence/red-phase.txt`.

## Phase 1: Setup
- [x] T001 Add `dcs-providers`, `dcs-niche-templates` to `apps/worker` dependencies and `[tool.uv.sources]`; refresh `uv.lock`

## Phase 2: Tests first
- [x] T002 [P] `apps/worker/tests/test_voice_synthesize.py` — per-line audio, manifest, validation, idempotency, partial resume, retry, budget not retried, key sensitivity
- [x] T003 [P] `apps/worker/tests/test_voice_pauses.py` — pauses from the English template, custom/zero pause, pause change without re-synthesis
- [x] T004 [P] `apps/worker/tests/test_voice_store.py` — local store round trip, path safety
- [x] T005 [P] `apps/worker/tests/test_voice_job.py` — Arq job payload → manifest, registered in `WorkerSettings`
- [x] T006 [P] niche-templates test for `shadowing_sections`

## Phase 3: Implementation
- [x] T007 Template model + data (`shadowing_sections`)
- [x] T008 `voice` package (models, store, synthesize)
- [x] T009 Arq job and worker wiring

## Phase 4: Close-out
- [x] T010 Lint, full tests; evidence
- [x] T011 Code review; board; single commit; PR on `dgmodesto-spec-kit-workflow-setup`
