# Feature Specification: Script Pipeline

**Feature Branch**: `004-script-pipeline` (board story US-004)

**Created**: 2026-10-16

**Status**: Implemented

**Input**: "Script pipeline: LangGraph writer + reviewer loop with bounded iterations and Postgres checkpoints"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Approved script from a topic (Priority: P1)

As the owner, I give the pipeline a topic and a niche template, and it produces a script that respects the template (sections, line count, words per line) after an idea → write → review loop.

**Acceptance Scenarios**:

1. **Given** a topic and the English A1/A2 template, **When** the pipeline runs and the reviewer approves the first draft, **Then** the result is `approved` with the script lines and 1 iteration.
2. **Given** the reviewer requests changes, **When** the writer is called again, **Then** it receives the reviewer's notes and the result carries the revised script.
3. **Given** a draft that violates the template (too many lines, too many words in a line, unknown section, invalid JSON), **Then** it is rejected by deterministic checks without spending a reviewer call, and the violation is fed back to the writer.
4. **Given** the reviewer never approves, **When** `max_iterations` is reached, **Then** the result is `rejected_max_iterations`, keeps the last draft and notes, and never reports an approved script (constitution I: a human decides next).

### User Story 2 - Resumable runs (Priority: P1)

As the owner, I want an interrupted run (crash, provider outage, restart) to continue from its last checkpoint instead of starting over and paying again.

**Acceptance Scenarios**:

1. **Given** a run that failed during the first write, **When** a new orchestrator instance (new process) resumes the same run id against the same checkpoint store, **Then** the idea step is not repeated and the run completes.
2. **Given** a finished run, **When** its state is requested, **Then** the final result is returned without calling any model.
3. **Given** an unknown run id, **When** its state is requested, **Then** `None` is returned and resuming raises `script.run_not_found`.

### User Story 3 - LangGraph stays behind an interface (Priority: P2)

As a maintainer, I want callers to depend on a `ScriptOrchestrator` protocol so the orchestration engine can be swapped (constitution III, ADR-0001).

**Acceptance Scenarios**:

1. **Given** the package, **Then** only `dcs_orchestrator.adapters.langgraph_script` imports `langgraph`, enforced by a test.
2. **Given** the LangGraph adapter, **Then** it satisfies the `ScriptOrchestrator` protocol.

## Requirements *(mandatory)*

- **FR-001**: Workspace package `packages/orchestrator` (`dcs-orchestrator`) exposes `ScriptOrchestrator`, `ScriptRequest`, `ScriptResult`, `ScriptLine`, `ScriptStatus`.
- **FR-002**: The graph is `idea → write → review`, looping review → write while not approved and `iteration < max_iterations` (default 3, must be ≥ 1).
- **FR-003**: Review runs deterministic template checks first; the LLM reviewer is called only when they pass and must answer JSON `{"approved": bool, "notes": str}`; unparsable reviewer output counts as not approved.
- **FR-004**: Agents use only `ChatModel` (US-002); callers pass metered models so every call records a `cost_event` and obeys the run budget (constitution VI). `BudgetExceededError` and provider errors propagate and leave the run resumable.
- **FR-005**: The run id is the LangGraph thread id; state is checkpointed after every node. `postgres_checkpointer(dsn)` builds a Postgres-backed saver; any LangGraph saver can be injected (in-memory in tests).
- **FR-006**: Template data (limits, sections, language, level) drives prompts and checks; no niche-specific logic in code (constitution IV).
- **FR-007**: Errors carry codes (`script.run_not_found`, `script.run_exists`, `script.invalid_request`), not localized strings (constitution VIII).
- **FR-008**: `ScriptResult.lines` always reflects the last draft produced (empty if it could not be parsed), never an earlier one.

## Success Criteria

- **SC-001**: All tests pass offline using scripted fake chat models and the shipped template; lint passes.
- **SC-002**: Killing the pipeline mid-run and resuming it with a fresh orchestrator does not repeat completed steps.

## Assumptions

- Persistence in production is Postgres via `langgraph-checkpoint-postgres`; tests use the in-memory saver sharing one store between two orchestrator instances to model a restart. A live Postgres check is opt-in.
- Out of scope: API/worker endpoints and queueing, the human approval interrupt (US-007), voice/render (US-005/006), SEO (US-008).
