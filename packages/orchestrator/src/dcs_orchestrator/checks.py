import json
import re

from dcs_niche_templates import NicheTemplate
from dcs_orchestrator.interface import ScriptLine

_FENCE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")


def parse_draft(raw: str, template: NicheTemplate) -> tuple[list[ScriptLine], list[str]]:
    """Parse writer output; returns (lines, problems). Malformed output yields no lines."""
    try:
        data = json.loads(_FENCE.sub("", raw.strip()))
        lines = [
            ScriptLine(section=str(item["section"]), text=str(item["text"]))
            for item in data["lines"]
        ]
    except (ValueError, KeyError, TypeError):
        return [], ["draft.invalid_json"]
    return lines, validate_lines(lines, template)


def validate_lines(lines: list[ScriptLine], template: NicheTemplate) -> list[str]:
    if not lines:
        return ["draft.empty"]
    spec = template.script
    problems: list[str] = []
    if len(lines) > spec.max_lines:
        problems.append("draft.too_many_lines")
    if any(not line.text.strip() for line in lines):
        problems.append("draft.empty_line")
    if any(len(line.text.split()) > spec.max_words_per_line for line in lines):
        problems.append("draft.line_too_long")
    if any(line.section not in spec.sections for line in lines):
        problems.append("draft.unknown_section")
    return problems
