# Post-v0.18.0 Test Plan and Acceptance Criteria

> Historical note: this document captured a pre-fork validation plan while the repository still
> tracked upstream cloud and Postgres work. It is preserved for context, not as current guidance.

## What still matters

The useful parts of the old plan were:

- feature-focused acceptance criteria
- real MCP integration testing
- black-box validation of schema and search behavior
- explicit coverage gap tracking

Those remain good engineering habits for the fork.

## What is no longer current

Do not treat this file as the current release checklist for MemoryHub. It assumes:

- Postgres parity testing
- cloud routing and auth flows
- release-era upstream backlog state
- test commands that no longer exist in the fork

## Current replacement guidance

For the fork as it exists now:

1. Run SQLite-only test and validation flows.
2. Treat local MCP behavior, note sync, schema flows, and semantic search as the critical paths.
3. Prefer current repo docs and current test files over this historical planning note.

Useful current commands:

- `just fast-check`
- `just coverage`
- `memoryhub doctor`
- `pytest tests -q`
- `pytest test-int -q`

## Why this file still exists

This note is still useful as an audit trail for:

- what upstream was validating before the fork diverged
- which feature areas were considered high-risk
- how MCP, schema, and search testing were organized

If you need the live testing policy for the fork, use:

- `README.md`
- `tests/README.md`
- `docs/testing-coverage.md`
