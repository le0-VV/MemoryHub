# MemoryHub

MemoryHub is an experimental fork of Basic Memory focused on multi-project,
multi-agent MCP workflows.

Today this repository is still mostly the upstream Basic Memory codebase with
fork-specific documentation, attribution, and direction. The fork vision is to
turn the existing note graph and MCP stack into a routing hub for multiple
repositories and agent sessions, but that work is not complete yet.

## Current State

What already exists in this repository today:

- The upstream Basic Memory architecture: API, MCP server, CLI, sync, search,
  Markdown-backed notes, and knowledge graph traversal.
- SQLite-backed local deployment.
- Multi-project configuration and project management.
- Default or explicit project selection for tool calls.
- Per-project local or cloud routing once a project is known.

What has not been implemented yet:

- Automatic routing by repository root, current working directory, or generic
  request metadata.
- A dedicated MemoryHub routing layer or project registry/cache.
- A maintained Postgres backend. This fork is standardizing on SQLite only.

## Fork Goal

The long-term goal is still the same as the fork vision:

- One MCP endpoint for many projects.
- Strong project isolation between repositories.
- Context-aware routing without per-project MCP configuration.
- Safe concurrent use by multiple agents.
- No change to the underlying Markdown-based knowledge model.

In short: keep Basic Memory's file format and graph semantics, but evolve the
server into a workspace-aware memory hub.

## Running The Fork Today

Install this fork from the local checkout:

```bash
uv tool install -e .
memoryhub mcp
```

You can also run it directly from the repository:

```bash
uv run memoryhub mcp
```

## MCP Configuration

Your MCP config can invoke the renamed CLI directly:

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

If you want to ensure you are using this fork rather than the upstream PyPI
package, prefer a local editable install and reference the installed
`memoryhub` executable directly.

## Documentation Map

- [README.md](README.md): current fork status and direction
- [README_old.md](README_old.md): preserved upstream README for reference
- [CONTRIBUTING.md](CONTRIBUTING.md): contributor guidance for this fork
- [AGENTS.md](AGENTS.md): repo-specific instructions for coding agents
- [NOTICE](NOTICE): fork attribution and licensing notice

## Automation Status

Repository automation is intentionally conservative during the fork transition:

- Dependabot configuration is retained.
- GitHub Actions workflows and issue templates are currently removed.
- PyPI, Homebrew, and Docker publishing are not configured in this fork right
  now.

## Attribution And License

MemoryHub is derived from Basic Memory:

- Upstream repository:
  [basicmachines-co/basic-memory](https://github.com/basicmachines-co/basic-memory)
- License: AGPL-3.0-or-later
- Upstream copyright notices remain with their original authors
- Additional modifications in this fork are copyright their respective
  contributors

If this modified software is run as a network service, AGPL obligations still
apply, including providing the corresponding source for the modified version.

## Status

Early-stage fork. The documentation now reflects the current reality more
accurately than the implementation roadmap.

The next major phase is architectural: introduce real project routing on top of
the renamed local-only MemoryHub baseline.
