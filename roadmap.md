# MemoryHub Roadmap

MemoryHub is a local OpenViking implementation layer that adapts repo-local
context folders into one central runtime, registry, and SQLite-backed derived
database.

## Product Thesis

MemoryHub exists to provide reusable local OpenViking-style context
infrastructure for agents:

- one managed runtime/install root per machine
- project-owned OpenViking-style context folders inside repositories
- central project registry paths under the runtime root, normally symlinks back
  to those repo-local context folders
- SQLite-backed derived state for search, relations, and embeddings
- MCP over stdio as the first supported agent interface
- a thin CLI for installation, project registration, doctor checks, and reindex
- OpenViking-style directory conventions and resource semantics, with full API,
  CLI, package, import/export, or server compatibility claimed only after those
  contracts are specified and tested

MemoryHub's core value is adapting OpenViking-style project context into a
single local hub: repositories own their context folders, while MemoryHub owns
the central registry, database, indexing, runtime environment, and MCP surface.

## Design Principles

- Keep Markdown as the source of truth.
- Treat SQLite, search indexes, vector tables, logs, and caches as derived or
  disposable runtime state.
- Keep one central runtime root per machine.
- Keep project context files owned by the project repository.
- Make framework contracts importable and testable without starting MCP, CLI, or
  web services.
- Keep adapters thin. MCP and CLI should expose framework behaviour, not own
  business rules.
- Prefer explicit failure over silent fallback.
- Keep type checking clean. Pylance/pyright cleanliness is part of done work.
- Add tests with every behavior change.

## Non-Goals

- No hosted cloud service.
- No Postgres backend.
- No per-repository runtime installations.
- No full OpenViking feature-parity claim before a written compatibility spec.
- No product-specific agent assumptions in core framework code.
- No hidden background source of truth beyond the Markdown source tree.

## Core Contracts

### Central Runtime Root

`MEMORYHUB_CONFIG_DIR` identifies the whole runtime root. If unset, it defaults
to:

```text
~/.memoryhub
```

The runtime root owns:

```text
~/.memoryhub/
├── bin/
├── cache/
│   ├── pip/
│   ├── uv/
│   └── xdg/
├── config.json
├── memory.db
├── memoryhub.log
├── models/
│   └── fastembed/
├── projects/
│   ├── main/
│   └── <project> -> <repo>/.agents/memoryhub/
├── runtime/
└── venv/
```

### Project Context Source

Each repository owns its Markdown context source:

```text
<repo>/.agents/memoryhub/
├── agent/
│   ├── memories/
│   │   ├── cases/
│   │   ├── patterns/
│   │   ├── skills/
│   │   └── tools/
│   └── skills/
├── resources/
└── user/
    └── memories/
        ├── entities/
        ├── events/
        └── preferences/
```

The central runtime references each project through:

```text
$MEMORYHUB_CONFIG_DIR/projects/<project>
```

That path is normally a symlink back to the repo-local `.agents/memoryhub/`
directory.

### Global Memory

`$MEMORYHUB_CONFIG_DIR/projects/main` is the stand-alone Markdown context tree
for global or uncategorised context that does not belong to a repository.

### Agent Surface

The initial agent surface is MCP over stdio:

```bash
memoryhub mcp
```

The initial MCP tool set should be small:

- project list/discover
- search
- read
- write
- context/build-context
- status/doctor

Every MCP response that depends on project routing should include explicit
project/routing metadata.

## Target Package Layout

```text
src/memoryhub/
├── framework/
│   ├── layout.py
│   ├── project_source.py
│   ├── registry.py
│   ├── runtime.py
│   └── errors.py
├── storage/
│   └── sqlite/
│       ├── connection.py
│       ├── migrations/
│       ├── models.py
│       ├── search.py
│       └── vectors.py
├── sources/
│   └── markdown/
│       ├── parser.py
│       ├── serializer.py
│       ├── sync.py
│       └── schema.py
├── openviking/
│   ├── layout.py
│   ├── resources.py
│   ├── uris.py
│   └── compatibility.py
├── adapters/
│   ├── cli/
│   └── mcp/
└── __init__.py
```

Keep internal dependencies one-way:

```text
adapters -> framework -> sources/storage/openviking
```

Adapters may depend on framework services. Framework services may depend on
source/storage/openviking contracts. Storage and source layers should not import
MCP or CLI code.

## Milestones

### Milestone 1: Empty Project Skeleton

- [ ] Create `pyproject.toml` for package `memoryhub`.
- [ ] Require Python 3.12+.
- [ ] Configure `ruff`, `pyright`, and `pytest`.
- [ ] Add `README.md`, `LICENSE`, `NOTICE`, `AGENTS.md`, and this roadmap.
- [ ] Add empty package directories for framework, storage, sources,
      openviking, and adapters.
- [ ] Add CI or local `just` commands for lint, typecheck, and tests.

Exit criteria:

- `pytest`, `ruff check`, and `pyright` run on an empty implementation.

### Milestone 2: Framework Layout Primitives

- [ ] Implement central runtime layout resolution.
- [ ] Implement OpenViking-style project source layout objects.
- [ ] Implement global context source layout.
- [ ] Implement deterministic directory creation for runtime and project source
      trees.
- [ ] Implement strict validation for empty names, invalid paths, conflicting
      files, and unsafe symlink targets.

Exit criteria:

- Tests prove `MEMORYHUB_CONFIG_DIR`, `~/.memoryhub`, `projects/main`, and
  `.agents/memoryhub/` resolve correctly without starting any service.

### Milestone 3: Project Registry

- [ ] Define a project registry data model.
- [ ] Store registry metadata in `config.json`.
- [ ] Add project add/list/remove/default operations.
- [ ] Create or validate symlinks under `$MEMORYHUB_CONFIG_DIR/projects/`.
- [ ] Resolve projects by explicit name, cwd, repository identifier, and
      default project.
- [ ] Fail fast on ambiguous names, duplicate slugs, stale paths, and symlink
      conflicts.

Exit criteria:

- A setup tool can register a repository and resolve it by cwd without invoking
  MCP or touching SQLite.

### Milestone 4: SQLite Derived State

- [ ] Define the minimal SQLite schema.
- [ ] Add migration bootstrap.
- [ ] Add project/source file tracking tables.
- [ ] Add text search tables.
- [ ] Add vector storage only after text indexing is stable.
- [ ] Add rebuild-from-Markdown flow.
- [ ] Add backup and recovery commands.

Exit criteria:

- Deleting `memory.db` and running reindex rebuilds derived state from Markdown
  source trees.

### Milestone 5: Markdown Source Layer

- [ ] Define the Markdown file format.
- [ ] Define frontmatter fields.
- [ ] Define resource, memory, skill, and relation representation.
- [ ] Implement parser and serializer.
- [ ] Preserve unknown frontmatter and user-authored content.
- [ ] Add sync rules that never make SQLite the source of truth.

Exit criteria:

- Round-trip tests prove Markdown files can be parsed, indexed, written, and
  re-read without losing user content.

### Milestone 6: Search And Context

- [ ] Implement FTS search.
- [ ] Implement metadata filters.
- [ ] Implement path/category filters.
- [ ] Add optional local embedding provider.
- [ ] Add hybrid search only after FTS is predictable.
- [ ] Implement context assembly for agent prompts.

Exit criteria:

- Agents can search across one or more registered projects and receive stable
  project-aware results.

### Milestone 7: MCP Adapter

- [ ] Add a FastMCP stdio server.
- [ ] Register minimal tools: project list, search, read, write, context,
      status/doctor.
- [ ] Keep MCP startup local-only.
- [ ] Keep logging off stdout.
- [ ] Add project/routing metadata to relevant responses.
- [ ] Add MCP smoke tests.

Exit criteria:

- A local MCP client can run `memoryhub mcp`, list projects, search, read, and
  write notes.

### Milestone 8: CLI Adapter

- [ ] Add `memoryhub install`.
- [ ] Add `memoryhub doctor`.
- [ ] Add `memoryhub project add/list/remove/default`.
- [ ] Add `memoryhub reindex`.
- [ ] Add `memoryhub mcp`.
- [ ] Add JSON output for automation.
- [ ] Keep CLI implementation thin over framework services.

Exit criteria:

- `agent-basics` or another setup tool can install MemoryHub, register a repo,
  validate health, and configure MCP using only stable CLI commands.

### Milestone 9: Installer And Update Flow

- [ ] Add a stand-alone install script as a thin wrapper around CLI/framework
      behavior.
- [ ] Install into `$MEMORYHUB_CONFIG_DIR/venv`.
- [ ] Create `$MEMORYHUB_CONFIG_DIR/bin/memoryhub`.
- [ ] Keep package, pip, uv, xdg, and model caches under the runtime root.
- [ ] Add update and repair behavior.

Exit criteria:

- A fresh macOS machine can install MemoryHub into `~/.memoryhub` and run
  `memoryhub doctor` successfully.

### Milestone 10: OpenViking Compatibility Contract

- [ ] Write a compatibility spec before claiming compatibility.
- [ ] Define which OpenViking URI/resource semantics are supported.
- [ ] Define import/export expectations.
- [ ] Define unsupported OpenViking features explicitly.
- [ ] Add conformance tests for each supported compatibility claim.

Exit criteria:

- Documentation and tests agree on the exact meaning of
  `OpenViking implementation layer`.

## Verification Strategy

Every milestone needs focused tests before it is considered complete:

- layout tests
- project source-tree tests
- symlink registry tests
- config serialization tests
- SQLite migration/rebuild tests
- Markdown round-trip tests
- search ranking/filter tests
- MCP stdio smoke tests
- CLI JSON contract tests
- pyright/Pylance-clean touched code

The default fast check should run:

```bash
ruff check
pyright
pytest
```

## First Implementation Slice

Start with the smallest useful vertical slice:

1. Package skeleton.
2. Runtime layout object.
3. Project source layout object.
4. Project registry stored in JSON config.
5. CLI commands: `project add`, `project list --json`, `doctor`.
6. MCP server with `project list`.
7. Tests for all of the above.

Do not add search, embeddings, importers, or broad note graph behavior until the
layout and registry contracts are stable.
