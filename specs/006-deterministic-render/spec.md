# Feature Specification: Deterministic Render

**Feature Branch**: `006-deterministic-render` (board story US-006)

**Created**: 2026-10-16

**Status**: Implemented

**Input**: "Deterministic render: FFmpeg with dual EN/PT subtitles, background, music ducking at -20 dB; same inputs produce the same video." Depends on the US-005 voice manifest and the niche template `subtitles` config.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Same inputs, same video (Priority: P1)

As the owner, re-rendering an unchanged run must yield a byte-identical video and must not re-encode.

**Acceptance Scenarios**:

1. **Given** identical inputs (voice clips, translations, template, background, music, settings), **Then** the render plan and its `input_hash` are identical, including the FFmpeg command line.
2. **Given** any changed input (a clip's audio content, a translation, the background, the music, the template subtitle style), **Then** the `input_hash` and output key change.
3. **Given** an existing output for the same `input_hash`, **When** the job runs again, **Then** FFmpeg is not invoked and the result is flagged `cached`.
4. **Given** FFmpeg is installed, **When** the same inputs are rendered twice, **Then** the two MP4 files are byte-identical.

### User Story 2 - Dual EN/PT subtitles from the template (Priority: P1)

1. **Given** a template with `subtitles.primary = en`, `secondary = pt-BR`, **Then** the generated ASS file has, per line, a primary (EN) and a secondary (PT-BR) text stacked, timed to the line's audio.
2. **Given** a template without a secondary language, **Then** only the primary text is rendered.
3. **Given** a secondary language is configured but a translation is missing, **Then** the job fails fast with `render.missing_translation` (index in params) before FFmpeg runs.

### User Story 3 - Background and music ducking (Priority: P1)

1. **Given** a background (solid color or stored image), **Then** it is the video track for the whole timeline.
2. **Given** a music track, **Then** it is looped, trimmed to the timeline length and mixed under the voice, attenuated by -20 dB while a voice line is speaking (ducking) and at the configured base level otherwise.
3. **Given** shadowing pauses in the voice manifest, **Then** the timeline leaves silence after the line for the pause duration.

### Edge Cases

- Unsafe run id, empty manifest, or non-positive clip duration → stable error codes (`render.invalid_run_id`, `render.no_clips`, `render.invalid_duration`).
- FFmpeg failure → `render.ffmpeg_failed`; never a partial output (output is stored only on success).

## Requirements

- **FR-001** Render planning is a pure function producing command, subtitles and hash; no I/O.
- **FR-002** FFmpeg is invoked with bit-exact, single-threaded, metadata-stripped flags; the subtitle file is passed by relative path (runner cwd).
- **FR-003** Errors are stable codes with params, never localized strings (constitution VIII).
- **FR-004** Job is a deterministic Arq worker job with no LLM decisions (constitution II).
- **FR-005** Tests use fake media tools; real encoding tests are skipped when `ffmpeg` is absent. The worker Docker image installs FFmpeg.

## Success Criteria

- Plan/hash/subtitle/command tests pass without FFmpeg; the end-to-end determinism test passes where FFmpeg exists.
