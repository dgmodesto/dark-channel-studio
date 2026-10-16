# Implementation Plan: Platform Skeleton

**Branch**: `001-platform-skeleton` | **Date**: 2026-10-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-platform-skeleton/spec.md` (board story US-001)

## Summary

Deliver a runnable walking skeleton: one `docker compose up` starts Postgres, Redis, a FastAPI service, an Arq worker and a Next.js portal. The API exposes a dependency-aware health endpoint, the worker publishes a Redis heartbeat, the portal serves locale-prefixed `en` / `pt-BR` shells with a language switcher, and GitHub Actions runs lint, tests and a translation-completeness check. No domain features yet.

## Technical Context

**Language/Version**: Python 3.12 (API, worker, shared package); TypeScript 5 on Node 22 LTS (portal)

**Primary Dependencies**: FastAPI, Uvicorn, Pydantic Settings, SQLAlchemy 2 (async) + asyncpg, Alembic (empty baseline), Arq, redis-py, structlog; Next.js (App Router), next-intl

**Storage**: PostgreSQL (domain data, later checkpoints), Redis (queue, heartbeat). Local named volumes.

**Testing**: pytest + pytest-asyncio + httpx (API, worker); Vitest + Testing Library (portal); a Node script for translation key parity; a Compose smoke test script (PowerShell and bash)

**Target Platform**: Linux containers via Docker Compose, developed on Windows/macOS/Linux

**Project Type**: Monorepo web application (apps/api, apps/worker, apps/web, packages/common)

**Performance Goals**: health response < 2 s including dependency probes (SC-002); full stack healthy < 5 min from fresh clone (SC-001)

**Constraints**: localhost-bound ports by default; config only from environment; no secrets in logs or git; dependencies wait/retry on startup

**Scale/Scope**: single owner, 5 containers, 2 locales, ~4 portal routes (shell only)

## Constitution Check

*GATE: passed before research; re-checked after design.*

| Principle | Status | Notes |
|---|---|---|
| I. Human gate by default | N/A | No publishing in this story |
| II. Agents judge, workers execute | Pass | Worker skeleton has only deterministic heartbeat job; no LLM code |
| III. Pluggable providers/orchestrator | Pass | No provider or `langgraph` import introduced; package layout leaves room for adapters |
| IV. Niche templates as data | N/A | `packages/niche-templates` untouched |
| V. Test-first, evidence | Pass | Tasks order tests before implementation; evidence in `specs/001-platform-skeleton/evidence/` |
| VI. Cost and quota awareness | N/A | No spending calls |
| VII. Secure and self-hosted | Pass | `.env.example` only, localhost bind, secret-free config errors |
| VIII. English repo, bilingual product | Pass | next-intl, key-parity CI check, error codes not strings |

## Project Structure

### Documentation (this feature)

```text
specs/001-platform-skeleton/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── health.md
├── checklists/requirements.md
├── evidence/            # filled during implementation
└── tasks.md             # /speckit.tasks
```

### Source Code (repository root)

```text
packages/
└── common/                      # shared Python: settings, logging, health probes
    ├── pyproject.toml
    ├── src/dcs_common/
    │   ├── settings.py
    │   ├── logging.py
    │   └── health.py
    └── tests/
apps/
├── api/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── alembic/ (empty baseline) + alembic.ini
│   ├── src/dcs_api/{main.py,routes/health.py,db.py}
│   └── tests/
├── worker/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── src/dcs_worker/{settings.py,jobs/heartbeat.py}
│   └── tests/
└── web/
    ├── package.json, Dockerfile, next.config.ts
    ├── messages/{en.json,pt-BR.json}
    ├── src/{i18n/,middleware.ts,app/[locale]/...,components/}
    ├── scripts/check-translations.mjs
    └── tests/
deploy/
├── compose.yaml
├── .env.example                 # (also copied to repo root .env.example reference)
└── scripts/{smoke.ps1,smoke.sh,reset.ps1,reset.sh}
.github/workflows/ci.yml
```

**Structure Decision**: Use the existing `apps/*` and `packages/*` skeleton. Shared Python code lives in `packages/common`, installed as a path dependency by API and worker, so config, logging and health probes are written once. Compose files live in `deploy/`.

## Key Design Decisions

1. **Health model**: API `/health` returns overall status plus per-component results (`api`, `database`, `redis`, `worker`). Dependency probes run concurrently with a 1 s timeout each. HTTP 200 when API is up and all required dependencies are healthy; 503 otherwise, body always complete. Contract in `contracts/health.md`.
2. **Worker heartbeat**: an Arq cron job writes `dcs:worker:heartbeat` (ISO timestamp, TTL 30 s) every 10 s. API reports `worker` healthy when the key exists. Worker unhealthy does not fail the API's own liveness.
3. **Startup ordering**: Compose `depends_on` with `condition: service_healthy` plus in-app connect retry with backoff (FR-004).
4. **Config**: Pydantic Settings reads env; a missing required value raises a validation error that names the variable but never echoes values (FR-006). `.env.example` lists every variable.
5. **i18n**: next-intl with `localePrefix: always`, middleware negotiating `Accept-Language` with `en` fallback, a `LocaleSwitcher` using the locale-aware navigation helpers to preserve the path. `scripts/check-translations.mjs` fails on any key present in one catalog but not the other.
6. **API errors**: error envelope `{ "code": "...", "params": {} }`; no localized text (FR-010).
7. **Logging**: structlog JSON with `correlation_id`, `run_id`, `video_id`, `channel_id` fields (nullable) bound via context vars (FR-014).
8. **Persistence & reset**: named volumes for Postgres and Redis (Redis AOF on); `reset` scripts run `compose down -v` after confirmation (FR-007).
9. **CI**: GitHub Actions jobs `python` (ruff, mypy-light, pytest), `web` (lint, typecheck, vitest, translation check), `compose-smoke` (build, up, smoke script, tear down). Smoke output uploaded as an artifact to serve as evidence.
10. **Network exposure**: Compose publishes ports on `127.0.0.1` only; ports overridable via env (edge case).

## Complexity Tracking

No constitution violations. A shared `packages/common` package is the only addition beyond the existing skeleton; it avoids duplicating settings/logging/health code across two Python services.
