# Tasks: Niche Template and Channel Model

**Tests**: written first and seen failing (constitution V).

## Phase 1: Setup
- [x] T001 Create `packages/niche-templates` workspace package; add as `dcs-api` dependency; Dockerfiles copy `packages/`

## Phase 2: Tests first
- [x] T002 [P] `packages/niche-templates/tests/test_templates.py` — list, latest, not found, gate validation
- [x] T003 [P] `apps/api/tests/test_channels.py` — CRUD, template validation, error codes, ordering
- [x] T004 [P] `apps/web/tests/channels.test.tsx` — list, empty state, form, error mapping in both locales

## Phase 3: Implementation
- [x] T005 Template models, loader and `english-a1-a2-br.v1.json`
- [x] T006 Channel table, repository, migration `0003`, routes, error handler
- [x] T007 Web page, components, server actions, en/pt-BR catalogs, nav link

## Phase 4: Close-out
- [x] T008 Lint, tests, typecheck, translation check; evidence
- [x] T009 Code review; board; single commit; PR stacked on US-002 branch
