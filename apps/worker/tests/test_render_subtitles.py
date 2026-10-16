import dataclasses

import pytest
from render_helpers import make_request

from dcs_worker.render.models import RenderError
from dcs_worker.render.plan import build_plan
from dcs_worker.render.subtitles import build_ass, format_ass_time


def test_ass_time_format():
    assert format_ass_time(0) == "0:00:00.00"
    assert format_ass_time(3725.5) == "1:02:05.50"


def test_dual_stacked_subtitles():
    ass = build_plan(make_request()).ass
    assert "Dialogue: 0,0:00:00.00,0:00:01.50" in ass
    assert "Dialogue: 0,0:00:01.50,0:00:03.50" in ass  # second line; its pause has no cue
    assert "Hello!\\N{\\rSecondary}Ola!" in ass


def test_single_language_when_no_secondary():
    req = make_request()
    tpl = req.template.model_copy(
        update={"subtitles": req.template.subtitles.model_copy(update={"secondary": None})}
    )
    ass = build_ass(dataclasses.replace(req, template=tpl), [(0.0, 1.5), (1.5, 3.5)])
    assert "Hello!" in ass and "Ola!" not in ass


def test_missing_translation_fails_fast():
    req = make_request()
    clips = [req.clips[0], dataclasses.replace(req.clips[1], translation=None)]
    with pytest.raises(RenderError) as e:
        build_plan(dataclasses.replace(req, clips=clips))
    assert e.value.code == "render.missing_translation"
    assert e.value.params == {"index": "1"}


def test_text_is_escaped():
    req = make_request()
    clips = [dataclasses.replace(req.clips[0], text="a {b} c\nd"), req.clips[1]]
    ass = build_plan(dataclasses.replace(req, clips=clips)).ass
    assert "{b}" not in ass.split("[Events]")[1]
