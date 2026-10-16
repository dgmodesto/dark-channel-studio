from dcs_niche_templates import get_template
from dcs_niche_templates.seo import build_metadata, render_thumbnail_svg
from dcs_worker.render.models import Background, MusicSpec, RenderClip, RenderRequest
from dcs_worker.render.render import FfmpegTools, render_video


async def render_video_job(ctx: dict, payload: dict) -> dict:
    """Arq entry point. Payload: run_id, template_id, manifest (US-005), translations, background,
    music?, width?, height?, fps?."""
    translations = payload.get("translations") or []
    clips = [
        RenderClip(
            index=e["index"],
            section=e["section"],
            text=e["text"],
            translation=translations[i] if i < len(translations) else None,
            audio_key=e["audio_key"],
            pause_after_seconds=e["pause_after_seconds"],
        )
        for i, e in enumerate(payload["manifest"]["entries"])
    ]
    bg = payload["background"]
    music = payload.get("music")
    extra = {k: payload[k] for k in ("width", "height", "fps") if k in payload}
    request = RenderRequest(
        run_id=payload["run_id"],
        template=get_template(payload["template_id"], payload.get("template_version")),
        clips=clips,
        background=Background(kind=bg["kind"], value=bg["value"]),
        music=MusicSpec(**music) if music else None,
        **extra,
    )
    topic = str(payload.get("topic") or (clips[0].text if clips else "")).strip()
    metadata = build_metadata(request.template, topic, phrases=[clip.text for clip in clips])
    thumbnail_key = f"{request.run_id}/thumbnail.svg"
    tools = ctx.get("media_tools") or FfmpegTools()
    result = await render_video(request, ctx["audio_store"], tools)
    await ctx["audio_store"].put(
        thumbnail_key, render_thumbnail_svg(request.template, topic).encode("utf-8")
    )
    submit_review = ctx.get("review_submitter")
    if submit_review is not None:
        await submit_review(
            {
                "run_id": result.run_id,
                "title": str(payload.get("review_title") or metadata.title),
                "video_key": result.video_key,
                "audio_keys": [entry["audio_key"] for entry in payload["manifest"]["entries"]],
                "thumbnail_key": thumbnail_key,
                "description": metadata.description,
                "tags": metadata.tags,
                "synthetic_content_disclosed": metadata.synthetic_content_disclosed,
            }
        )
    return {
        **result.to_dict(),
        "thumbnail_key": thumbnail_key,
        "seo": {
            "title": metadata.title,
            "description": metadata.description,
            "tags": metadata.tags,
            "synthetic_content_disclosed": metadata.synthetic_content_disclosed,
        },
    }
