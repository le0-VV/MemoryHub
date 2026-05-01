# AGENTS.md - MemoryHub Project Guide

## Instructions

MemoryHub is being rebuilt from a clean slate as a local OpenViking
implementation layer. The product adapts repository-owned OpenViking-style
context folders into one central machine-local runtime, registry, and
SQLite-backed derived database.

The authoritative implementation plan is `roadmap.md`. If this file and the
roadmap disagree, follow the roadmap and update this file in the same
checkpoint.

The active product direction is:

- local-only
- SQLite-only for derived state
- multi-project
- agent-neutral
- one central runtime/install root under `~/.memoryhub` by default
- repo-local Markdown context folders under `.agents/memoryhub/`
- central project registry paths under `$MEMORYHUB_CONFIG_DIR/projects/`,
  normally symlinked back to repo-local context folders
- MCP over stdio as the first supported agent interface
- thin CLI over framework services
- explicit framework, storage, source, OpenViking, CLI, and MCP boundaries

Do not rebuild the deleted Basic Memory-derived application shape. The old
fork history is not a design constraint for new code.

MemoryHub should not claim full OpenViking API, CLI, package, import/export, or
server compatibility until the compatibility contract is written and tested.
Use `OpenViking-style`, `OpenViking-aligned`, or `OpenViking implementation
layer` for the current product boundary.

### Target Package Layout

The roadmap target is:

```text
src/memoryhub/
|-- framework/
|   |-- layout.py
|   |-- project_source.py
|   |-- registry.py
|   |-- runtime.py
|   `-- errors.py
|-- storage/
|   `-- sqlite/
|       |-- connection.py
|       |-- migrations/
|       |-- models.py
|       |-- search.py
|       `-- vectors.py
|-- sources/
|   `-- markdown/
|       |-- parser.py
|       |-- serializer.py
|       |-- sync.py
|       `-- schema.py
|-- openviking/
|   |-- layout.py
|   |-- resources.py
|   |-- uris.py
|   `-- compatibility.py
|-- adapters/
|   |-- cli/
|   `-- mcp/
`-- __init__.py
```

Keep dependencies one-way:

```text
adapters -> framework -> sources/storage/openviking
```

Adapters may depend on framework services. Framework services may depend on
source, storage, and OpenViking contracts. Storage and source layers must not
import CLI or MCP code.

### Core Runtime Contract

- `MEMORYHUB_CONFIG_DIR` identifies the runtime root.
- If unset, `MEMORYHUB_CONFIG_DIR` defaults to `~/.memoryhub`.
- The runtime root owns binaries, the Python environment, config, SQLite state,
  caches, embedding models, logs, runtime state, global context, and project
  registry symlinks.
- Project-owned context remains plain Markdown under each repository's
  `.agents/memoryhub/`.
- `$MEMORYHUB_CONFIG_DIR/projects/main` is the stand-alone global context tree.
- `$MEMORYHUB_CONFIG_DIR/projects/<project>` is normally a symlink to the
  repository-local `.agents/memoryhub/` folder.
- Markdown files are the source of truth.
- SQLite, search indexes, vector tables, logs, and caches are derived or
  disposable runtime state.

### First Implementation Slice

Build the smallest useful vertical slice first:

1. Package skeleton.
2. Runtime layout object.
3. Project source layout object.
4. Project registry stored in JSON config.
5. CLI commands: `project add`, `project list --json`, `doctor`.
6. MCP stdio server with `project list`.
7. Tests for all of the above.

Do not add search, embeddings, importers, or broad note graph behavior until
the layout and registry contracts are stable.

### Coding Etiquette

- Find up-to-date documentation for any library, framework, and programming
  language used in this project, and record source URLs in
  `./.agents/DOCUMENTATIONS.md`.
- While writing code, refer to sources recorded in
  `./.agents/DOCUMENTATIONS.md` to avoid guessing at APIs or standards.
- Anything the user asks you to remember, record under the `## Memory` section
  in this file.
- When `.agents/DOCUMENTATIONS.md` is updated, commit only
  `.agents/DOCUMENTATIONS.md` with commit message:
  `docs(agent docs): agent added more doc sources`.
- When the `## Memory` section is updated, commit only `AGENTS.md` with commit
  message: `docs(agent memory): update memory`.
- If you have any questions or concerns, clarify with the user immediately.
- Before making codebase changes, plan the work in `./.agents/TODO.md` and
  follow it.
- Tick off every item completed in `./.agents/TODO.md`.
- Read a file fully before editing it.
- Keep diffs narrow and task-focused.
- Do not guess at attribute names, control flow, config behavior, or file
  layout.
- Be strict with types and treat Pylance/pyright cleanliness as part of done
  work.
- Prefer fail-fast behavior over silent fallback logic.
- Add tests for new behavior unless the change is strictly docs or metadata.
- Keep comments rare and useful. Explain why or constraints, not obvious
  mechanics.
- Only stop working when everything listed in `./.agents/TODO.md` is complete
  or when progress requires user intervention with no reasonably safe
  alternative.
- If everything is ticked off in `./.agents/TODO.md` and a new work round is
  needed, clear it and write the new plan.
- Commit messages must use `{type}({scope}): {description}` with one of:
  `build`, `chore`, `CI`, `docs`, `feat`, `fix`, `perf`, `refactor`,
  `revert`, `style`, or `test`.

## Preferences

### Development Workflow

The initial implementation should provide these commands through `just` or
documented `uv` equivalents:

- Install: `uv sync`
- Fast local loop: `just fast-check`
- Full check: `just check`
- Unit tests: `just test`
- Doctor: `just doctor`
- Lint: `just lint`
- Format: `just format`
- Type check: `just typecheck`
- Single test: `uv run pytest tests/path/to/test_file.py::test_name`

Project code requires Python 3.12+.

#### Verify Loop

1. Make the change.
2. Run `just fast-check` when available, otherwise run the equivalent
   `uv run ruff check`, `uv run pyright`, and `uv run pytest`.
3. Run `memoryhub doctor` or `just doctor` when a change affects runtime layout,
   project registration, files, or end-to-end behavior.
4. Run the full check before larger merges.

### Product Surface

- runtime layout management
- repo-local context source registration
- central project registry
- SQLite-derived state
- local indexing and search
- MCP tool access to projects, notes, search, context, and status
- thin CLI for install, project operations, reindex, doctor, and MCP startup

### Not Part Of The Current Scope

- hosted cloud service
- Postgres backend
- per-repository runtime installations
- cloud workspaces
- cloud MCP routing
- agent-vendor-specific repository files
- full OpenViking feature parity before a written compatibility spec
- deleted Basic Memory product-shaped modules

### Testing Guidance

- `tests/` covers focused unit and contract tests.
- Add integration or smoke tests only when a real adapter or end-to-end flow
  exists.
- Runtime layout, symlink registry, config serialization, CLI JSON contracts,
  and MCP stdio behavior need tests before their milestones count as complete.
- Keep touched code Pylance/pyright-clean.

### Naming Guidance

- User-facing docs should say `MemoryHub` for this project.
- Runtime package and CLI names are `memoryhub`.
- Use `context` for repository-owned OpenViking-style files.
- Use `memory` only when referring to user-visible memory resources or global
  uncategorized memory, not as the generic name for every project source.

## Memory

- `.agents/` contains agent-neutral workflow documents for this repository.
- `AGENTS.md` is the main repository guide.
- `roadmap.md` is the authoritative product and implementation plan.
- `.agents/commands/` contains reusable workflow notes for release, spec, and
  test tasks.
- `.agents/TODO.md` is a local ignored scratch plan for ongoing work.
- These files are intentionally system-agnostic. They should not assume a
  specific assistant product, slash-command syntax, or vendor-specific
  metadata.
- The repository was reset to a fresh git history on 2026-05-02. Treat the
  current codebase as a greenfield rebuild, not as a Basic Memory fork migration.
- `agent-basics` is the sibling bootstrap repository at
  `/Users/leonardw/Projects/agent-basics`.
- Future MemoryHub work for `agent-basics` should preserve the central-hub
  contract: one MemoryHub runtime under `$MEMORYHUB_CONFIG_DIR`, repo-local
  context under each project's `.agents/memoryhub/`, hub project symlinks under
  `$MEMORYHUB_CONFIG_DIR/projects/`, stable `memoryhub project add/list/doctor`
  CLI behavior, and no return to per-repo OpenViking runtimes.
