# MemoryHub Roadmap

This document is the long-term migration todo for turning the current forked codebase into the MemoryHub described in [README.md](README.md): local-only, SQLite-only, multi-project, and agent-neutral.

The codebase already has the right core primitives: Markdown-backed notes, SQLite indexing, a FastAPI app, MCP tools, a CLI, and project management. The main gap is that those pieces still reflect a transitional fork. Much of the tree still carries upstream compatibility for cloud routing, Postgres, transport-era flags, and legacy naming. The roadmap below focuses on removing that mismatch first, then building the routing hub that makes the fork worth existing.

## Guiding Constraints

- Keep Markdown files as the source of truth.
- Keep SQLite as the only supported database backend.
- Treat projects as the main isolation boundary.
- Prefer local ASGI/API composition over extra network-routing modes.
- Preserve agent neutrality at the MCP layer and in user-facing docs.
- Remove or isolate upstream baggage instead of extending it.

## What The Roadmap Is Optimizing For

- One MemoryHub instance serving many repositories.
- Project resolution that does not depend on manually passing `--project` everywhere.
- Predictable project isolation for concurrent agent sessions.
- A simpler implementation surface with fewer legacy switches and compatibility shims.
- Test coverage and docs that describe the supported product, not the upstream history.

## Current Migration Pressure

These are the main seams this roadmap addresses:

- Project resolution is still mostly explicit-parameter or env-driven, with only a light CWD fallback in `src/memoryhub/project_resolver.py`.
- The client and CLI layers still model "routing" as an optional transport choice even though the fork is local-only, for example in `src/memoryhub/mcp/async_client.py` and `src/memoryhub/cli/commands/routing.py`.
- Config, services, migrations, tests, and comments still carry substantial cloud/Postgres compatibility baggage.
- Legacy `BASIC_MEMORY_*` names are still the dominant public config surface.
- Project and routing context are not yet centralized into a dedicated MemoryHub registry/cache layer.
- Several tests still exercise removed or unsupported cloud/Postgres behavior rather than converging on the fork's supported surface.

## Phased Todo

### Phase 1: Lock The Supported Surface

- [ ] Publish a short support matrix covering what MemoryHub supports today: local runtime, SQLite, Markdown-first storage, multi-project management, MCP/API/CLI entrypoints.
- [ ] Mark cloud routing, cloud workspaces, and Postgres as unsupported everywhere user-facing docs still imply otherwise.
- [ ] Audit CLI help text, router docstrings, comments, and MCP tool descriptions for outdated "local vs cloud" wording.
- [ ] Replace "compatibility" language that sounds permanent with explicit deprecation and removal targets.
- [ ] Add a single architecture section that distinguishes "supported", "transitional", and "scheduled for removal" code paths.

Exit criteria:

- New contributors can tell, without reading the git history, what MemoryHub does and does not support.

### Phase 2: Establish A Real Project Registry Layer

- [ ] Introduce a dedicated project registry service that owns project lookup, normalization, caching, and invalidation.
- [ ] Move project discovery inputs into that layer: explicit project id/name, cwd, memory URL prefix, configured default project, and repo-root metadata.
- [ ] Define a first-class routing context object instead of passing project names and env flags through loosely coupled helpers.
- [ ] Make API, MCP, and CLI entrypoints all depend on the same registry and routing context contract.
- [ ] Add clear conflict handling for ambiguous cwd matches, duplicate project slugs, missing project roots, and stale registry entries.

Exit criteria:

- Project selection logic is implemented once and reused everywhere.

### Phase 3: Make Routing Workspace-Aware

- [ ] Add repository-root inference so requests can resolve the active project from the current workspace without manual `--project` input.
- [ ] Support request metadata routing for agent sessions that provide cwd or repository identifiers.
- [ ] Keep explicit project selection as an override, not the default workflow.
- [ ] Standardize memory URL behavior so project-prefixed permalinks are canonical and unambiguous.
- [ ] Define discovery-mode behavior explicitly for cross-project tools such as search, recent activity, and project listing.

Exit criteria:

- The common path for an agent in a repository is "start using MemoryHub" rather than "configure a project flag for every call".

### Phase 4: Simplify Entry Points Around Local ASGI

- [ ] Remove the remaining "force local" routing abstraction once all callers use the local path by default.
- [ ] Collapse CLI routing helpers into a simpler local execution model.
- [ ] Remove transport-era environment toggles whose only job is to force the already-required local path.
- [ ] Keep composition roots explicit, but reduce duplicate startup logic across API, MCP, and CLI.
- [ ] Ensure MCP client helpers clearly separate project-scoped and non-project-scoped usage around the routing context model.

Exit criteria:

- Entry points read as local composition roots, not as leftovers from a multi-transport transition.

### Phase 5: Finish The SQLite-Only Migration

- [ ] Remove dead backend branching from config, repository code, migrations, services, and tests.
- [ ] Delete or archive migrations whose only purpose is Postgres behavior.
- [ ] Strip Postgres-specific comments, constants, and test fixtures that no longer inform supported behavior.
- [ ] Replace backend-agnostic abstractions that only have one valid implementation with SQLite-focused interfaces.
- [ ] Re-check initialization, backup, recovery, WAL, and semantic-search behavior as first-class SQLite product features.

Exit criteria:

- The active runtime code no longer reads like it expects another database backend to return.

### Phase 6: Normalize Configuration And Naming

- [ ] Introduce a documented `MEMORYHUB_*` config surface for supported settings.
- [ ] Keep `BASIC_MEMORY_*` aliases only as temporary compatibility shims with explicit sunset notes.
- [ ] Remove legacy config keys tied to cloud mode, cloud promos, workspace concepts, and obsolete project metadata.
- [ ] Make the config model fail fast when unsupported historical shapes appear after the migration window.
- [ ] Audit CLI names, docs, JSON payloads, and sample configs so the product consistently presents itself as MemoryHub.

Exit criteria:

- The supported configuration model matches the fork name and product direction.

### Phase 7: Strengthen Multi-Project Isolation And Concurrency

- [ ] Define per-project locking, sync ownership, and cache invalidation rules for concurrent agents.
- [ ] Ensure file watching and background sync remain derived-state maintainers, never hidden sources of truth.
- [ ] Add stress and integration coverage for simultaneous reads, writes, syncs, and cross-project searches.
- [ ] Make project-scoped temp state, task scheduling, and watcher lifecycle explicit.
- [ ] Review note mutation flows for race conditions between filesystem writes and database refresh.

Exit criteria:

- Multiple agents can use different projects concurrently without leaking context or corrupting derived state.

### Phase 8: Refocus The MCP Surface On Agent-Neutral Workflows

- [ ] Audit prompts, resources, and tool text for product-specific assumptions that do not generalize across agents.
- [ ] Keep the MCP tool surface thin and push routing/business logic into services and registry code.
- [ ] Define which tools are project-scoped, multi-project, or routing-aware by design.
- [ ] Standardize tool responses so project context is explicit and consistent when it matters.
- [ ] Review importer and prompt naming so they describe data sources and workflows, not upstream brand history.

Exit criteria:

- The MCP layer looks like a reusable workspace memory hub, not a fork with renamed commands.

### Phase 9: Clean Up Legacy Importers And Historical Surface Area

- [ ] Decide which importers remain part of the fork's active product surface and which should move behind clearly labeled compatibility paths.
- [ ] Remove code paths that only exist to preserve historical cloud or vendor-specific workflows.
- [ ] Archive obsolete release notes, bakeoff docs, and transitional specs that no longer guide active development.
- [ ] Keep upstream attribution, but reduce user-facing references that distract from the current fork behavior.

Exit criteria:

- The repository surface area matches the product MemoryHub is actively trying to become.

### Phase 10: Rebuild The Test And Docs Story Around The Fork

- [ ] Rewrite tests that still frame unsupported cloud/Postgres behavior as normal compatibility coverage.
- [ ] Add focused unit and integration tests for registry-based routing, cwd inference, memory URL routing, and concurrent multi-project usage.
- [ ] Keep doctor/smoke coverage aligned with the local-only product path.
- [ ] Maintain one architecture doc, one operator guide, and one contributor guide that all describe the same system.
- [ ] Track migration removals in changelog-style notes so downstream users can follow breaking cleanup work.

Exit criteria:

- Tests and docs protect the current fork direction instead of anchoring the old one.

## Cross-Cutting Workstreams

These should progress alongside the main phases rather than waiting until the end:

- [ ] Keep deleting compatibility code only when a replacement path and test coverage already exist.
- [ ] Prefer moving behavior behind explicit service boundaries before removing old adapters.
- [ ] Measure startup time, sync throughput, and search latency after each major routing or registry change.
- [ ] Keep migrations narrow and reversible until the Postgres/cloud cleanup window is closed.
- [ ] Treat every remaining global env read outside composition roots as migration debt to retire.

## Non-Goals

This roadmap does not aim to:

- reintroduce hosted cloud routing
- preserve Postgres parity
- turn background sync into a second source of truth
- specialize the product around a single agent vendor

## Recommended Execution Order

If this roadmap is turned into active implementation work, the highest-leverage sequence is:

1. Phase 1: lock the supported surface
2. Phase 2: add the project registry layer
3. Phase 3: make routing workspace-aware
4. Phase 4: simplify entrypoints
5. Phase 5 and Phase 6: remove backend and naming baggage
6. Phase 7 through Phase 10: harden concurrency, MCP ergonomics, and the test/docs story

That order minimizes rework: once project resolution is centralized, the remaining cleanup becomes much easier and much safer.
