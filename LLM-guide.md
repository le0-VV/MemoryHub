# MemoryHub Installation Guide for LLMs

This guide is for the MemoryHub fork in this repository.

Important: the fork has not been fully renamed yet. The code still runs through the inherited `memoryhub` CLI, so install from the local checkout rather than from PyPI.

## Installation Steps

### 1. Install This Fork

From the repository root:

```bash
# Recommended
uv tool install -e .

# Or editable pip install
pip install -e .
```

Do not use `uv tool install memoryhub` or `pip install memoryhub` if you want this fork. Those commands install the upstream project from PyPI.

### 2. Configure The MCP Server

Use the inherited runtime command until the rename is complete:

```json
{
  "mcpServers": {
    "memoryhub": {
      "command": "memoryhub",
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
memoryhub sync --watch
```

For a one-time sync:

```bash
memoryhub sync
```

## Configuration Options

### Custom Directory

```bash
memoryhub project add custom-project /path/to/your/directory
memoryhub project default custom-project
```

### Multiple Projects

```bash
memoryhub project list
memoryhub project add work ~/work-memoryhub
memoryhub project default work
```

## Importing Existing Data

### From Claude.ai

```bash
memoryhub import claude conversations path/to/conversations.json
memoryhub import claude projects path/to/projects.json
```

### From ChatGPT

```bash
memoryhub import chatgpt path/to/conversations.json
```

### From MCP Memory Server

```bash
memoryhub import memory-json path/to/memory.json
```

## Troubleshooting

1. Check the installed executable:
   ```bash
   memoryhub --version
   ```
2. Verify the process is running:
   ```bash
   ps aux | grep memoryhub
   ```
3. Check sync output:
   ```bash
   memoryhub sync --verbose
   ```
4. Check logs:
   ```bash
   cat ~/.memoryhub/memoryhub.log
   ```

See [README.md](README.md) for the fork status and [README_old.md](README_old.md) for the preserved upstream product documentation.
