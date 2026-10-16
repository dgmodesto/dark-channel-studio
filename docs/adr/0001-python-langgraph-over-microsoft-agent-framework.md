# ADR-0001: Python + LangGraph over Microsoft Agent Framework

- Status: Accepted

## Context
The pipeline needs durable, resumable workflows with human approval that can wait days, per-step budgets, and tight integration with media tooling (FFmpeg, TTS, Whisper-class libs), which is Python-centric.

## Decision
Use Python (FastAPI) with **LangGraph** for agentic workflows: checkpointing in Postgres (`langgraph-checkpoint-postgres`), `interrupt()` for human-in-the-loop, conditional edges for budget-aware loops. LangChain is used thinly (chat models, Pydantic structured output). LangGraph is confined to one adapter behind an `Orchestrator` interface.

## Alternatives
- **Microsoft Agent Framework**: strong .NET/Azure story and good workflow support, but the media/ML ecosystem and checkpoint/HITL pattern we need are more mature on the Python/LangGraph side for this project; choosing it would split the stack.
- **Hand-rolled state machine**: full control but re-implements checkpointing and interrupts.

## Consequences
- Fast path to durable HITL; Postgres is the single store.
- Framework churn risk is contained by the interface; domain state lives in our tables, not only in checkpoints.
