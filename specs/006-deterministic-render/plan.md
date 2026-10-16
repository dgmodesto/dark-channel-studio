# Implementation Plan: Deterministic Render

**Spec**: [spec.md](spec.md)

## Technical Context

- Python 3.12, Arq worker, `dcs-niche-templates` (`subtitles`), US-005 voice manifest and `AudioStore`.
- No new workspace package: code in `apps/worker/src/dcs_worker/render/`; no dependency change. The worker Dockerfile installs `ffmpeg` (apt). CI python job has no FFmpeg, so real-encode tests skip there.

## Design

- `render/models.py`: `RenderError(code, **params)`, `RenderClip`, `Background`, `MusicSpec`, `RenderRequest`, `RenderPlan`, `RenderResult`.
- `render/timeline.py`: cumulative cue times (clip duration, then pause), rounded to milliseconds.
- `render/subtitles.py`: ASS document, primary + secondary stacked, from template `subtitles`.
- `render/plan.py`: validation, ASS, `-filter_complex` (per-clip `apad` for pauses, `concat`, music `volume` expression with -20 dB inside speech windows, `amix normalize=0`), deterministic flags, canonical `input_hash` (includes audio/music/background content hashes and the FFmpeg arg list).
- `render/render.py`: `MediaTools` protocol (`probe_duration`, `run`), `FfmpegTools`; `render_video` materializes inputs to a temp dir, skips if output key exists, stores output only on success.
- `jobs/render.py`: Arq entry point (payload: run_id, template_id, manifest, translations, background, music); registered in `WorkerSettings`.

## Constitution Check

II deterministic job, no LLM · IV subtitle style/languages from template data · V test-first with evidence · VIII error codes only · VI render has no paid provider call (no cost event). No violations; Complexity Tracking: none.
