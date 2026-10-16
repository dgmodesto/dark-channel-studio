import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from dcs_niche_templates import NicheTemplate
from dcs_orchestrator import prompts
from dcs_orchestrator.checks import parse_draft
from dcs_orchestrator.interface import (
    ScriptLine,
    ScriptPipelineError,
    ScriptRequest,
    ScriptResult,
)
from dcs_orchestrator.review import (
    ReviewDecision,
    ReviewGateError,
    ReviewRequest,
    ReviewResult,
)
from dcs_providers.protocols import ChatModel


class _State(TypedDict, total=False):
    topic: str
    template: dict[str, Any]
    max_iterations: int
    idea: str
    draft: str
    lines: list[dict[str, str]]
    iteration: int
    feedback: list[str]
    notes: list[str]
    status: str


class _ReviewState(TypedDict, total=False):
    run_id: str
    video_key: str
    audio_keys: list[str]
    status: str
    notes: str


def _reviewer_verdict(raw: str) -> tuple[bool, str]:
    try:
        data = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        return data["approved"] is True, str(data.get("notes", ""))
    except (ValueError, KeyError, TypeError, AttributeError):
        return False, ""


class LangGraphScriptOrchestrator:
    """idea -> write -> review loop. The only module that imports LangGraph."""

    def __init__(self, writer: ChatModel, reviewer: ChatModel, checkpointer: BaseCheckpointSaver):
        self._writer, self._reviewer = writer, reviewer
        self._graph = self._build(checkpointer)

    def _build(self, checkpointer: BaseCheckpointSaver):
        async def idea(state: _State) -> _State:
            template = NicheTemplate.model_validate(state["template"])
            result = await self._writer.complete(prompts.idea_messages(state["topic"], template))
            return {"idea": result.text.strip()}

        async def write(state: _State) -> _State:
            template = NicheTemplate.model_validate(state["template"])
            messages = prompts.writer_messages(
                state["topic"], state["idea"], template, state.get("feedback", [])
            )
            result = await self._writer.complete(messages)
            return {"draft": result.text, "iteration": state.get("iteration", 0) + 1}

        async def review(state: _State) -> _State:
            template = NicheTemplate.model_validate(state["template"])
            lines, problems = parse_draft(state["draft"], template)
            update: _State = {"lines": [{"section": x.section, "text": x.text} for x in lines]}
            notes = list(state.get("notes", []))
            approved = False
            if problems:
                update["feedback"] = problems
            else:
                messages = prompts.reviewer_messages(state["topic"], state["draft"], template)
                result = await self._reviewer.complete(messages)
                approved, note = _reviewer_verdict(result.text)
                if not approved:
                    notes.append(note)
                    update["feedback"] = [note or "reviewer.unparsable"]
            update["notes"] = notes
            if approved:
                update["status"] = "approved"
            elif state["iteration"] >= state["max_iterations"]:
                update["status"] = "rejected_max_iterations"
            else:
                update["status"] = "in_progress"
            return update

        def route(state: _State) -> str:
            return "write" if state["status"] == "in_progress" else END

        graph = StateGraph(_State)
        graph.add_node("idea", idea)
        graph.add_node("write", write)
        graph.add_node("review", review)
        graph.add_edge(START, "idea")
        graph.add_edge("idea", "write")
        graph.add_edge("write", "review")
        graph.add_conditional_edges("review", route, {"write": "write", END: END})
        return graph.compile(checkpointer=checkpointer)

    @staticmethod
    def _config(run_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": run_id}}

    async def start(self, request: ScriptRequest) -> ScriptResult:
        if await self.get_result(request.run_id) is not None:
            raise ScriptPipelineError("script.run_exists", run_id=request.run_id)
        initial: _State = {
            "topic": request.topic,
            "template": request.template.model_dump(),
            "max_iterations": request.max_iterations,
            "iteration": 0,
            "feedback": [],
            "notes": [],
            "status": "in_progress",
        }
        await self._graph.ainvoke(initial, self._config(request.run_id))
        return await self._require(request.run_id)

    async def resume(self, run_id: str) -> ScriptResult:
        snapshot = await self._graph.aget_state(self._config(run_id))
        if not snapshot.values:
            raise ScriptPipelineError("script.run_not_found", run_id=run_id)
        if snapshot.next:
            await self._graph.ainvoke(None, self._config(run_id))
        return await self._require(run_id)

    async def get_result(self, run_id: str) -> ScriptResult | None:
        snapshot = await self._graph.aget_state(self._config(run_id))
        values = snapshot.values
        if not values:
            return None
        return ScriptResult(
            run_id=run_id,
            status=values.get("status", "in_progress"),
            idea=values.get("idea", ""),
            lines=[ScriptLine(**x) for x in values.get("lines", [])],
            iterations=values.get("iteration", 0),
            notes=list(values.get("notes", [])),
        )

    async def _require(self, run_id: str) -> ScriptResult:
        result = await self.get_result(run_id)
        if result is None:
            raise ScriptPipelineError("script.run_not_found", run_id=run_id)
        return result


@asynccontextmanager
async def postgres_checkpointer(dsn: str) -> AsyncIterator[BaseCheckpointSaver]:
    """Postgres-backed checkpoint store; accepts SQLAlchemy-style DSNs (postgresql+driver://)."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    plain = dsn.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg://", "postgresql://"
    )
    async with AsyncPostgresSaver.from_conn_string(plain) as saver:
        await saver.setup()
        yield saver


class LangGraphReviewGate:
    """Persisted human decision gate; each decision resumes its thread checkpoint."""

    def __init__(self, checkpointer: BaseCheckpointSaver):
        async def wait_for_decision(state: _ReviewState) -> _ReviewState:
            response = interrupt(
                {
                    "run_id": state["run_id"],
                    "video_key": state["video_key"],
                    "audio_keys": state.get("audio_keys", []),
                }
            )
            return {"status": response["decision"], "notes": response.get("notes", "")}

        graph = StateGraph(_ReviewState)
        graph.add_node("wait_for_decision", wait_for_decision)
        graph.add_edge(START, "wait_for_decision")
        graph.add_edge("wait_for_decision", END)
        self._graph = graph.compile(checkpointer=checkpointer)

    @staticmethod
    def _config(run_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": run_id}}

    @staticmethod
    def _result(run_id: str, state: _ReviewState) -> ReviewResult:
        return ReviewResult(
            run_id=run_id,
            video_key=state["video_key"],
            audio_keys=state.get("audio_keys", []),
            status=state.get("status", "awaiting_review"),
            notes=state.get("notes", ""),
        )

    async def start(self, request: ReviewRequest) -> ReviewResult:
        if await self.get_result(request.run_id) is not None:
            raise ReviewGateError("review.run_exists", run_id=request.run_id)
        await self._graph.ainvoke(
            {
                "run_id": request.run_id,
                "video_key": request.video_key,
                "audio_keys": request.audio_keys or [],
                "status": "awaiting_review",
            },
            self._config(request.run_id),
        )
        result = await self.get_result(request.run_id)
        if result is None:
            raise ReviewGateError("review.run_not_found", run_id=request.run_id)
        return result

    async def decide(self, run_id: str, decision: ReviewDecision, notes: str = "") -> ReviewResult:
        current = await self.get_result(run_id)
        if current is None:
            raise ReviewGateError("review.run_not_found", run_id=run_id)
        if current.status != "awaiting_review":
            raise ReviewGateError("review.already_decided", run_id=run_id)
        if decision not in ("approve", "request_changes"):
            raise ReviewGateError("review.invalid_decision")
        cleaned_notes = notes.strip()
        if decision == "request_changes" and not cleaned_notes:
            raise ReviewGateError("review.notes_required")
        await self._graph.ainvoke(
            Command(
                resume={
                    "decision": "approved" if decision == "approve" else "changes_requested",
                    "notes": cleaned_notes,
                }
            ),
            self._config(run_id),
        )
        result = await self.get_result(run_id)
        if result is None:
            raise ReviewGateError("review.run_not_found", run_id=run_id)
        return result

    async def get_result(self, run_id: str) -> ReviewResult | None:
        snapshot = await self._graph.aget_state(self._config(run_id))
        if not snapshot.values:
            return None
        return self._result(run_id, snapshot.values)
