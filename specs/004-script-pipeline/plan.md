# Implementation Plan: Script Pipeline

**Spec**: [spec.md](spec.md) · **Constitution check**: II (judgment in agent nodes, no heavy I/O), III (LangGraph confined to one adapter), IV (template drives behavior), V (test-first), VI (metered models), simplicity (single writer + reviewer loop, bounded) — satisfied.

## Technical Context

- New workspace package `packages/orchestrator` (`dcs-orchestrator`), depends on `dcs-providers`, `dcs-niche-templates`, `langgraph`, `langgraph-checkpoint-postgres`, `psycopg[binary]`.
- Layout under `src/dcs_orchestrator/`:
  - `interface.py` — `ScriptRequest`, `ScriptResult`, `ScriptLine`, `ScriptStatus`, `ScriptOrchestrator` protocol, `ScriptPipelineError`.
  - `checks.py` — pure template validation of a draft.
  - `prompts.py` — prompt builders from template data.
  - `adapters/langgraph_script.py` — the only module importing `langgraph`; `LangGraphScriptOrchestrator` and the `postgres_checkpointer(dsn)` async context manager.
- State is a JSON-serializable `TypedDict` (template stored as a dict) so any checkpointer works.
- No app imports the package yet (API/worker wiring lands with later stories); when one does, it must list `dcs-orchestrator` in its dependencies and `[tool.uv.sources]`, and `uv.lock` must be refreshed. Dockerfiles already copy `packages/`.

## Graph

`idea` (writer model brainstorms an angle) → `write` (JSON lines, receives prior feedback) → `review` (deterministic checks, then LLM reviewer) → conditional: approved → END; `iteration >= max_iterations` → END (`rejected_max_iterations`); else → `write`.

## Complexity Tracking

None. Reviewer is a separate `ChatModel` instance so it can use a different model/role in cost events.
