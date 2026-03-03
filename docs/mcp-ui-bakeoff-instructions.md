# MCP UI Bakeoff - Instructions & Test Plan

Last updated: 2026-02-02

> Historical/internal note: this is an experimental MCP UI comparison document for the fork. It is
> not a product guarantee or a supported distribution guide.

## Scope

Compare three presentation paths for MemoryHub MCP tools:

1. **Tool‑UI (React)** via MCP App resources.
2. **MCP‑UI Python SDK** embedded UI resources (legacy host path).
3. **ASCII/ANSI** output for TUI clients.

This doc is the running instruction set and test plan. Update as implementation progresses.

---

## Prerequisites

- Repo: `MemoryHub`
- Node for tool‑ui build (already used for POC)
- Python 3.12+ with `uv`

Optional (for MCP‑UI Python SDK path):

- Local repo: `/Users/phernandez/dev/mcp-ui`
- Install the server SDK into the project venv:
  - `uv pip install -e /Users/phernandez/dev/mcp-ui/sdks/python/server`

---

## Build / Refresh Steps

### Tool‑UI React bundle

```bash
cd ui/tool-ui-react
npm install
npm run build
```

This regenerates:

- `src/memoryhub/mcp/ui/html/search-results-tool-ui.html`
- `src/memoryhub/mcp/ui/html/note-preview-tool-ui.html`

---

## How to Run the MCP Server

```bash
memoryhub mcp --transport stdio
```

Optional to pick UI variant for MCP App resources:

```bash
export MEMORYHUB_MCP_UI_VARIANT=tool-ui   # or vanilla | mcp-ui
```

---

## Test Cases

### 1) MCP App Resource UI (tool‑ui / vanilla / mcp‑ui)

Tools:
- `search_notes`
- `read_note`

Expect:
- Tool meta points to `ui://memoryhub/search-results` and `ui://memoryhub/note-preview`
- Resource content differs by `MEMORYHUB_MCP_UI_VARIANT` (legacy `BASIC_MEMORY_MCP_UI_VARIANT` still works during compatibility)
- Variant‑specific URIs also available:
  - `ui://memoryhub/search-results/vanilla`
  - `ui://memoryhub/search-results/tool-ui`
  - `ui://memoryhub/search-results/mcp-ui`
  - `ui://memoryhub/note-preview/vanilla`
  - `ui://memoryhub/note-preview/tool-ui`
  - `ui://memoryhub/note-preview/mcp-ui`

Manual check:
- Trigger tool in MCP‑App‑capable host and confirm UI renders.

---

### 2) Text / JSON Output Modes

Tools:
- `search_notes(output_format="text" | "json")`
- `read_note(output_format="text" | "json")`
- `write_note(output_format="text" | "json")`
- `edit_note(output_format="text" | "json")`
- `recent_activity(output_format="text" | "json")`
- `list_memory_projects(output_format="text" | "json")`
- `create_memory_project(output_format="text" | "json")`
- `delete_note(output_format="text" | "json")`
- `move_note(output_format="text" | "json")`
- `build_context(output_format="json" | "text")`

Expect:
- `text` mode preserves existing human-readable responses.
- `json` mode returns structured dict/list payloads for machine-readable clients.

Automated:
- `uv run pytest test-int/mcp/test_output_format_json_integration.py`

---

### 3) MCP‑UI Python SDK (embedded UI resource)

Tools (embedded resource responses):
- `search_notes_ui` (MCP‑UI SDK)
- `read_note_ui` (MCP‑UI SDK)

Expected output:
- Tool response content contains an EmbeddedResource (`type: "resource"`)
- `mimeType` is `text/html`
- `_meta` includes:
  - `mcpui.dev/ui-preferred-frame-size`
  - `mcpui.dev/ui-initial-render-data`

Manual check:
- Render tool responses using `UIResourceRenderer` (legacy host flow).

Automated (if SDK installed):
- `uv run pytest test-int/mcp/test_ui_sdk_integration.py`

---

## Bakeoff Notes Template

Fill in after running:

- Tool‑UI (React): __
- MCP‑UI SDK (embedded): __
- Text/JSON modes: __

Decision + rationale: __
