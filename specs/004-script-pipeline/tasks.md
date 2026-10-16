# Tasks: Script Pipeline

**Tests**: written first and seen failing (constitution V); red-phase output in `evidence/red-phase.txt`.

## Phase 1: Setup
- [x] T001 Create `packages/orchestrator` workspace package, register in root `pyproject.toml` (workspace, ruff isort, pytest testpaths); refresh `uv.lock`

## Phase 2: Tests first
- [x] T002 [P] `tests/test_checks.py` — template validation (lines, words, sections, empty, JSON)
- [x] T003 [P] `tests/test_pipeline.py` — approve, revise with notes, deterministic reject skips reviewer, max iterations, invalid reviewer output, budget error propagation
- [x] T004 [P] `tests/test_resume.py` — resume after failure without repeating idea, finished state, unknown run
- [x] T005 [P] `tests/test_boundaries.py` — only the adapter imports `langgraph`; protocol conformance

## Phase 3: Implementation
- [x] T006 Interface, checks, prompts
- [x] T007 LangGraph adapter and Postgres checkpointer factory

## Phase 4: Close-out
- [x] T008 Lint, full tests; evidence
- [x] T009 Code review; board; single commit; PR on `dgmodesto-spec-kit-workflow-setup`
