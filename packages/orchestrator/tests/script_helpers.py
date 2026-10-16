import json

from langgraph.checkpoint.memory import MemorySaver

from dcs_niche_templates import get_template
from dcs_orchestrator.adapters.langgraph_script import LangGraphScriptOrchestrator
from dcs_orchestrator.interface import ScriptRequest
from dcs_providers.protocols import ChatMessage, ChatResult, Usage

TEMPLATE = get_template("english-a1-a2-br")


def draft(*pairs):
    return json.dumps({"lines": [{"section": s, "text": t} for s, t in pairs]})


GOOD = draft(("hook", "Let us order coffee today."), ("key_phrases", "Can I have a coffee?"))


def verdict(approved, notes=""):
    return json.dumps({"approved": approved, "notes": notes})


class ScriptedChat:
    """Offline ChatModel that replays queued replies and records every prompt."""

    def __init__(self, replies, fail_at=None):
        self.replies = list(replies)
        self.prompts: list[str] = []
        self.fail_at = fail_at

    async def complete(self, messages: list[ChatMessage]) -> ChatResult:
        self.prompts.append("\n".join(m.content for m in messages))
        if self.fail_at is not None and len(self.prompts) == self.fail_at:
            raise RuntimeError("provider down")
        text = self.replies.pop(0)
        return ChatResult(text=text, usage=Usage(input_tokens=10, output_tokens=10))


def make(writer, reviewer, saver=None):
    return LangGraphScriptOrchestrator(writer, reviewer, saver or MemorySaver())


def request(run_id="run-1", max_iterations=3):
    return ScriptRequest(
        run_id=run_id, topic="Ordering coffee", template=TEMPLATE, max_iterations=max_iterations
    )
