# apps/worker

Arq workers run deterministic jobs such as TTS and FFmpeg rendering; they do not make LLM decisions (ADR-0002).

The render job writes the MP4 to `VOICE_STORAGE_DIR` and submits its video key and voice-manifest audio keys to the API review queue. Configure `API_BASE_URL` and mount the same storage directory into the API as `MEDIA_STORAGE_DIR`; the Compose stack shares this storage through its `media` volume. The optional `review_title` render payload field controls the review card title; the run id is used when it is absent.
