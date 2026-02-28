# MemoryHub

MemoryHub is a multi-project, multi-agent MCP memory server built on top of Basic Memory.

It provides a single MCP endpoint that dynamically routes requests to the correct memory project based on workspace context, repository detection, or explicit metadata.

MemoryHub is designed for modern AI-native workflows where multiple agents operate across multiple codebases — without requiring per-project MCP configuration.

---

## Overview

Basic Memory introduced a powerful local-first knowledge graph built from structured Markdown files and exposed through MCP. However, the default architecture assumes a single active project per MCP server instance.

MemoryHub extends that model by introducing a routing layer that enables:

- One MCP server
- Multiple independent memory projects
- Context-aware request dispatching
- Concurrent multi-agent access
- Lazy project initialization

From the agent’s perspective, there is only one memory server.
Internally, MemoryHub multiplexes across multiple project-specific memory contexts.

---

## Design Goals

MemoryHub is built around the following principles:

### 1. Single Endpoint Simplicity

Agents should connect to one MCP server — not one per project.

### 2. Project Isolation

Each repository or workspace maintains its own memory graph.
No cross-project leakage unless explicitly configured.

### 3. Context-Aware Routing

MemoryHub determines the correct project by:

- Detecting a memory store in the current repository
- Inspecting metadata (e.g., `project_id`)
- Falling back to a configured default project

### 4. Multi-Agent Safety

Multiple agents can operate simultaneously across different projects without interfering with each other.

### 5. Local-First Architecture

All knowledge remains Markdown-based and file-backed.
MemoryHub does not change the underlying knowledge model.

---

## How It Works

MemoryHub runs a single MCP JSON-RPC server.

For each incoming request:

1. Extract routing metadata (e.g., `project_id`, `cwd`, repo marker)
2. Resolve the appropriate project root
3. Load or retrieve the cached memory context
4. Dispatch the request to that context
5. Return the response transparently

This creates a logical structure like:

```
Agents
   │
   ▼
MemoryHub MCP Server
   │
   ├── Project: repo-a
   ├── Project: repo-b
   └── Project: research-notes
```

Projects are loaded on demand and cached for performance.

---

## Routing Strategies

MemoryHub supports multiple routing modes.

### Workspace Auto-Detection

If a repository contains a memory store (e.g., `.basicmemory/` or configured project path), requests originating from that workspace are routed automatically.

### Explicit Metadata Routing

Agents may include routing metadata in requests:

```json
{
    "metadata": {
        "project_id": "repo-a"
    }
}
```

MemoryHub resolves the matching memory project.

### Default Project Fallback

If no routing hint is found, MemoryHub can:

- Route to a global default project
- Or reject the request in strict mode

---

## Use Cases

### Multi-Agent Development Systems

- Planner agent → project A
- Refactor agent → project B
- Reviewer agent → project A

All share a single MCP endpoint.

### Monorepos

Each subdirectory maintains its own memory store.
MemoryHub routes automatically based on workspace detection.

### AI Toolchains

Ephemeral agents spawned by automation pipelines can connect to a unified memory service without project-specific configuration.

---

## Installation (Development)

```bash
uv tool install -e .
```

Run the MCP server:

```bash
memoryhub mcp
```

Or:

```bash
uvx memoryhub mcp
```

---

## Agent Configuration

Configure a single MCP server entry.

Example (Claude Desktop):

```json
{
    "mcpServers": {
        "memoryhub": {
            "command": "uvx",
            "args": ["memoryhub", "mcp"]
        }
    }
}
```

No per-project `--project` argument required.

---

## Comparison with Basic Memory

| Capability                | Basic Memory | MemoryHub |
| ------------------------- | ------------ | --------- |
| Single MCP endpoint       | ✔            | ✔         |
| One project per server    | ✔            | ✘         |
| Dynamic project selection | ✘            | ✔         |
| Multi-agent concurrency   | Limited      | ✔         |
| Workspace-aware routing   | ✘            | ✔         |

MemoryHub builds on Basic Memory’s knowledge model and storage system.
It extends server behavior — not the data format.

---

## Technical Foundation

MemoryHub inherits:

- Markdown-based entity storage
- SQLite / Postgres indexing
- Knowledge graph traversal
- MCP tool exposure

It introduces:

- Context resolver
- Project registry
- Routing dispatcher
- Memory context cache

The file format, graph semantics, and tool APIs remain unchanged.

---

## Roadmap

Planned enhancements:

- Configurable routing plugins
- Namespaced tool exposure per project
- Access control policies
- Project discovery via Git integration
- Observability and metrics

---

## License

AGPL-3.0

MemoryHub inherits licensing terms from Basic Memory.

If operated as a network service, source code must be made available under AGPL.

---

## Status

Early-stage experimental fork.

MemoryHub is intended for advanced multi-agent and multi-repository workflows.

Contributions and architectural discussions are welcome.
