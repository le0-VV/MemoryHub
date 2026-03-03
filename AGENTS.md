# AGENTS.md - MemoryHub Project Guide

## Project Overview

MemoryHub is an experimental fork of Basic Memory.

The active fork direction is:

- local-only
- SQLite-only
- multi-project
- agent-neutral

`README.md` describes the current fork status. `README_old.md` preserves the
upstream product README for reference.

## Development Workflow

### Core Commands

- Install: `just install` or `pip install -e ".[dev]"`
- Fast local loop: `just fast-check`
- Full check: `just check`
- Unit tests: `just test-unit-sqlite`
- Integration tests: `just test-int-sqlite`
- Full test suite: `just test`
- Smoke test: `just test-smoke`
- Doctor: `just doctor`
- Lint: `just lint`
- Format: `just format`
- Type check: `just typecheck`
- Supplemental type check: `just typecheck-ty`
- Coverage: `just coverage`
- Single test: `pytest tests/path/to/test_file.py::test_name`

Project requires Python 3.12+.

### Working Rules

- Read a file fully before editing it.
- Keep diffs narrow and task-focused.
- Prefer fail-fast behavior over silent fallback logic.
- Do not guess at attribute names, control flow, or config behavior.
- Add tests for new behavior unless the change is strictly docs/metadata cleanup.
- Keep comments rare and useful. Explain why or constraints, not obvious mechanics.

### Verify Loop

1. Make the change.
2. Run `just fast-check`.
3. Run `just doctor` when the change affects file/database or end-to-end behavior.
4. Run `just test` or `just check` before larger merges.

## Architecture

See `docs/ARCHITECTURE.md` for the fuller design write-up.

### Important Directories

- `/src/memoryhub/api` - FastAPI app and routers
- `/src/memoryhub/cli` - Typer CLI
- `/src/memoryhub/importers` - chat/import tooling
- `/src/memoryhub/markdown` - markdown parsing and formatting
- `/src/memoryhub/mcp` - MCP server, tools, prompts, typed clients
- `/src/memoryhub/models` - SQLAlchemy models
- `/src/memoryhub/repository` - persistence layer
- `/src/memoryhub/services` - business logic
- `/src/memoryhub/sync` - file sync/watch logic
- `/tests` - unit-style tests
- `/test-int` - integration tests

### Current Runtime Model

- SQLite is the only supported database backend.
- Local ASGI routing is the only supported MCP/API routing path.
- Markdown files are the source of truth.
- The app still contains some upstream compatibility shims for old config shapes and names.
- Cloud and Postgres code should be treated as migration baggage unless a file clearly documents otherwise.

### MCP Client Usage

For project-scoped MCP tools:

```python
from memoryhub.mcp.project_context import get_project_client

async with get_project_client(project, context=context) as (client, active_project):
    ...
```

For CLI commands or non-project-scoped code:

```python
from memoryhub.mcp.async_client import get_client

async with get_client(project_name=project_name) as client:
    ...
```

Do not use deprecated module-level HTTP clients or hand-managed auth headers.

## Product Surface

### Supported Direction

- local note storage
- local indexing and search
- multi-project management
- MCP tool access to notes, search, context, and project operations
- import flows for supported local data sources

### Not Part Of This Fork

- hosted cloud MCP service
- per-project cloud routing
- cloud workspaces
- Postgres-backed deployment paths
- Claude-specific repository agent files

If you find code that still assumes those features are current, prefer removing
or isolating it instead of extending it.

## Testing Guidance

- `tests/` covers smaller, isolated components.
- `test-int/` covers real component interaction with the local stack.
- Smoke tests and doctor checks matter for CLI/MCP regressions.
- Keep coverage at 100% when modifying active runtime code.

## Naming Guidance

- User-facing docs should say `MemoryHub` when referring to the forked product.
- Runtime package and CLI names are now `memoryhub`.
- Some compatibility env vars and historical config helpers may still retain
  `BASIC_MEMORY_*` names during the transition.

## Agent Files

- `AGENTS.md` is the main repository guide.
- `.agents/commands/` contains reusable workflow notes for release/spec/test tasks.
- `.agents/TODO.md` is a local ignored scratch plan for ongoing cleanup work.
