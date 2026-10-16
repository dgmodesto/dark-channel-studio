from dcs_worker.render.models import RenderRequest

FONT = "DejaVu Sans"


def format_ass_time(seconds: float) -> str:
    cs = round(seconds * 100)
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, c = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def _escape(text: str) -> str:
    cleaned = text.replace("{", "(").replace("}", ")").replace("\r", "")
    return cleaned.replace("\n", "\\N")


def build_ass(request: RenderRequest, cues: list[tuple[float, float]]) -> str:
    """ASS document: primary text, then the secondary language stacked below it."""
    cfg = request.template.subtitles
    size = max(12, request.height // 15)
    header = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {request.width}",
        f"PlayResY: {request.height}",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Primary,{FONT},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,"
        "-1,0,0,0,100,100,0,0,1,2,1,2,40,40,60,1",
        f"Style: Secondary,{FONT},{round(size * 0.8)},&H0000E5FF,&H0000E5FF,&H00000000,"
        "&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,40,40,60,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    events = []
    for clip, (start, end) in zip(request.clips, cues, strict=True):
        text = _escape(clip.text)
        if cfg.secondary and clip.translation is not None:
            text += "\\N{\\rSecondary}" + _escape(clip.translation)
        events.append(
            f"Dialogue: 0,{format_ass_time(start)},{format_ass_time(end)},Primary,,0,0,0,,{text}"
        )
    return "\n".join(header + events) + "\n"
