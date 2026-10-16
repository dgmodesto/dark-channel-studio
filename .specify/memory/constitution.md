# Dark Channel Studio Constitution

## Core Principles

### I. Human Gate by Default
Publishing is never unattended unless the channel's autonomy level explicitly allows it. Technical-review and policy/disclosure gates are never bypassed, at any autonomy level. Every pipeline that can spend money or publish content pauses on an interrupt and resumes only on an explicit decision.

### II. Agents Judge, Workers Execute
LLM agents (LangGraph) handle judgment: ideation, writing, review, SEO. Deterministic, idempotent, retryable jobs (Arq workers) handle TTS, render, upload and analytics sync. No LLM decision-making inside a worker; no heavy I/O inside an agent node (ADR-0002).

### III. Pluggable Providers and Orchestrator
All AI/media providers sit behind our own interfaces (`ChatModel`, `TTS`, `ImageGen`, ...), selected by configuration (ADR-0003). Only the LangGraph adapter imports `langgraph`; the rest of the system depends on the orchestrator interface (ADR-0001).

### IV. Niche Templates Are Data, Not Code
Niche-specific behavior (script structure, voice, subtitle style, SEO rules, CTAs, gates) lives in versioned template data under `packages/niche-templates`. Adding a niche must not require forking the pipeline.

### V. Test-First, Evidence-Backed (NON-NEGOTIABLE)
Tests are written before implementation and must fail first. Every user story closes with evidence (test output, screenshots, logs) stored under its `specs/<feature>/evidence/` folder and linked in the pull request. Provider calls are faked in tests; live-provider checks are opt-in.

### VI. Cost and Quota Awareness
Every LLM/TTS/image/render call records a `cost_event`. Runs and channels have enforced budgets; YouTube API quota is reserved before upload. Features that spend must expose their cost.

### VII. Secure and Self-Hosted
Local-first, single owner. Secrets only in `.env`/Docker secrets, never committed. OAuth tokens are encrypted at rest with minimal scopes; provider keys never reach the browser (ADR-0004).

### VIII. English Repository, Bilingual Product
All code, docs, commits, ADRs and specs are in English. The dashboard ships `en` and `pt-BR` catalogs from the first screen; the backend returns error codes and params, never localized strings. Content language is a channel setting independent of UI language (ADR-0005).

## Additional Constraints

- Stack: Python (FastAPI, LangGraph, LangChain as a thin layer, Arq), Next.js + next-intl, Postgres, Redis, Docker Compose, FFmpeg/Remotion for render.
- Compliance: no scraping, view-botting or policy-violating behavior; synthetic-content disclosure defaults to on; no personalized financial advice.
- Simplicity: start with the smallest agent topology that works (e.g. writer + reviewer loop with a bounded iteration count); complexity must be justified in the plan's Complexity Tracking section.

## Development Workflow

Each user story follows the Spec Kit lifecycle on its own branch:

1. `specify` → `clarify` (if needed) → `plan` → `tasks` → `analyze`
2. `implement` test-first, task by task
3. Test, then independent review (reviewer agent / code-review)
4. Collect evidence in `specs/<feature>/evidence/`
5. Open a PR with evidence, review, and merge

The local board (`board/BOARD.md`) is the source of truth for story status. Rule: **one commit per completed feature**, using Conventional Commits (`feat(US-00X): ...`), with the board updated in the same commit.

**Branching (OneBranch)**: `main` is the only long-lived branch. Every story branch is created from `main` and its PR targets `main`; no integration or stacked base branches. Dependent stories start only after their dependencies are merged into `main`.

## Governance

This constitution supersedes other practices. Amendments require a PR that explains the change, updates dependent templates/ADRs, and bumps the version. Every PR and review must check compliance with these principles; deviations must be justified in the plan.

**Version**: 1.1.0 | **Ratified**: 2026-10-16 | **Last Amended**: 2026-10-16
