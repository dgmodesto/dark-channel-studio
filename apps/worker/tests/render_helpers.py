import dataclasses

from dcs_niche_templates import get_template
from dcs_worker.render.models import Background, MusicSpec, RenderClip, RenderRequest


def make_request(**over) -> RenderRequest:
    clips = [
        RenderClip(0, "hook", "Hello!", "Ola!", "run-r/000-a.mp3", "aa" * 32, 1.5, 0.0),
        RenderClip(
            1, "dialogue", "How are you?", "Como vai?", "run-r/001-b.mp3", "bb" * 32, 2.0, 2.0
        ),
    ]
    base = RenderRequest(
        run_id="run-r",
        template=get_template("english-a1-a2-br"),
        clips=clips,
        background=Background(kind="color", value="101418"),
        music=MusicSpec(key="music/loop.mp3", sha256="cc" * 32),
    )
    return dataclasses.replace(base, **over)
