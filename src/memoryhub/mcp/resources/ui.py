"""UI resources for MCP Apps integration."""

from memoryhub.mcp.server import mcp
from memoryhub.mcp.ui import load_html, load_variant_html

# FastMCP's MIME type validator currently accepts only type/subtype, so we
# use text/html here. MCP Apps hosts typically expect text/html;profile=mcp-app.
MIME_TYPE = "text/html"


@mcp.resource(
    uri="ui://memoryhub/search-results",
    name="MemoryHub Search Results",
    description="Search results UI for MemoryHub tools.",
    mime_type=MIME_TYPE,
)
def search_results_ui() -> str:
    return load_variant_html("search-results")


@mcp.resource(
    uri="ui://memoryhub/note-preview",
    name="MemoryHub Note Preview",
    description="Note preview UI for the MemoryHub read_note tool.",
    mime_type=MIME_TYPE,
)
def note_preview_ui() -> str:
    return load_variant_html("note-preview")


# Variant-specific resource URIs for bakeoff comparisons.
@mcp.resource(
    uri="ui://memoryhub/search-results/vanilla",
    name="MemoryHub Search Results (Vanilla)",
    description="Vanilla HTML search results UI.",
    mime_type=MIME_TYPE,
)
def search_results_ui_vanilla() -> str:
    return load_html("search-results-vanilla.html")


@mcp.resource(
    uri="ui://memoryhub/search-results/tool-ui",
    name="MemoryHub Search Results (Tool UI)",
    description="Tool UI styled search results UI.",
    mime_type=MIME_TYPE,
)
def search_results_ui_tool_ui() -> str:
    return load_html("search-results-tool-ui.html")


@mcp.resource(
    uri="ui://memoryhub/search-results/mcp-ui",
    name="MemoryHub Search Results (MCP UI)",
    description="MCP UI styled search results UI.",
    mime_type=MIME_TYPE,
)
def search_results_ui_mcp_ui() -> str:
    return load_html("search-results-mcp-ui.html")


@mcp.resource(
    uri="ui://memoryhub/note-preview/vanilla",
    name="MemoryHub Note Preview (Vanilla)",
    description="Vanilla HTML note preview UI.",
    mime_type=MIME_TYPE,
)
def note_preview_ui_vanilla() -> str:
    return load_html("note-preview-vanilla.html")


@mcp.resource(
    uri="ui://memoryhub/note-preview/tool-ui",
    name="MemoryHub Note Preview (Tool UI)",
    description="Tool UI styled note preview UI.",
    mime_type=MIME_TYPE,
)
def note_preview_ui_tool_ui() -> str:
    return load_html("note-preview-tool-ui.html")


@mcp.resource(
    uri="ui://memoryhub/note-preview/mcp-ui",
    name="MemoryHub Note Preview (MCP UI)",
    description="MCP UI styled note preview UI.",
    mime_type=MIME_TYPE,
)
def note_preview_ui_mcp_ui() -> str:
    return load_html("note-preview-mcp-ui.html")
