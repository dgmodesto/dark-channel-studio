import pytest
from pydantic import ValidationError

from dcs_niche_templates import TemplateNotFoundError, get_template, list_templates
from dcs_niche_templates.models import NicheTemplate


def test_english_template_is_listed():
    assert ("english-a1-a2-br", 1) in {(t.id, t.version) for t in list_templates()}


def test_latest_version_is_default():
    t = get_template("english-a1-a2-br")
    assert t.version == max(x.version for x in list_templates() if x.id == t.id)
    assert t.content_language == "en" and t.subtitles.secondary == "pt-BR"


def test_explicit_version():
    assert get_template("english-a1-a2-br", 1).version == 1


@pytest.mark.parametrize("args", [("nope", None), ("english-a1-a2-br", 99)])
def test_not_found(args):
    with pytest.raises(TemplateNotFoundError) as exc:
        get_template(*args)
    assert exc.value.code == "template.not_found"


@pytest.mark.parametrize("gate", ["human_approval", "synthetic_disclosure"])
def test_gates_cannot_be_disabled(gate):
    data = get_template("english-a1-a2-br").model_dump()
    data["gates"][gate] = False
    with pytest.raises(ValidationError):
        NicheTemplate.model_validate(data)
