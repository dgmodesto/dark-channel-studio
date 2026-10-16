# US-008 Verification Record

## Local validation

- `uv run --all-packages pytest -q` — 164 passed.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- In `apps/web`: `npm test` — 22 passed; `npm run typecheck`, `npm run lint`, and `npm run check:translations` — passed.
- In `apps/web`: `npm run build` — production build passed.
- In `apps/api`, with `DATABASE_URL=sqlite+aiosqlite:///:memory:`: `uv run --all-packages alembic upgrade head --sql` — generated the migration chain through revision `0005`.

The test-first red phase is recorded in [test-first.txt](test-first.txt).

## Independent code review

The independent read-only review found one medium-severity issue in the initial migration: pre-existing review rows received an empty thumbnail key, while the API always exposed a thumbnail URL. The review UI then requested a nonexistent asset.

Resolved before merge: legacy rows now return a null thumbnail URL; the migration marks their synthetic-content disclosure as false; and the API rejects approval with `review.synthetic_disclosure_required` until disclosure is confirmed. The UI shows the missing-disclosure warning. No additional findings were reported in the review.

## Merged status

- PR [#9](https://github.com/dgmodesto/dark-channel-studio/pull/9) merged into `main` on 2026-10-16.
- GitHub Actions checks all passed: `python`, `web`, and `compose-smoke`.
- `board/BOARD.md` marks US-008 **Done**; `spec.md` is Implemented and all tasks are checked off.
