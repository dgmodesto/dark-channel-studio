# ADR-0002: Deterministic workers vs agents split

- Status: Accepted

## Context
Some steps need judgment (research, scripting, critique); others must be repeatable and cheap (TTS, render, upload). Mixing them makes cost, failures and reproducibility hard to control.

## Decision
- **Agents (LangGraph)** own judgment: ideation, script, critique, technical review, SEO copy, planning.
- **Workers (Redis + Arq)** own deterministic execution: TTS, asset fetch/generation calls, FFmpeg/Remotion render, thumbnail composition, upload, analytics sync. No LLM decisions inside workers.
- The graph dispatches jobs with idempotency keys and waits for artifacts; workers write to disk and register assets.

## Consequences
- Renders are reproducible and testable without an LLM.
- Retries are safe and cheap; agent loops are budget-capped.
- Slight orchestration overhead (dispatch/await), accepted.
