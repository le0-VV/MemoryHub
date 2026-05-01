# MemoryHub

MemoryHub is a clean-slate local implementation layer for OpenViking-style
agent context. It adapts repository-owned Markdown context folders into one
machine-local runtime, registry, and SQLite-backed derived database.

The current source of truth is `roadmap.md`.

## Current Scope

- one local runtime root, defaulting to `~/.memoryhub`
- project context folders under each repository's `.agents/memoryhub/`
- central project registry paths under `$MEMORYHUB_CONFIG_DIR/projects/`
- JSON config for project registration
- thin CLI over framework services
- MCP over stdio as the first agent interface

MemoryHub does not yet claim full OpenViking compatibility. Compatibility
claims will be added only after the supported contracts are specified and
tested.

## Development

Install dependencies:

```bash
uv sync
```

Run the fast local check:

```bash
uv run ruff check .
uv run pyright
uv run pytest
```

The `memoryhub` console script is provided by the Python package.
