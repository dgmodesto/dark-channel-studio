# Feature Specification: Platform Skeleton

**Feature Branch**: `001-platform-skeleton` (board story US-001)

**Created**: 2026-10-16

**Status**: Draft

**Input**: User description: "Platform skeleton: Compose stack (Postgres, Redis, API, worker, web), health checks, CI, bilingual shell"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start the whole platform with one command (Priority: P1)

As the owner, I start every platform component locally with a single command and can see that each one is running and healthy, so every later feature has a working foundation to build on.

**Why this priority**: Nothing else can be built or demonstrated without a runnable environment. It is the walking skeleton for the MVP.

**Independent Test**: On a clean machine with only the documented prerequisites, run the single start command and verify that all components report healthy within the expected time.

**Acceptance Scenarios**:

1. **Given** a fresh clone with the example configuration copied, **When** the owner runs the start command, **Then** the database, queue store, API, background worker and web portal all start and report healthy.
2. **Given** the platform is running, **When** the owner checks the API health endpoint, **Then** it reports the status of the API and of its database and queue dependencies.
3. **Given** the platform is running, **When** the owner checks the worker status, **Then** a recent worker heartbeat is visible.
4. **Given** one dependency (for example the database) is stopped, **When** the owner checks health, **Then** the affected component is reported unhealthy with a clear reason rather than the whole check failing silently.

---

### User Story 2 - Open the portal in English or Brazilian Portuguese (Priority: P1)

As the owner, I open the web portal and see a shell page in my chosen language (English or Brazilian Portuguese) and can switch languages at any time.

**Why this priority**: Bilingual support is a day-one product requirement; retrofitting it later is costly.

**Independent Test**: Open the portal in each locale and verify the shell content and language switcher; run the translation completeness check.

**Acceptance Scenarios**:

1. **Given** the portal is running, **When** the owner opens the English route, **Then** the shell is shown in English.
2. **Given** the portal is running, **When** the owner opens the Brazilian Portuguese route, **Then** the same shell is shown in Brazilian Portuguese.
3. **Given** the owner is on any page, **When** they use the language switcher, **Then** they stay on the equivalent page in the other language.
4. **Given** a text key exists in one language but is missing in the other, **When** the automated translation check runs, **Then** it fails and names the missing key.
5. **Given** the owner opens the portal root with no language chosen, **When** the page loads, **Then** they are redirected to a default language based on their browser preference, falling back to English.

---

### User Story 3 - Every change is automatically verified (Priority: P2)

As the owner, every proposed change is automatically checked for code style, tests and translation completeness, so regressions are caught before merging.

**Why this priority**: Supports the constitution's test-first and evidence-backed principles, but the platform can run without it.

**Independent Test**: Open a change that deliberately breaks a check and confirm it is reported as failing; open a clean change and confirm all checks pass.

**Acceptance Scenarios**:

1. **Given** a proposed change, **When** it is submitted, **Then** style checks, automated tests and the translation check run automatically and their results are visible on the change.
2. **Given** a proposed change that breaks any check, **When** results are reported, **Then** the change is marked as failing.

---

### Edge Cases

- A required configuration value is missing: the component fails fast at startup with a message naming the missing value, and no secret is ever printed.
- A port needed by a component is already in use: the owner gets a clear message and can override the port through configuration.
- The queue store or database is slow to become ready at startup: dependent components wait and retry instead of crashing permanently.
- Persistent data (database, queue store) survives a restart of the platform; a documented command resets it.
- The browser requests an unsupported language: the portal falls back to English.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The platform MUST start the database, queue store, API, background worker and web portal with one documented command.
- **FR-002**: Every component MUST expose a health signal; the API MUST expose a health endpoint that reports its own status and the status of its database and queue dependencies.
- **FR-003**: The background worker MUST publish a periodic heartbeat that the owner can inspect.
- **FR-004**: Components MUST wait for their dependencies to be ready and retry before failing.
- **FR-005**: All configuration MUST come from environment values with a committed example file; real secrets MUST never be committed.
- **FR-006**: Missing or invalid required configuration MUST stop startup with a clear, secret-free error.
- **FR-007**: Database and queue data MUST persist across restarts, with a documented reset procedure.
- **FR-008**: The web portal MUST provide locale-prefixed routes for English and Brazilian Portuguese showing the same shell content.
- **FR-009**: The portal MUST offer a language switcher that preserves the current page, and MUST choose a default language from browser preference with English as fallback.
- **FR-010**: All user-visible portal text MUST come from translation catalogs; API errors MUST be returned as codes with parameters, never as localized text.
- **FR-011**: An automated check MUST fail when any translation key is missing in either language.
- **FR-012**: An automated pipeline MUST run style checks, tests and the translation check on every proposed change and report the result on it.
- **FR-013**: The repository MUST document prerequisites, the start command, health checks and the reset procedure in English.
- **FR-014**: The API and worker MUST emit structured logs that include a correlation identifier field for later features to populate.

### Key Entities

- **Component**: A running part of the platform (database, queue store, API, worker, portal) with a health status.
- **Worker Heartbeat**: A timestamped signal showing the worker is alive.
- **Translation Catalog**: The set of text keys and their values for one language.
- **Configuration**: The set of environment values required to run the platform, with an example template.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a fresh clone, the owner has all five components healthy in under 5 minutes using only the documented steps.
- **SC-002**: A health check returns a complete result in under 2 seconds, including the reason when a dependency is unhealthy.
- **SC-003**: 100% of user-visible portal text exists in both languages, enforced by an automated check.
- **SC-004**: The owner can switch language from any page in one action without losing their place.
- **SC-005**: 100% of proposed changes receive automated check results within 10 minutes.
- **SC-006**: Restarting the platform loses no persisted data.

## Assumptions

- The owner runs the platform locally on a single machine with a container runtime installed (ADR-0004).
- Single owner; no sign-in is part of this story (authentication is added in a later story and the portal is bound to localhost by default).
- The shell page shows only the product name, a status placeholder and navigation placeholders; no domain features yet.
- Technology choices follow `docs/design.md` and the ADRs and are decided in the plan, not in this spec.
- Continuous integration uses the repository's existing hosting platform.
