# Implementation Plan: Review Player and Approval Gate

**Spec**: [spec.md](spec.md)

## Technical Context

- FastAPI stores review item metadata and decisions in Postgres; a new Alembic migration adds the table.
- `packages/orchestrator` adds an engine-agnostic human review gate backed by a LangGraph interrupt/checkpointer.
- The render worker automatically submits each successful render and its voice-track keys to the API review queue. The API serves those media keys through a path-confined file response from the shared local media root. Compose mounts the same named volume in API and worker.
- Next.js adds a locale-aware review queue page, server actions, video/audio controls, status and note feedback.

## Constitution Check

- I: graph blocks on an explicit owner decision before approval is recorded.
- II/III: deterministic media remains in worker; the human-gate interface is separate from the LangGraph adapter.
- V: tests are authored and run red before implementation; evidence is stored in this feature folder.
- VII: media is confined to a local root; no browser-exposed provider credentials or external service is introduced.
- VIII: API errors are codes and UI text is provided in English and Brazilian Portuguese.

## Complexity Tracking

The review metadata table complements LangGraph checkpoints so the UI can list runs without depending on checkpoint internals. No other new infrastructure is introduced.
