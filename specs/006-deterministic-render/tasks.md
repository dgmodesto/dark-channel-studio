# Tasks: Deterministic Render

**Tests**: written first and seen failing (constitution V); red-phase output in `evidence/red-phase.txt`.

## Phase 1: Tests first
- [x] T001 [P] `apps/worker/tests/test_render_plan.py` — determinism, hash sensitivity, validation, flags, ducking at -20 dB, pauses
- [x] T002 [P] `apps/worker/tests/test_render_subtitles.py` — dual stacked EN/PT, single language, missing translation
- [x] T003 [P] `apps/worker/tests/test_render_job.py` — fake tools, cache hit, failure keeps no output, job registered
- [x] T004 [P] `apps/worker/tests/test_render_ffmpeg.py` — real byte-identical render (skipped without ffmpeg)

## Phase 2: Implementation
- [x] T005 `render/` package and `jobs/render.py`; register in `WorkerSettings`
- [x] T006 Install `ffmpeg` in `apps/worker/Dockerfile`

## Phase 3: Close-out
- [x] T007 Evidence, code review, board update, single commit `feat(US-006)`, PR to `main`
