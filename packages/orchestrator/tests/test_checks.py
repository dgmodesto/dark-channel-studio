import json

import pytest

from dcs_niche_templates import get_template
from dcs_orchestrator.checks import parse_draft, validate_lines

TEMPLATE = get_template("english-a1-a2-br")


def _draft(lines):
    return json.dumps({"lines": [{"section": s, "text": t} for s, t in lines]})


def test_parse_valid_draft():
    lines, problems = parse_draft(_draft([("hook", "Hello there")]), TEMPLATE)
    assert problems == []
    assert [(line.section, line.text) for line in lines] == [("hook", "Hello there")]


def test_parse_accepts_code_fences():
    raw = "```json\n" + _draft([("hook", "Hi")]) + "\n```"
    lines, problems = parse_draft(raw, TEMPLATE)
    assert problems == [] and len(lines) == 1


@pytest.mark.parametrize("raw", ["not json", "[]", '{"lines": "x"}', '{"lines": [{"text": "a"}]}'])
def test_parse_rejects_malformed(raw):
    lines, problems = parse_draft(raw, TEMPLATE)
    assert lines == [] and problems == ["draft.invalid_json"]


def test_too_many_lines():
    lines, _ = parse_draft(_draft([("hook", "Hi")] * 25), TEMPLATE)
    assert "draft.too_many_lines" in validate_lines(lines, TEMPLATE)


def test_too_many_words_in_line():
    lines, _ = parse_draft(_draft([("hook", " ".join(["word"] * 13))]), TEMPLATE)
    assert "draft.line_too_long" in validate_lines(lines, TEMPLATE)


def test_unknown_section_and_empty_text():
    lines, _ = parse_draft(_draft([("intro", "Hi"), ("hook", "  ")]), TEMPLATE)
    problems = validate_lines(lines, TEMPLATE)
    assert "draft.unknown_section" in problems and "draft.empty_line" in problems


def test_no_lines_is_a_problem():
    assert validate_lines([], TEMPLATE) == ["draft.empty"]
