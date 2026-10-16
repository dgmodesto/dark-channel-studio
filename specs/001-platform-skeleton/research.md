# Research: Platform Skeleton

Decisions made while planning US-001. Versions are pinned by lockfiles at implementation time; check current stable releases then.

## Health and heartbeat
- **Decision**: API probes Postgres (`SELECT 1`) and Redis (`PING`) concurrently with 1 s timeouts; worker liveness is a Redis key with TTL written by an Arq cron job.
- **Rationale**: Reuses infrastructure already present; no extra service; TTL expiry makes a dead worker visible without polling logic.
- **Alternatives**: Arq's built-in health check key (rejected: coupled to Arq internals, harder to assert in tests); a dedicated worker HTTP port (rejected: extra surface for no gain).

## Startup readiness
- **Decision**: Compose healthchecks with `service_healthy` plus application-level retry with exponential backoff.
- **Rationale**: Compose ordering alone does not cover restarts of a dependency after startup.
- **Alternatives**: wait-for scripts (rejected: duplicates healthchecks).

## Python layout
- **Decision**: `uv`-managed packages with path dependency on `packages/common`; ruff for lint/format; pytest for tests.
- **Rationale**: Fast, reproducible installs; single tool for lint+format.
- **Alternatives**: Poetry (rejected: slower, no benefit here); single Python package (rejected: API and worker deploy and scale separately per ADR-0002).

## Portal i18n
- **Decision**: next-intl, App Router, `localePrefix: always`, middleware locale negotiation.
- **Rationale**: Matches ADR-0005; ICU formatting available for later features.
- **Alternatives**: react-i18next (rejected: weaker App Router/server component story).

## Translation completeness check
- **Decision**: A small Node script comparing flattened key sets of `messages/en.json` and `messages/pt-BR.json`, run in CI and as an npm script.
- **Rationale**: Deterministic, no dependency, names missing keys (FR-011).

## Database migrations
- **Decision**: Alembic with an empty baseline revision now, so later stories only add revisions.
- **Rationale**: Establishes the migration workflow early; avoids schema in a story that has no domain data.

## CI evidence
- **Decision**: The compose smoke job uploads logs and the health JSON as artifacts; the same output is copied into `evidence/` for the PR.
- **Rationale**: Satisfies the constitution's evidence rule.
