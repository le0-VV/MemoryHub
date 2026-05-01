# agent-basics Integration Handoff

This note is for agents working in `/Users/leonardw/Projects/MemoryHub` while another agent or sandbox may be working in `/Users/leonardw/Projects/agent-basics`.

## Current Direction

- `agent-basics` treats MemoryHub as a mandatory central dependency.
- MemoryHub is the machine-local, OpenViking-aligned central runtime for this integration.
- There should be one MemoryHub installation/runtime/embedding/index stack per machine, not one OpenViking install per repo.
- That central installation lives under `$MEMORYHUB_CONFIG_DIR` by default and owns binaries, the Python environment, config, SQLite state, caches, embedding models, logs, runtime state, and uncategorized/global memory.
- `agent-basics` keeps each project memory source in that project under `.agents/memoryhub/`.
- The central hub should reference repo-local memory through `$MEMORYHUB_CONFIG_DIR/projects/<project-name>` symlinks.
- `setup-macos.sh` in agent-basics uses `MEMORYHUB_SOURCE_DIR` to find this checkout for editable installs.

## Expected Local Layout

```text
/Users/leonardw/Projects/
├── agent-basics/
└── MemoryHub/
```

Useful environment:

```bash
export AGENT_BASICS_ROOT="/Users/leonardw/Projects/agent-basics"
export MEMORYHUB_SOURCE_DIR="/Users/leonardw/Projects/MemoryHub"
export MEMORYHUB_CONFIG_DIR="${MEMORYHUB_CONFIG_DIR:-$HOME/.memoryhub}"
export PATH="$MEMORYHUB_CONFIG_DIR/bin:$MEMORYHUB_CONFIG_DIR/venv/bin:$PATH"
```

## Ownership Boundary

MemoryHub owns:

- central runtime installation behavior
- project registry and cwd/repository resolution
- markdown sync/indexing behavior
- MCP/API/CLI semantics
- tests for config, routing, sync, and multi-agent safety

agent-basics owns:

- bootstrap UX and `setup-macos.sh`
- generated `Agents.md` and `.agents/INSTRUCTIONS.md` templates
- repo-local `.agents/memoryhub/` layout
- migration UI for agent instruction markdown
- Homebrew packaging for the bootstrapper

## Cross-Repo Coordination

- Check git status in both repos before edits.
- Do not overwrite dirty files from the other repo or another agent.
- Commit each repository separately.
- If you need to leave a message for the other sandbox, write a timestamped markdown file in `.agents/agent-mailbox/outbox/` and mention the target repo in the title.
- If you consume a message, copy or move it to `.agents/agent-mailbox/archive/` only when the owner of that repo has approved that convention.

## Recent agent-basics Commits To Know

- `cd6d0bb feat(memoryhub): centralize agent memory setup`
- `81a7f98 docs(workspaces): document memoryhub coordination`

## Verified Progress As Of 2026-04-30

The current MemoryHub checkout is usable for the agent-basics central-hub flow.

Verified with isolated temporary hub state:

- `memoryhub --version` returned `0.18.5`.
- `memoryhub project list --json` worked with an empty temporary `$MEMORYHUB_CONFIG_DIR`.
- `memoryhub project add smoke <project-source>` registered a repo-local markdown source directory.
- `memoryhub doctor` passed end-to-end file, database, sync, and search checks.
- A symlinked project path at `$MEMORYHUB_CONFIG_DIR/projects/agent-basics-smoke` pointing to a repo-local `.agents/memoryhub/` source was accepted and listable.
- `agent-basics/setup-macos.sh` passed a full smoke run using the real MemoryHub executable from this checkout and isolated temp hub state.

Recent MemoryHub commits relevant to this integration:

- `9055612e refactor(config): move implicit default project root under app state`
- `4ecb5309 docs(agent): add agent-basics coordination mailbox`
- `1104ef0c fix(runtime): support central hub state roots`

## Requirements For Future Work

MemoryHub must keep the agent-basics central-hub contract stable:

- `MEMORYHUB_CONFIG_DIR` owns central config, SQLite state, logs, ignore state, runtime state, `bin`, `venv`, caches, local embedding models, and the implicit `projects/main` uncategorized/global memory root unless explicitly overridden.
- `MEMORYHUB_SOURCE_DIR` points agent-basics setup at this checkout for editable installs.
- Project content can live outside the central hub and be referenced through `$MEMORYHUB_CONFIG_DIR/projects/<project-name>` symlinks.
- Repo-local project memory source should remain plain markdown under `.agents/memoryhub/`.
- `memoryhub project add`, `memoryhub project list --json`, and `memoryhub doctor` should remain stable enough for setup automation.
- Project registry and cwd/repository resolution should remain deterministic when projects are symlinked into the hub.
- Sync/indexing must treat markdown files as source of truth and must not create hidden project-local runtime state inside downstream repos unless explicitly documented.
- Concurrency hardening remains important: multiple agents may read, write, sync, and search different projects through the same hub at the same time.
- The `.agents/agent-mailbox/` convention is a temporary cross-sandbox channel, not a product source of truth. Durable decisions belong in docs, tests, or MemoryHub notes.

Suggested next tests:

- A unit or integration test for project registration through symlinked project paths.
- A CLI contract test for `project list --json` used by setup automation.
- A smoke test that creates a repo-style `.agents/memoryhub/` tree and verifies list/read/sync behavior through the central hub symlink.
- Concurrent-agent tests that exercise two configured projects under one `$MEMORYHUB_CONFIG_DIR`.
