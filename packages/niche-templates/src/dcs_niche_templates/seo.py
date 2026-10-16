import html
import re
from dataclasses import dataclass

from dcs_niche_templates.models import NicheTemplate

_WORD = re.compile(r"[A-Za-z0-9']+")


@dataclass(frozen=True)
class SeoMetadata:
    title: str
    description: str
    tags: list[str]
    synthetic_content_disclosed: bool


def _clean(value: str) -> str:
    return " ".join(value.split())


def build_metadata(
    template: NicheTemplate, topic: str, phrases: list[str] | None = None
) -> SeoMetadata:
    topic = _clean(topic)
    if not topic:
        raise ValueError("topic must not be empty")

    title_suffix = f" | {template.level} English"
    title = topic[: max(1, template.seo.title_max_chars - len(title_suffix))].rstrip()
    title = f"{title}{title_suffix}"[: template.seo.title_max_chars]
    phrase_text = " ".join(_clean(phrase) for phrase in (phrases or []) if _clean(phrase))
    description = (
        f"Learn English with this {template.level} lesson about {topic}. "
        f"{template.seo.description_cta} {template.seo.synthetic_disclosure}"
    )

    candidates = [topic, *(_WORD.findall(phrase_text)), template.content_language, template.level]
    tags: list[str] = []
    for candidate in candidates:
        tag = _clean(candidate).strip(" .,!?")
        if tag and tag.casefold() not in {item.casefold() for item in tags}:
            tags.append(tag[:100])
        if len(tags) == template.seo.max_tags:
            break
    return SeoMetadata(title, description, tags, template.gates.synthetic_disclosure)


def render_thumbnail_svg(template: NicheTemplate, text: str) -> str:
    config = template.thumbnail
    label = html.escape(_clean(config.label), quote=True)
    headline = html.escape(_clean(text)[: config.max_text_chars], quote=True)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" '
        'viewBox="0 0 1280 720">'
        f'<rect width="1280" height="720" fill="{config.background}"/>'
        f'<rect x="0" y="0" width="28" height="720" fill="{config.accent}"/>'
        f'<text x="88" y="168" fill="{config.accent}" font-family="sans-serif" '
        f'font-size="40" font-weight="700">{label}</text>'
        f'<text x="88" y="360" fill="#FFFFFF" font-family="sans-serif" '
        f'font-size="76" font-weight="700">{headline}</text>'
        "</svg>"
    )
