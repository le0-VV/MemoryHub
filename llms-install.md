# MemoryHub Installation Guide for LLMs

This guide is for the MemoryHub fork in this repository.

Important: the fork has not been fully renamed yet. The code still runs through
the inherited `basic-memory` CLI, so install from the local checkout rather
than from PyPI.

## Installation Steps

### 1. Install This Fork

From the repository root:

```bash
# Recommended
uv tool install -e .

# Or editable pip install
pip install -e .
```

Do not use `uv tool install basic-memory` or `pip install basic-memory` if you
want this fork. Those commands install the upstream project from PyPI.

### 2. Configure The MCP Server

Use the inherited runtime command until the rename is complete:

```json
{
  "mcpServers": {
    "memoryhub": {
      "command": "basic-memory",
      "args": ["mcp"]
    }
  }
}
```

For Claude Desktop, this file is usually located at:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\\Claude\\claude_desktop_config.json`

### 3. Start Synchronization (optional)

```bash
basic-memory sync --watch
```

For a one-time sync:

```bash
basic-memory sync
```

## Configuration Options

### Custom Directory

```bash
basic-memory project add custom-project /path/to/your/directory
basic-memory project default custom-project
```

### Multiple Projects

```bash
basic-memory project list
basic-memory project add work ~/work-basic-memory
basic-memory project default work
```

## Importing Existing Data

### From Claude.ai

```bash
basic-memory import claude conversations path/to/conversations.json
basic-memory import claude projects path/to/projects.json
```

### From ChatGPT

```bash
basic-memory import chatgpt path/to/conversations.json
```

### From MCP Memory Server

```bash
basic-memory import memory-json path/to/memory.json
```

## Troubleshooting

1. Check the installed executable:
   ```bash
   basic-memory --version
   ```
2. Verify the process is running:
   ```bash
   ps aux | grep basic-memory
   ```
3. Check sync output:
   ```bash
   basic-memory sync --verbose
   ```
4. Check logs:
   ```bash
   cat ~/.basic-memory/basic-memory.log
   ```

See [README.md](README.md) for the fork status and [README_old.md](README_old.md)
for the preserved upstream product documentation.
