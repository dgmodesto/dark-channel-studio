# Feature Specification: Voice Job

**Feature Branch**: `005-voice-job` (board story US-005)

**Created**: 2026-10-16

**Status**: Implemented

**Input**: "Voice job: TTS worker producing per-line audio with shadowing pauses" — idempotent TTS job per script line with retry; shadowing pauses configurable by the niche template.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Per-line audio from an approved script (Priority: P1)

As the owner, once a script is approved, a worker job synthesizes one audio clip per script line and writes a manifest describing every clip.

**Acceptance Scenarios**:

1. **Given** a script of N lines and a TTS provider, **When** the job runs, **Then** N audio clips are stored and a manifest lists, per line: index, section, text, audio key, pause after, and whether it was reused.
2. **Given** a line with empty text or an unsafe run id, **Then** the job fails fast with a stable error code (`voice.empty_line`, `voice.invalid_run_id`) before any provider call.

### User Story 2 - Idempotent and retryable (Priority: P1)

As the owner, I never want to pay twice for the same line, and I want transient provider failures retried.

**Acceptance Scenarios**:

1. **Given** a finished job, **When** it runs again with the same inputs, **Then** no TTS call is made, nothing is billed, and every manifest entry is marked `cached`.
2. **Given** a job that failed midway, **When** it is re-run, **Then** only the missing lines are synthesized.
3. **Given** a transient `ProviderCallError`, **When** a line is synthesized, **Then** it is retried with backoff up to `attempts`; after the last attempt the job fails with `voice.line_failed` (index in params) while already-stored lines are kept.
4. **Given** a budget error, **Then** it is never retried and propagates unchanged.
5. **Given** the same text with a different voice or provider/model, **Then** it is a different clip (different idempotency key).

### User Story 3 - Shadowing pauses from the niche template (Priority: P1)

As a content designer, I configure shadowing pauses in the niche template data, not in code (constitution IV).

**Acceptance Scenarios**:

1. **Given** the English A1/A2 template (`shadowing_pause_seconds` = 2.0 and `shadowing_sections` listing practice sections), **Then** lines in those sections get `pause_after_seconds` = 2.0 and other lines get 0.
2. **Given** a template with `shadowing_sections` empty or pause 0, **Then** no pauses are produced.
3. **Given** a template whose pause is changed, **Then** the manifest follows without code changes and without re-synthesis (pauses are not part of the audio key).

## Requirements

- **FR-001**: The worker exposes an Arq job `synthesize_voice_job` that wraps a pure, testable `synthesize_voice` function.
- **FR-002**: Audio keys are deterministic: `sha256(provider/model | voice | text)`; storage path `<run_id>/<index>-<key16>.mp3`.
- **FR-003**: Storage sits behind an `AudioStore` protocol (local filesystem implementation under `VOICE_STORAGE_DIR`, default `storage/audio`; in-memory for tests).
- **FR-004**: The job performs no LLM decisions (constitution II); TTS is called through the `TTS` protocol, metered by `MeteredTTS` in production (constitution VI).
- **FR-005**: Errors carry stable codes and params, never localized text.
- **FR-006**: Tests use `FakeTTS` and templates from `packages/niche-templates`; no real providers.
