import hashlib
import json
import re

from dcs_common.retry import retry_async
from dcs_providers.errors import ProviderCallError
from dcs_providers.protocols import TTS
from dcs_worker.voice.models import ManifestEntry, VoiceError, VoiceManifest, VoiceRequest
from dcs_worker.voice.store import AudioStore

_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def audio_key_digest(provider: str, model: str, voice: str | None, text: str) -> str:
    raw = "\x1f".join([provider, model, voice or "", text])
    return hashlib.sha256(raw.encode()).hexdigest()


def pause_after(request: VoiceRequest, section: str) -> float:
    cfg = request.template.voice
    return cfg.shadowing_pause_seconds if section in cfg.shadowing_sections else 0.0


def _validate(request: VoiceRequest) -> None:
    if ".." in request.run_id or not _RUN_ID.match(request.run_id):
        raise VoiceError("voice.invalid_run_id")
    if not request.lines:
        raise VoiceError("voice.no_lines")
    for i, line in enumerate(request.lines):
        if not line.text.strip():
            raise VoiceError("voice.empty_line", index=str(i))


async def synthesize_voice(
    request: VoiceRequest,
    tts: TTS,
    store: AudioStore,
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
) -> VoiceManifest:
    """Synthesize one clip per line. Re-runs reuse stored clips, so they cost nothing."""
    _validate(request)
    entries: list[ManifestEntry] = []
    for index, line in enumerate(request.lines):
        digest = audio_key_digest(request.provider, request.model, request.voice, line.text)
        key = f"{request.run_id}/{index:03d}-{digest[:16]}.mp3"
        cached = await store.exists(key)
        if not cached:
            try:
                result = await retry_async(
                    lambda text=line.text: tts.synthesize(text, voice=request.voice),
                    attempts=attempts,
                    base_delay=base_delay,
                    exceptions=(ProviderCallError,),
                )
            except ProviderCallError as e:
                raise VoiceError("voice.line_failed", index=str(index)) from e
            await store.put(key, result.audio)
        entries.append(
            ManifestEntry(
                index=index,
                section=line.section,
                text=line.text,
                audio_key=key,
                pause_after_seconds=pause_after(request, line.section),
                cached=cached,
            )
        )
    manifest = VoiceManifest(run_id=request.run_id, entries=entries)
    await store.put(f"{request.run_id}/manifest.json", json.dumps(manifest.to_dict()).encode())
    return manifest
