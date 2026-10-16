from dcs_worker.render.models import RenderClip


def build_timeline(clips: list[RenderClip]) -> tuple[list[tuple[float, float]], float]:
    """Speech window (start, end) per clip, and total duration including pauses."""
    cues: list[tuple[float, float]] = []
    t = 0.0
    for clip in clips:
        assert clip.duration_seconds is not None
        start = round(t, 3)
        end = round(t + clip.duration_seconds, 3)
        cues.append((start, end))
        t = end + clip.pause_after_seconds
    return cues, round(t, 3)
