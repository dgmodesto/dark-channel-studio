from dcs_niche_templates import get_template
from dcs_worker.voice.models import VoiceLine, VoiceRequest
from dcs_worker.voice.synthesize import synthesize_voice


async def synthesize_voice_job(ctx: dict, payload: dict) -> dict:
    """Arq entry point. Payload: run_id, template_id, lines[{section,text}], voice?, channel_id?."""
    run_id = payload["run_id"]
    tts, provider, model = ctx["tts_factory"](run_id, payload.get("channel_id"))
    request = VoiceRequest(
        run_id=run_id,
        lines=[VoiceLine(section=ln["section"], text=ln["text"]) for ln in payload["lines"]],
        template=get_template(payload["template_id"], payload.get("template_version")),
        provider=provider,
        model=model,
        voice=payload.get("voice"),
    )
    manifest = await synthesize_voice(request, tts, ctx["audio_store"])
    return manifest.to_dict()
