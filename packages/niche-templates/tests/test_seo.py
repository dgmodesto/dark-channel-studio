from dcs_niche_templates import get_template
from dcs_niche_templates.seo import build_metadata, render_thumbnail_svg


def test_metadata_uses_template_limits_and_discloses_synthetic_content():
    template = get_template("english-a1-a2-br")

    metadata = build_metadata(
        template,
        topic="Ordering coffee",
        phrases=["I'd like a coffee", "Could I have a latte?"],
    )

    assert len(metadata.title) <= template.seo.title_max_chars
    assert metadata.tags
    assert len(metadata.tags) <= template.seo.max_tags
    assert template.seo.description_cta in metadata.description
    assert "AI-generated" in metadata.description
    assert metadata.synthetic_content_disclosed is True


def test_thumbnail_is_deterministic_template_driven_and_escapes_text():
    template = get_template("english-a1-a2-br")

    first = render_thumbnail_svg(template, "Coffee & tea")
    second = render_thumbnail_svg(template, "Coffee & tea")

    assert first == second
    assert "<svg" in first
    assert "Coffee &amp; tea" in first
    assert "Coffee & tea" not in first
