from dcs_niche_templates import NicheTemplate
from dcs_providers.protocols import ChatMessage


def _brief(t: NicheTemplate) -> str:
    s = t.script
    return (
        f"Channel: {t.name}. Content language: {t.content_language}. Level: {t.level}.\n"
        f"Sections (in order): {', '.join(s.sections)}.\n"
        f"At most {s.max_lines} lines and {s.max_words_per_line} words per line."
    )


def idea_messages(topic: str, t: NicheTemplate) -> list[ChatMessage]:
    return [
        ChatMessage("system", f"You plan short educational videos.\n{_brief(t)}"),
        ChatMessage(
            "user", f"Topic: {topic}\nGive one concise angle for the video, in one paragraph."
        ),
    ]


def writer_messages(
    topic: str, idea: str, t: NicheTemplate, feedback: list[str]
) -> list[ChatMessage]:
    system = (
        f"You write video scripts.\n{_brief(t)}\n"
        'Answer only with JSON: {"lines": [{"section": "<section>", "text": "<line>"}]}.'
    )
    user = f"Topic: {topic}\nAngle: {idea}"
    if feedback:
        user += "\nFix these issues from the previous draft:\n" + "\n".join(
            f"- {f}" for f in feedback
        )
    return [ChatMessage("system", system), ChatMessage("user", user)]


def reviewer_messages(topic: str, draft_json: str, t: NicheTemplate) -> list[ChatMessage]:
    system = (
        f"You review video scripts for quality, level fit and clarity.\n{_brief(t)}\n"
        'Answer only with JSON: {"approved": true|false, "notes": "<what to change>"}.'
    )
    return [
        ChatMessage("system", system),
        ChatMessage("user", f"Topic: {topic}\nScript:\n{draft_json}"),
    ]
