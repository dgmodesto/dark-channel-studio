# Board

Local Kanban for Dark Channel Studio. Source of truth for story status (see the constitution).

**Workflow per story:** `specify → plan → tasks → implement (test-first) → test → review → evidence → PR → merge`.
**Commit rule:** one commit per completed feature — `feat(US-00X): <summary>`, with this board updated in the same commit.

Status: `Backlog` · `In Progress` · `Review` · `Done`

## Phase 1 — MVP (English A1/A2 channel)

| ID | Story | Status | Depends on | Spec |
|---|---|---|---|---|
| US-001 | Platform skeleton: Compose stack (Postgres, Redis, API, worker, web), health checks, CI, bilingual shell | Done | — | [specs/001-platform-skeleton](../specs/001-platform-skeleton/spec.md) |
| US-002 | Provider abstraction + cost tracking: `ChatModel`/`TTS` protocols, OpenAI + ElevenLabs adapters, fakes, `cost_event` | Done | US-001 | [specs/002-provider-abstraction](../specs/002-provider-abstraction/spec.md) |
| US-003 | Niche template + channel model: English A1/A2 template as data, channel CRUD in API and UI | Done | US-001 | [specs/003-niche-template-channel-model](../specs/003-niche-template-channel-model/spec.md) |
| US-004 | Script pipeline: LangGraph writer + reviewer loop with bounded iterations and Postgres checkpoints | Done | US-002, US-003 | [specs/004-script-pipeline](../specs/004-script-pipeline/spec.md) |
| US-005 | Voice job: TTS worker producing per-line audio with shadowing pauses | Done | US-002, US-004 | [specs/005-voice-job](../specs/005-voice-job/spec.md) |
| US-006 | Deterministic render: FFmpeg/Remotion with dual EN/PT subtitles, background, music ducking | Done | US-005 | [specs/006-deterministic-render](../specs/006-deterministic-render/spec.md) |
| US-007 | Review player and approval gate: audio/video review UI, approve/request changes resumes the graph | Backlog | US-004, US-006 | — |
| US-008 | Thumbnail and SEO: template-based thumbnail, title/description/tags, disclosure rules | Backlog | US-004 | — |
| US-009 | YouTube OAuth + upload: encrypted tokens, `publishAt` scheduling, quota budgeter, manual-publish fallback | Backlog | US-007, US-008 | — |
| US-010 | Calendar and scheduler: per-channel publication queue respecting quota | Backlog | US-009 | — |
| US-011 | Basic metrics and costs dashboard: analytics sync, cost per video, ROI inputs | Backlog | US-009 | — |

## Backlog (Phase 2 and 3, not yet broken down)

- Multi-channel/multi-niche templates (finance, AI engineering with technical-review gate)
- Analytics feedback into ideation
- Derived Shorts
- Chat command interface and per-channel autonomy
- A/B titles and thumbnails, richer ROI

## Story details

### US-001 Platform skeleton
- [x] `docker compose up` starts Postgres, Redis, API, worker and web
- [x] `/health` on API and worker heartbeat visible
- [x] Web shell routes `/en` and `/pt-BR` with a CI check for missing keys
- [x] CI runs lint and tests

### US-002 Provider abstraction + cost tracking
- [x] `ChatModel` and `TTS` protocols with config-selected adapters
- [x] OpenAI chat and ElevenLabs TTS adapters; fakes for tests
- [x] Every call writes a `cost_event`; per-run budget cap enforced

### US-003 Niche template + channel model
- [x] English A1/A2 template stored as versioned data
- [x] Channel CRUD (API + UI) referencing a template

### US-004 Script pipeline
- [x] Graph: idea → script → review loop (max N iterations) → approved script
- [x] State persisted in Postgres; resumable after restart
- [x] Orchestrator interface hides LangGraph

### US-005 Voice job
- [x] Idempotent TTS job per script line with retry
- [x] Shadowing pauses configurable by template

### US-006 Deterministic render
- [x] Same inputs produce the same video
- [x] Dual subtitles, background, music at -20 dB ducking

### US-007 Review player and approval gate
- [ ] Interrupt pauses the run until a decision is made
- [ ] Approve resumes; request changes routes back with notes

### US-008 Thumbnail and SEO
- [ ] Thumbnail rendered from template with short text
- [ ] Title/description/tags generated; synthetic-content disclosure defaults on

### US-009 YouTube OAuth + upload
- [ ] Tokens encrypted at rest, minimal scopes
- [ ] Upload with `publishAt`; quota reserved before upload
- [ ] Manual-publish fallback when uploads are locked private

### US-010 Calendar and scheduler
- [ ] Calendar view per channel
- [ ] Queue never exceeds daily quota budget

### US-011 Metrics and costs dashboard
- [ ] Views/CTR/retention sync
- [ ] Cost per video and per channel visible
