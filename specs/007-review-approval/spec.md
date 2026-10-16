# Feature Specification: Review Player and Approval Gate

**Feature Branch**: `007-review-approval` (board story US-007)

**Status**: Implemented

## User Scenarios & Testing

### User Story 1 - Review rendered media (Priority: P1)

As the channel owner, I can review a rendered video and its voice audio before it proceeds, so I can check the final output in the context of its production run.

**Acceptance Scenarios**:

1. Given a rendered run submitted for review, when I open the review page, then I can play the video and its audio and see the run identifier and review status.
2. Given no runs need review, when I open the review page, then I see a clear empty state.
3. Given media cannot be loaded, then the media controls and page report an actionable error without losing the review item.

### User Story 2 - Explicit approval or change request (Priority: P1)

As the channel owner, I can approve a run or request changes with notes, so publishing remains behind an explicit human gate.

**Acceptance Scenarios**:

1. Given a run awaiting review, when I approve it, then the persisted graph resumes with an approved decision and the item is no longer pending.
2. Given a run awaiting review, when I request changes with notes, then the persisted graph resumes with the notes and records a changes-requested decision.
3. Given a run already decided or unknown, then a repeated or invalid decision is rejected with a stable API error code.

## Requirements

- **FR-001**: Review items are persisted and expose video and optional audio media from the shared media store.
- **FR-002**: A LangGraph checkpoint interrupts each submitted run until an explicit approve or request-changes decision resumes it.
- **FR-003**: Request-changes decisions require non-empty notes; approval does not.
- **FR-004**: API errors use stable `{code, params}` envelopes and the web product is bilingual.
- **FR-005**: The web review page provides accessible video/audio playback, pending/decided states, empty/loading/error feedback, and keyboard-operable decision controls.
- **FR-006**: Media keys are confined to the configured media root and never permit path traversal.

See [the review API contract](contracts/reviews.md) for endpoint details.

## Assumptions

- The existing local-first single-owner deployment does not require authentication in this story.
- Render and voice keys use the worker's shared filesystem store; a Docker named volume makes those files available to the API.
- Requesting changes resumes the approval graph with a `changes_requested` result and notes. The returned state is the handoff for a subsequent production revision; this story does not add an LLM writer or publish job.

## Out of Scope

- Automatic script rewriting or re-rendering after requested changes.
- Publishing, scheduling, or external media hosting.
