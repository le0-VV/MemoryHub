# MemoryHub Architecture

This fork still ships under the inherited Python package and CLI names, `basic_memory` and
`basic-memory`, but the product direction is MemoryHub: a local-first MCP memory system for many
projects on one machine.

## Overview

The current architecture is intentionally simple:

- Markdown files are the source of truth.
- SQLite is the only supported database backend.
- The app exposes three entrypoints: API, MCP, and CLI.
- Semantic search, when enabled, is built on SQLite plus local vector tables.
- File watching and sync are local-only background services.

At a high level:

```text
Markdown files
    ↓
Parser + sync/watch services
    ↓
SQLite index and search tables
    ↓
FastAPI application
    ↓
MCP tools / CLI commands
```

## Entrypoints

The repo has three user-facing entrypoints:

- `API`: FastAPI routers under `src/basic_memory/api/`
- `MCP`: the stdio/HTTP MCP server under `src/basic_memory/mcp/`
- `CLI`: the Typer app under `src/basic_memory/cli/`

Each entrypoint has a composition root in `container.py`. The composition root is the only place
that should read global config and assemble concrete dependencies.

```text
src/basic_memory/
├── api/container.py
├── cli/container.py
├── mcp/container.py
└── runtime.py
```

## Runtime Model

The fork now treats runtime mode as a local concern:

- `TEST`: isolated test environment
- `LOCAL`: normal app runtime

Historical cloud-oriented compatibility code still exists in parts of the tree, but it is not part
of the supported architecture for this fork.

Runtime mode decides whether to start local background services such as file watching. It is not a
network-routing feature anymore.

## Composition Roots

Every container follows the same pattern:

1. Read `ConfigManager`
2. Resolve runtime mode
3. Build explicit dependencies
4. Expose those dependencies to tools, routers, or commands

This keeps configuration lookup centralized and makes the rest of the codebase easier to test.

## Core Request Flow

The main request path is:

```text
CLI command or MCP tool
    ↓
typed API client
    ↓
FastAPI router
    ↓
service layer
    ↓
repository layer
    ↓
SQLite
```

This matters because MCP tools are intentionally thin. Business rules belong in services and
repositories, not in tool handlers.

## Typed MCP Clients

MCP tools talk to the API through typed clients in `src/basic_memory/mcp/clients/`:

- `KnowledgeClient`
- `SearchClient`
- `MemoryClient`
- `DirectoryClient`
- `ResourceClient`
- `ProjectClient`
- `SchemaClient`

Those clients encapsulate HTTP paths and response validation so the tool layer stays small.

## Projects and Resolution

Projects are the main isolation boundary. A project is a local directory of notes plus an indexed
database view of that directory.

Project selection is unified through `ProjectResolver`:

1. explicit project argument
2. configured default project
3. single available project

The fork vision is to get smarter about workspace inference over time, but the current
implementation is still explicit-project-first.

## Storage Model

The storage model is local-first and SQLite-only:

- Markdown files are canonical.
- SQLite holds derived state for search, relations, metadata, and semantic chunks.
- Reindexing and sync rebuild derived state from files when needed.

There is no supported Postgres path in this fork.

## Search Architecture

Search currently has three layers:

1. FTS-style text search in SQLite
2. metadata/frontmatter filtering
3. optional vector and hybrid search on SQLite vector tables

Semantic search is still local. The app can use either:

- `fastembed` for fully local embeddings
- `openai` for remote embedding generation while the deployment remains local

## Sync and Watch Services

`src/basic_memory/sync/` manages file watching and local indexing lifecycle.

Important boundaries:

- watchers read local files only
- sync updates SQLite derived state from files
- background tasks should never become a hidden source of truth

`SyncCoordinator` is the lifecycle hub for starting and stopping those background services.

## Dependencies Layout

The `deps/` package provides feature-scoped FastAPI dependencies:

```text
src/basic_memory/deps/
├── config.py
├── db.py
├── importers.py
├── projects.py
├── repositories.py
└── services.py
```

New code should import from the specific dependency module it needs rather than from broad
re-export shims.

## Main Source Directories

```text
src/basic_memory/
├── api/          FastAPI app and routers
├── cli/          Typer app and command groups
├── config.py     Config models and manager
├── deps/         FastAPI dependency providers
├── importers/    Chat export and external import flows
├── markdown/     Markdown parsing and rendering helpers
├── mcp/          MCP server, tools, prompts, and typed clients
├── models/       SQLAlchemy models
├── repository/   Data access and search backends
├── schema/       Schema parsing, validation, inference, and diffing
├── services/     Business logic
└── sync/         File watch and sync lifecycle
```

## Design Principles

### Explicit dependencies

Pass config and collaborators in explicitly. Avoid hidden global reads outside composition roots.

### Thin adapters

Routers, tools, and CLI commands should translate inputs and outputs, then defer to services.

### Markdown-first

Files outlive any one runtime. Derived database state should always be rebuildable.

### Local-first support surface

Documentation and active code paths should optimize for local, SQLite-backed deployments first.

### Compatibility is not the same as product direction

Some inherited upstream code still exists for transition reasons. Treat docs and new development as
the source of truth for what is actually supported.
