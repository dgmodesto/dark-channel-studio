# Feature Specification: Niche Template and Channel Model

**Feature Branch**: `003-niche-template-channel-model` (board story US-003)

**Created**: 2026-10-16

**Status**: Implemented

**Input**: "Niche template + channel model: English A1/A2 template as data, channel CRUD in API and UI"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Niche behavior lives in versioned data (Priority: P1)

As the owner, I want the English A1/A2 channel's behavior (script structure, voice, subtitles, SEO rules, cadence, gates) defined as versioned data, so a new niche is a new data file and not a pipeline fork (constitution IV).

**Acceptance Scenarios**:

1. **Given** the shipped templates, **When** they are listed, **Then** `english-a1-a2-br` version 1 is present.
2. **Given** a template id without a version, **When** it is loaded, **Then** the latest version is returned.
3. **Given** an unknown id or version, **Then** a `template.not_found` error is raised.
4. **Given** template data that disables the human-approval or synthetic-disclosure gate, **Then** validation rejects it (constitution I, VIII).

### User Story 2 - Manage channels through the API (Priority: P1)

As the owner, I create, list, view, rename/re-template and delete channels; each channel references a template id and version.

**Acceptance Scenarios**:

1. **Given** a valid name and template id, **When** I create a channel, **Then** it is stored pinned to the latest template version with the template's content language.
2. **Given** an unknown template, **When** I create or update a channel, **Then** the API returns 422 `channel.template_unknown`.
3. **Given** an unknown channel id, **When** I get, update or delete it, **Then** the API returns 404 `channel.not_found`.
4. **Given** channels exist, **When** I list them, **Then** all are returned, newest first.
5. **Given** a channel, **When** I delete it, **Then** it is no longer listed.

### User Story 3 - Manage channels in the portal (Priority: P2)

As the owner, I see my channels in the portal, create one by choosing a template, and delete one, in English or Brazilian Portuguese.

**Acceptance Scenarios**:

1. **Given** channels exist, **When** I open `/en/channels` or `/pt-BR/channels`, **Then** they are listed with localized labels.
2. **Given** no channels, **Then** a localized empty state is shown.
3. **Given** the create form, **When** I submit a name and template, **Then** the channel is created through the API and shown.
4. **Given** the API returns an error code, **Then** the UI shows a localized message for that code.
5. **Given** the translation check, **Then** both catalogs have identical keys.

## Requirements *(mandatory)*

- **FR-001**: Templates are JSON data files in `packages/niche-templates`, validated by a Pydantic model; no niche logic in code.
- **FR-002**: Template `gates.human_approval` and `gates.synthetic_disclosure` must be `true`.
- **FR-003**: API exposes `GET /templates`, and `POST/GET/PATCH/DELETE /channels` (+ `GET /channels/{id}`).
- **FR-004**: A channel stores `template_id` and `template_version` (pinned), `content_language`, name, timestamps; persisted via migration `0003`.
- **FR-005**: API errors use `{code, params}`; the UI maps codes to localized messages (VIII).
- **FR-006**: Portal page at `/{locale}/channels` with list, create form and delete; the Channels nav item links to it.

## Success Criteria

- **SC-001**: API, template and web tests pass offline; lint, typecheck and the translation check pass.
- **SC-002**: Adding a template requires only a new data file.

## Assumptions

- Single owner, no auth yet. Channel names need not be unique. Template content language defaults the channel's content language; changing it per channel is out of scope.
- Out of scope: template editing UI, autonomy levels, pipeline use of templates (US-004+).
