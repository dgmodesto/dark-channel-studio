import dataclasses

import pytest
from render_helpers import make_request

from dcs_worker.render.models import Background, RenderError
from dcs_worker.render.plan import build_plan


def test_plan_is_deterministic():
    a, b = build_plan(make_request()), build_plan(make_request())
    assert a == b
    assert a.args == b.args and a.input_hash == b.input_hash


def test_plan_duration_includes_pauses():
    assert build_plan(make_request()).duration_seconds == 5.5


def test_output_key_uses_hash():
    plan = build_plan(make_request())
    assert plan.output_key == f"run-r/render-{plan.input_hash[:16]}.mp4"


def test_hash_changes_with_audio_content():
    req = make_request()
    clips = list(req.clips)
    clips[0] = dataclasses.replace(clips[0], audio_sha256="dd" * 32)
    assert (
        build_plan(dataclasses.replace(req, clips=clips)).input_hash != build_plan(req).input_hash
    )


def test_hash_changes_with_translation_background_music_and_style():
    base = build_plan(make_request()).input_hash
    req = make_request()
    clips = list(req.clips)
    clips[1] = dataclasses.replace(clips[1], translation="Tudo bem?")
    assert build_plan(dataclasses.replace(req, clips=clips)).input_hash != base
    assert build_plan(make_request(background=Background("color", "ffffff"))).input_hash != base
    assert build_plan(make_request(music=None)).input_hash != base
    tpl = req.template.model_copy(
        update={"subtitles": req.template.subtitles.model_copy(update={"style": "other"})}
    )
    assert build_plan(make_request(template=tpl)).input_hash != base


def test_command_has_deterministic_flags():
    args = build_plan(make_request()).args
    assert args[0] == "ffmpeg"
    for flag in ("-map_metadata", "-threads", "-fflags", "+bitexact"):
        assert flag in args
    assert args[args.index("-map_metadata") + 1] == "-1"
    assert args[-1] == "out.mp4"
    assert not any(a.startswith(("C:", "/")) for a in args)  # relative names only


def test_music_ducked_at_minus_20_db_during_speech():
    plan = build_plan(make_request())
    graph = plan.args[plan.args.index("-filter_complex") + 1]
    assert "volume=" in graph and "amix" in graph
    assert "0.1" in graph  # -20 dB linear gain
    assert "between(t,0.0,1.5)" in graph and "between(t,1.5,3.5)" in graph


def test_pause_padding_per_clip():
    plan = build_plan(make_request())
    graph = plan.args[plan.args.index("-filter_complex") + 1]
    assert "apad=pad_dur=2.0" in graph and "concat=n=2" in graph


def test_no_music_graph_has_no_amix():
    plan = build_plan(make_request(music=None))
    graph = plan.args[plan.args.index("-filter_complex") + 1]
    assert "amix" not in graph


def test_image_background_is_looped_input():
    plan = build_plan(make_request(background=Background("image", "bg/cover.png", "ee" * 32)))
    assert "-loop" in plan.args
    assert ("bg.png", "bg/cover.png") in plan.inputs


@pytest.mark.parametrize(
    ("over", "code"),
    [
        ({"run_id": "../x"}, "render.invalid_run_id"),
        ({"clips": []}, "render.no_clips"),
    ],
)
def test_validation(over, code):
    with pytest.raises(RenderError) as e:
        build_plan(make_request(**over))
    assert e.value.code == code


def test_non_positive_duration_rejected():
    req = make_request()
    clips = [dataclasses.replace(req.clips[0], duration_seconds=0.0), req.clips[1]]
    with pytest.raises(RenderError) as e:
        build_plan(dataclasses.replace(req, clips=clips))
    assert e.value.code == "render.invalid_duration"


@pytest.mark.parametrize("pause", [-1.0, float("nan"), float("inf")])
def test_invalid_pause_rejected(pause):
    req = make_request()
    clips = [dataclasses.replace(req.clips[0], pause_after_seconds=pause), req.clips[1]]
    with pytest.raises(RenderError) as e:
        build_plan(dataclasses.replace(req, clips=clips))
    assert e.value.code == "render.invalid_pause"
