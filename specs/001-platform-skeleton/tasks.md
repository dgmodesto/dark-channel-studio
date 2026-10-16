# Tasks: Platform Skeleton

**Input**: Design documents from `specs/001-platform-skeleton/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/health.md

**Tests**: Required (constitution principle V): test tasks come first and must fail before implementation.

**Format**: `[ID] [P?] [Story] Description` — `[P]` = parallelizable (different files, no dependencies).

Stories: **US1** one-command start and health · **US2** bilingual portal · **US3** automated verification

## Phase 1: Setup

- [x] T001 Create `packages/common` Python package (`pyproject.toml`, `src/dcs_common/__init__.py`) and wire path dependency in `apps/api/pyproject.toml` and `apps/worker/pyproject.toml`
- [x] T002 [P] Configure ruff, pytest and uv lock for Python packages (root `pyproject.toml` tool config)
- [x] T003 [P] Scaffold Next.js App Router project in `apps/web` (TypeScript, ESLint, Vitest, Testing Library)
- [x] T004 [P] Create `deploy/.env.example` with every variable from `data-model.md`

## Phase 2: Foundational (blocks all stories)

- [x] T005 [P] Test first: `packages/common/tests/test_settings.py` — missing required var raises error naming the variable and never its value (FR-006)
- [x] T006 Implement `packages/common/src/dcs_common/settings.py` (Pydantic Settings)
- [x] T007 [P] Test first: `packages/common/tests/test_logging.py` — JSON logs include nullable `correlation_id`, `run_id`, `video_id`, `channel_id` (FR-014)
- [x] T008 Implement `packages/common/src/dcs_common/logging.py` (structlog + context vars)
- [x] T009 [P] Test first: `packages/common/tests/test_retry.py` — connect retry with backoff succeeds after transient failures and gives up after the limit (FR-004)
- [x] T010 Implement retry helper in `packages/common/src/dcs_common/retry.py`

**Checkpoint**: shared Python foundation green.

## Phase 3: User Story 1 — One-command start and health (P1)

**Independent test**: run the compose smoke script; all components healthy; stopping Postgres yields 503 with reason.

### Tests first
- [x] T011 [P] [US1] `packages/common/tests/test_health.py` — probes return `healthy`/`unhealthy` with reason codes `timeout`, `connection_refused`, `error`; each respects the 1 s timeout
- [x] T012 [P] [US1] `apps/api/tests/test_health_route.py` — contract tests per `contracts/health.md` (200 all healthy, 503 database down, worker missing is informational, complete body, error envelope shape)
- [x] T013 [P] [US1] `apps/worker/tests/test_heartbeat.py` — job writes `dcs:worker:heartbeat` ISO timestamp with TTL 30 s
- [x] T014 [US1] `deploy/scripts/smoke.ps1` and `smoke.sh` — fail-first smoke test: waits for `/health`, asserts all components healthy, response under 2 s, portal responds

### Implementation
- [x] T015 [US1] Implement probes in `packages/common/src/dcs_common/health.py`
- [x] T016 [US1] Implement API app: `apps/api/src/dcs_api/main.py`, `db.py`, `routes/health.py`, error envelope handler
- [x] T017 [P] [US1] Implement worker: `apps/worker/src/dcs_worker/settings.py` and `jobs/heartbeat.py` (Arq cron every 10 s)
- [x] T018 [P] [US1] Alembic baseline (empty revision) in `apps/api/alembic/`
- [x] T019 [P] [US1] `apps/api/Dockerfile` and `apps/worker/Dockerfile`
- [x] T020 [US1] `deploy/compose.yaml`: postgres, redis (AOF), api, worker, web; healthchecks; `service_healthy` ordering; named volumes; ports bound to `127.0.0.1` and overridable (FR-001, FR-007, edge cases)
- [x] T021 [P] [US1] `deploy/scripts/reset.ps1` and `reset.sh` with confirmation (FR-007)
- [x] T022 [US1] Run smoke test and the three quickstart validation scenarios; save output to `specs/001-platform-skeleton/evidence/us1-*.txt`

## Phase 4: User Story 2 — Bilingual portal (P1)

**Independent test**: open `/en` and `/pt-BR`, switch language, run `npm run check:translations`.

### Tests first
- [x] T023 [P] [US2] `apps/web/tests/check-translations.test.ts` — script passes on parity and fails naming a missing key (FR-011)
- [x] T024 [P] [US2] `apps/web/tests/shell.test.tsx` — shell renders in `en` and `pt-BR` from catalogs; no hard-coded strings
- [x] T025 [P] [US2] `apps/web/tests/locale-switcher.test.tsx` — switcher preserves the current path
- [x] T026 [P] [US2] `apps/web/tests/middleware.test.ts` — root redirects by `Accept-Language`, unsupported language falls back to `en`

### Implementation
- [x] T027 [US2] `apps/web/messages/en.json` and `pt-BR.json` (shell, nav placeholders, status placeholder, language names)
- [x] T028 [US2] next-intl setup: `src/i18n/{routing,request,navigation}.ts`, `src/middleware.ts`, `localePrefix: always`
- [x] T029 [US2] `src/app/[locale]/layout.tsx`, `page.tsx` shell with product name, status placeholder (reads API `/health`), navigation placeholders
- [x] T030 [US2] `src/components/LocaleSwitcher.tsx`
- [x] T031 [P] [US2] `apps/web/scripts/check-translations.mjs` and `check:translations` npm script
- [x] T032 [P] [US2] `apps/web/Dockerfile`
- [x] T033 [US2] Capture screenshots of `/en` and `/pt-BR` and test output into `evidence/us2-*`

## Phase 5: User Story 3 — Automated verification (P2)

**Independent test**: a PR with a deliberately broken check fails; a clean PR passes.

- [x] T034 [US3] `.github/workflows/ci.yml`: jobs `python` (ruff, pytest), `web` (lint, typecheck, vitest, translation check), `compose-smoke` (build, up, smoke, upload logs and health JSON as artifacts, always tear down) (FR-012)
- [x] T035 [US3] Verify failure path: push a temporary commit that breaks a translation key; confirm CI fails, then revert; record run links in `evidence/us3-ci.md`

## Phase 6: Polish and delivery

- [x] T036 [P] Root `README.md`: prerequisites, start command, health checks, reset procedure, link to quickstart (FR-013)
- [x] T037 [P] Update `docs/design.md` section 14 status and add notes if any decision changed
- [x] T038 Run `/speckit.analyze`; fix any inconsistencies across spec, plan, tasks
- [x] T039 Code review (reviewer agent); address findings
- [x] T040 Assemble PR body with evidence links (SC-001..SC-006 mapping)
- [x] T041 Update `board/BOARD.md` (US-001 → Done) and make the single feature commit `feat(US-001): platform skeleton`

## Dependencies and order

- Phase 1 → Phase 2 → Phases 3 and 4 (independent of each other; US1 first, since the portal status placeholder reads `/health`) → Phase 5 (needs US1 smoke and US2 check) → Phase 6.
- Within each story: tests (fail) → implementation → evidence.
- Task T020 (compose) needs T019 and T032 images; T014 smoke can be written earlier but only passes after T020.

## Requirement coverage

| Requirement | Tasks |
|---|---|
| FR-001, FR-007 | T020, T021 |
| FR-002 | T011, T012, T015, T016 |
| FR-003 | T013, T017 |
| FR-004 | T009, T010, T020 |
| FR-005, FR-006 | T004, T005, T006 |
| FR-008, FR-009, FR-010 | T024–T030 |
| FR-011 | T023, T031 |
| FR-012 | T034, T035 |
| FR-013 | T036 |
| FR-014 | T007, T008 |
