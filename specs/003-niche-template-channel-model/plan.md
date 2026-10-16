# Implementation Plan: Niche Template and Channel Model

**Spec**: [spec.md](spec.md) · **Constitution check**: I (gates cannot be disabled), IV (templates are data), V (test-first), VIII (error codes, bilingual UI) — satisfied.

## Technical Context

- New workspace package `packages/niche-templates` (`dcs-niche-templates`): Pydantic models + JSON data files under `src/dcs_niche_templates/data/<id>.v<N>.json`.
- API (`apps/api`): `channels.py` (SQLAlchemy Core table + repository), `routes/channels.py`, `routes/templates.py`, `ApiError` envelope handler. `create_app(probes, engine)` accepts an injected engine; tests use SQLite via `aiosqlite`.
- Migration `0003_channel` in `apps/api/alembic/versions`.
- Web (`apps/web`): `/[locale]/channels` server page, `ChannelList` and `ChannelForm` components, server actions calling the API, error-code → message mapping in the catalogs. Vitest component tests.
- Dockerfiles copy `packages/` as a whole so every workspace member exists for `uv sync --frozen` (also fixes the missing `packages/providers` from US-002).

## Data model

`channel(id uuid pk, name, template_id, template_version int, content_language, created_at, updated_at)`

## Complexity Tracking

None.
