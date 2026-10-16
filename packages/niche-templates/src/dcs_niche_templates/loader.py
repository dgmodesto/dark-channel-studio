import json
from functools import cache
from importlib import resources

from dcs_niche_templates.models import NicheTemplate


class TemplateNotFoundError(Exception):
    code = "template.not_found"

    def __init__(self, template_id: str, version: int | None = None):
        self.template_id, self.version = template_id, version
        super().__init__(self.code)


@cache
def _load_all() -> tuple[NicheTemplate, ...]:
    data_dir = resources.files("dcs_niche_templates") / "data"
    templates = [
        NicheTemplate.model_validate(json.loads(p.read_text(encoding="utf-8")))
        for p in data_dir.iterdir()
        if p.name.endswith(".json")
    ]
    return tuple(sorted(templates, key=lambda t: (t.id, t.version)))


def list_templates() -> list[NicheTemplate]:
    return list(_load_all())


def get_template(template_id: str, version: int | None = None) -> NicheTemplate:
    matches = [t for t in _load_all() if t.id == template_id]
    if version is not None:
        matches = [t for t in matches if t.version == version]
    if not matches:
        raise TemplateNotFoundError(template_id, version)
    return matches[-1]
