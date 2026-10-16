import hashlib
import json
import math
import re
from pathlib import PurePosixPath

from dcs_worker.render.models import RenderError, RenderPlan, RenderRequest
from dcs_worker.render.subtitles import FONT, build_ass
from dcs_worker.render.timeline import build_timeline

_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_COLOR = re.compile(r"^[0-9A-Fa-f]{6}$")
PLAN_VERSION = 1
SAMPLE_RATE = 48000


def validate_request(request: RenderRequest) -> None:
    if ".." in request.run_id or not _RUN_ID.match(request.run_id):
        raise RenderError("render.invalid_run_id")
    if not request.clips:
        raise RenderError("render.no_clips")
    for clip in request.clips:
        pause = clip.pause_after_seconds
        if not math.isfinite(pause) or pause < 0:
            raise RenderError("render.invalid_pause", index=str(clip.index))
    if request.background.kind == "color" and not _COLOR.match(request.background.value):
        raise RenderError("render.invalid_background")
    if request.template.subtitles.secondary:
        for clip in request.clips:
            if not (clip.translation and clip.translation.strip()):
                raise RenderError("render.missing_translation", index=str(clip.index))


def _gain(db: float) -> str:
    return f"{10 ** (db / 20):.6g}"


def _num(value: float) -> str:
    return repr(round(value, 3))


def _suffix(key: str, default: str) -> str:
    return PurePosixPath(key).suffix or default


def build_plan(request: RenderRequest) -> RenderPlan:
    validate_request(request)
    for clip in request.clips:
        if (
            clip.duration_seconds is None
            or not math.isfinite(clip.duration_seconds)
            or clip.duration_seconds <= 0
        ):
            raise RenderError("render.invalid_duration", index=str(clip.index))
    cues, total = build_timeline(request.clips)
    ass = build_ass(request, cues)
    w, h, fps, total_s = request.width, request.height, request.fps, _num(total)

    inputs: list[tuple[str, str]] = []
    args = ["ffmpeg", "-y", "-hide_banner", "-nostdin", "-loglevel", "error"]
    args += ["-fflags", "+bitexact", "-flags:v", "+bitexact", "-flags:a", "+bitexact"]
    args += ["-filter_complex_threads", "1"]

    bg = request.background
    if bg.kind == "color":
        args += ["-f", "lavfi", "-i", f"color=c=0x{bg.value.upper()}:s={w}x{h}:r={fps}:d={total_s}"]
        bg_filter = "[0:v]format=yuv420p"
    else:
        name = f"bg{_suffix(bg.value, '.png')}"
        inputs.append((name, bg.value))
        args += ["-loop", "1", "-framerate", str(fps), "-t", total_s, "-i", name]
        bg_filter = f"[0:v]scale={w}:{h},setsar=1,format=yuv420p"

    chains = []
    for i, clip in enumerate(request.clips):
        name = f"a{i:03d}{_suffix(clip.audio_key, '.mp3')}"
        inputs.append((name, clip.audio_key))
        args += ["-i", name]
        chain = (
            f"[{i + 1}:a]aresample={SAMPLE_RATE},aformat=sample_fmts=fltp:channel_layouts=stereo"
        )
        if clip.pause_after_seconds > 0:
            chain += f",apad=pad_dur={_num(clip.pause_after_seconds)}"
        chains.append(f"{chain}[v{i}]")
    n = len(request.clips)
    concat_in = "".join(f"[v{i}]" for i in range(n))
    chains.append(f"{concat_in}concat=n={n}:v=0:a=1[voice]")

    music = request.music
    if music:
        name = f"music{_suffix(music.key, '.mp3')}"
        inputs.append((name, music.key))
        args += ["-stream_loop", "-1", "-i", name]
        speaking = "+".join(f"between(t,{_num(s)},{_num(e)})" for s, e in cues)
        expr = f"if(gt({speaking},0),{_gain(music.duck_db)},{_gain(music.base_db)})"
        chains.append(
            f"[{n + 1}:a]aresample={SAMPLE_RATE},aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"atrim=duration={total_s},volume='{expr}':eval=frame[music]"
        )
        chains.append("[voice][music]amix=inputs=2:duration=first:normalize=0[aout]")
    else:
        chains.append("[voice]anull[aout]")
    chains.append(f"{bg_filter},subtitles=subs.ass[vout]")

    args += ["-filter_complex", ";".join(chains), "-map", "[vout]", "-map", "[aout]"]
    args += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p"]
    args += ["-r", str(fps), "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE), "-ac", "2"]
    args += ["-threads", "1", "-map_metadata", "-1", "-movflags", "+faststart", "-t", total_s]
    args += ["out.mp4"]

    canonical = {
        "version": PLAN_VERSION,
        "font": FONT,
        "args": args,
        "ass": ass,
        "subtitles": request.template.subtitles.model_dump(),
        "content": {
            "clips": [c.audio_sha256 for c in request.clips],
            "music": music.sha256 if music else None,
            "background": bg.sha256,
        },
    }
    digest = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return RenderPlan(
        args=args,
        ass=ass,
        inputs=inputs,
        input_hash=digest,
        output_key=f"{request.run_id}/render-{digest[:16]}.mp4",
        duration_seconds=total,
    )
