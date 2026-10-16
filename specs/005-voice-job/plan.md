# Implementation Plan: Voice Job

**Spec**: [spec.md](spec.md)

## Technical Context

- Python 3.12, Arq worker, `dcs-providers` (`TTS`, `FakeTTS`, `MeteredTTS`, errors), `dcs-niche-templates`, `dcs_common.retry`.
- No new workspace package: code lives in `apps/worker/src/dcs_worker/voice/`. `apps/worker` gains `dcs-providers` and `dcs-niche-templates` dependencies and `[tool.uv.sources]` entries; `uv.lock` refreshed (Docker `--frozen` sync). Dockerfiles already copy `packages`.
- Template change (data, backward compatible): `voice.shadowing_sections: list[str] = []`; English A1/A2 sets `["key_phrases", "dialogue"]`.

## Design

- `voice/models.py`: `VoiceLine`, `VoiceRequest`, `ManifestEntry`, `VoiceManifest`, `VoiceError(code, **params)`.
- `voice/store.py`: `AudioStore` protocol, `LocalAudioStore` (path-safe, filesystem calls in threads), `InMemoryAudioStore`.
- `voice/synthesize.py`: validation → per line: key, skip if stored, else `retry_async` on `ProviderCallError` → store → manifest (stored as `<run_id>/manifest.json`).
- `jobs/voice.py`: Arq entry point building the request from a payload dict; TTS comes from `ctx["tts_factory"]`, store from `ctx["audio_store"]`. Registered in `WorkerSettings.functions`; startup wires the local store and a metered factory when a `tts` role is configured.

## Constitution Check

I n/a (no publishing) · II deterministic job, no LLM · III provider via protocol · IV pauses are template data · V test-first, evidence · VI metered TTS · VII no secrets · VIII English. No violations; Complexity Tracking: none.
