"""Search tools for MemoryHub MCP."""

from textwrap import dedent
from typing import List, Optional, Dict, Any, Literal

from loguru import logger
from fastmcp import Context

from memoryhub.config import ConfigManager
from memoryhub.mcp.container import get_container
from memoryhub.mcp.project_context import (
    detect_project_from_url_prefix,
    get_project_client,
    resolve_project_and_path,
)
from memoryhub.mcp.server import mcp
from memoryhub.schemas.search import (
    SearchItemType,
    SearchQuery,
    SearchResponse,
    SearchRetrievalMode,
)


def _semantic_search_enabled_for_text_search() -> bool:
    """Resolve semantic-search enablement in both MCP and CLI invocation paths."""
    try:
        return get_container().config.semantic_search_enabled
    except RuntimeError:
        # Trigger: MCP container is not initialized (e.g., `memoryhub tool search-notes` direct call).
        # Why: CLI path still needs the same semantic-default behavior as MCP server path.
        # Outcome: load config directly and keep text-mode retrieval behavior consistent.
        return ConfigManager().config.semantic_search_enabled


def _default_search_type() -> str:
    """Pick default search mode from semantic-search config."""
    return "hybrid" if _semantic_search_enabled_for_text_search() else "text"


def _format_search_error_response(
    project: str, error_message: str, query: str, search_type: str = "text"
) -> str:
    """Format helpful error responses for search failures that guide users to successful searches."""

    # Semantic config/dependency errors
    if "semantic search is disabled" in error_message.lower():
        return dedent(f"""
            # Search Failed - Semantic Search Disabled

            You requested `{search_type}` search for query '{query}', but semantic search is disabled.

            ## How to enable
            1. Set `MEMORYHUB_SEMANTIC_SEARCH_ENABLED=true`
            2. Restart the MemoryHub server/process

            ## Alternative now
            - Run FTS search instead:
              `search_notes("{query}", project="{project}", search_type="text")`
            """).strip()

    if "pip install" in error_message.lower() and "semantic" in error_message.lower():
        return dedent(f"""
            # Search Failed - Semantic Dependencies Missing

            Semantic retrieval is enabled but required packages are not installed.

            ## Fix
            1. Install/update MemoryHub: `pip install -U memoryhub`
            2. Restart MemoryHub
            3. Retry your query:
               `search_notes("{query}", project="{project}", search_type="{search_type}")`
            """).strip()

    # FTS5 syntax errors
    if "syntax error" in error_message.lower() or "fts5" in error_message.lower():
        clean_query = (
            query.replace('"', "")
            .replace("(", "")
            .replace(")", "")
            .replace("+", "")
            .replace("*", "")
        )
        return dedent(f"""
            # Search Failed - Invalid Syntax

            The search query '{query}' contains invalid syntax that the search engine cannot process.

            ## Common syntax issues:
            1. **Special characters**: Characters like `+`, `*`, `"`, `(`, `)` have special meaning in search
            2. **Unmatched quotes**: Make sure quotes are properly paired
            3. **Invalid operators**: Check AND, OR, NOT operators are used correctly

            ## How to fix:
            1. **Simplify your search**: Try using simple words instead: `{clean_query}`
            2. **Remove special characters**: Use alphanumeric characters and spaces
            3. **Use basic boolean operators**: `word1 AND word2`, `word1 OR word2`, `word1 NOT word2`

            ## Examples of valid searches:
            - Simple text: `project planning`
            - Boolean AND: `project AND planning`
            - Boolean OR: `meeting OR discussion`
            - Boolean NOT: `project NOT archived`
            - Grouped: `(project OR planning) AND notes`
            - Exact phrases: `"weekly standup meeting"`
            - Content-specific: `tag:example` or `category:observation`

            ## Try again with:
            ```python
            search_notes("{clean_query}", project="{project}")
            ```

            ## Alternative search strategies:
            - Break into simpler terms: `search_notes("{" ".join(clean_query.split()[:2])}", project="{project}")`
            - Try different search types: `search_notes("{clean_query}", project="{project}", search_type="title")`
            - Use filtering: `search_notes("{clean_query}", project="{project}", note_types=["note"])`
            """).strip()

    # Project not found errors (check before general "not found")
    if "project not found" in error_message.lower():
        return dedent(f"""
            # Search Failed - Project Not Found

            The current project is not accessible or doesn't exist: {error_message}

            ## How to resolve:
            1. **Check available projects**: `list_memory_projects()`
            3. **Verify project setup**: Ensure your project is properly configured

            ## Current session info:
            - See available projects: `list_memory_projects()`
            """).strip()

    # No results found
    if "no results" in error_message.lower() or "not found" in error_message.lower():
        simplified_query = (
            " ".join(query.split()[:2])
            if len(query.split()) > 2
            else query.split()[0]
            if query.split()
            else "notes"
        )
        return dedent(f"""
            # Search Complete - No Results Found

            No content found matching '{query}' in the current project.

            ## Search strategy suggestions:
            1. **Broaden your search**: Try fewer or more general terms
               - Instead of: `{query}`
               - Try: `{simplified_query}`

            2. **Check spelling and try variations**:
               - Verify terms are spelled correctly
               - Try synonyms or related terms

            3. **Use different search approaches**:
               - **Text search**: `search_notes("{query}", project="{project}", search_type="text")` (searches full content)
               - **Title search**: `search_notes("{query}", project="{project}", search_type="title")` (searches only titles)
               - **Permalink search**: `search_notes("{query}", project="{project}", search_type="permalink")` (searches file paths)

            4. **Try boolean operators for broader results**:
               - OR search: `search_notes("{" OR ".join(query.split()[:3])}", project="{project}")`
               - Remove restrictive terms: Focus on the most important keywords

            5. **Use filtering to narrow scope**:
               - By content type: `search_notes("{query}", project="{project}", note_types=["note"])`
               - By recent content: `search_notes("{query}", project="{project}", after_date="1 week")`
               - By entity type: `search_notes("{query}", project="{project}", entity_types=["observation"])`

            6. **Try advanced search patterns**:
               - Tag search: `search_notes("tag:your-tag", project="{project}")`
               - Category search: `search_notes("category:observation", project="{project}")`
               - Pattern matching: `search_notes("*{query}*", project="{project}", search_type="permalink")`

            ## Explore what content exists:
            - **Recent activity**: `recent_activity(timeframe="7d")` - See what's been updated recently
            - **List directories**: `list_directory("/", project="{project}")` - Browse all content
            - **Browse by folder**: `list_directory("/notes", project="{project}")` or `list_directory("/docs")`
            """).strip()

    # Server/API errors
    if "server error" in error_message.lower() or "internal" in error_message.lower():
        return dedent(f"""
            # Search Failed - Server Error

            The search service encountered an error while processing '{query}': {error_message}

            ## Immediate steps:
            1. **Try again**: The error might be temporary
            2. **Simplify the query**: Use simpler search terms
            3. **Check project status**: Ensure your project is properly synced

            ## Alternative approaches:
            - Browse files directly: `list_directory("/", project="{project}")`
            - Check recent activity: `recent_activity(timeframe="7d")`
            - Try a different search type: `search_notes("{query}", project="{project}", search_type="title")`

            ## If the problem persists:
            The search index might need to be rebuilt. Run `memoryhub doctor` or check the local project sync status.
            """).strip()

    # Permission/access errors
    if (
        "permission" in error_message.lower()
        or "access" in error_message.lower()
        or "forbidden" in error_message.lower()
    ):
        return f"""# Search Failed - Access Error

You don't have permission to search in the current project: {error_message}

## How to resolve:
1. **Check your project access**: Verify you have read permissions for this project
2. **Switch projects**: Try searching in a different project you have access to
3. **Check authentication**: You might need to re-authenticate

## Alternative actions:
- List available projects: `list_memory_projects()`"""

    # Generic fallback
    return f"""# Search Failed

Error searching for '{query}': {error_message}

## Troubleshooting steps:
1. **Simplify your query**: Try basic words without special characters
2. **Check search syntax**: Ensure boolean operators are correctly formatted
3. **Verify project access**: Make sure you can access the current project
4. **Test with simple search**: Try `search_notes("test")` to verify search is working

## Alternative search approaches:
- **Different search types**: 
  - Title only: `search_notes("{query}", project="{project}", search_type="title")`
  - Permalink patterns: `search_notes("{query}*", project="{project}", search_type="permalink")`
- **With filters**: `search_notes("{query}", project="{project}", note_types=["note"])`
- **Recent content**: `search_notes("{query}", project="{project}", after_date="1 week")`
- **Boolean variations**: `search_notes("{" OR ".join(query.split()[:2])}", project="{project}")`

## Explore your content:
- **Browse files**: `list_directory("/", project="{project}")` - See all available content
- **Recent activity**: `recent_activity(timeframe="7d")` - Check what's been updated
- **All projects**: `list_memory_projects()` 

## Search syntax reference:
- **Basic**: `keyword` or `multiple words`
- **Boolean**: `term1 AND term2`, `term1 OR term2`, `term1 NOT term2`
- **Phrases**: `"exact phrase"`
- **Grouping**: `(term1 OR term2) AND term3`
- **Patterns**: `tag:example`, `category:observation`"""


@mcp.tool(
    description="Search across all content in the knowledge base with advanced syntax support.",
    # TODO: re-enable once MCP client rendering is working
    # meta={"ui/resourceUri": "ui://memoryhub/search-results"},
    annotations={"readOnlyHint": True, "openWorldHint": False},
)
async def search_notes(
    query: Optional[str] = None,
    project: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    search_type: str | None = None,
    output_format: Literal["text", "json"] = "text",
    note_types: List[str] | None = None,
    entity_types: List[str] | None = None,
    after_date: Optional[str] = None,
    metadata_filters: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    status: Optional[str] = None,
    min_similarity: Optional[float] = None,
    context: Context | None = None,
) -> SearchResponse | dict | str:
    """Search across all content in the knowledge base with comprehensive syntax support.

    This tool searches the knowledge base using full-text search, pattern matching,
    or exact permalink lookup. It supports filtering by content type, entity type,
    and date, with advanced boolean and phrase search capabilities.

    Project Resolution:
    Server resolves projects using the current local-only priority chain:
    constrained project env var -> explicit project parameter -> configured CWD match
    -> configured default project.
    If project is unknown, use list_memory_projects() or recent_activity() first.

    ## Search Syntax Examples

    ### Basic Searches
    - `search_notes("keyword", project="my-project")` - Find any content containing "keyword"
    - `search_notes("'exact phrase'", project="work-docs")` - Search for exact phrase match

    ### Advanced Boolean Searches
    - `search_notes("term1 term2", project="my-project")` - Strict implicit-AND first; retries with
      relaxed OR terms only if strict search returns no results
    - `search_notes("term1 AND term2", project="my-project")` - Explicit AND search (both terms required)
    - `search_notes("term1 OR term2", project="my-project")` - Either term can be present
    - `search_notes("term1 NOT term2", project="my-project")` - Include term1 but exclude term2
    - `search_notes("(project OR planning) AND notes", project="my-project")` - Grouped boolean logic

    ### Content-Specific Searches
    - `search_notes("tag:example", project="research")` - Search within specific tags (if supported by content)
    - `search_notes("category:observation", project="work-project")` - Filter by observation categories
    - `search_notes("author:username", project="team-docs")` - Find content by author (if metadata available)

    **Note:** `tag:` shorthand requires `search_type="text"` when semantic search is enabled
    (the default is hybrid). Alternatively, use the `tags` parameter for tag filtering with
    any search type: `search_notes("query", project="project", tags=["my-tag"])`

    ### Search Type Examples
    - `search_notes("Meeting", project="my-project", search_type="title")` - Search only in titles
    - `search_notes("docs/meeting-*", project="work-docs", search_type="permalink")` - Pattern match permalinks
    - `search_notes("keyword", project="research")` - Default search (hybrid when semantic is enabled,
      text when disabled)

    ### Filtering Options
    - `search_notes("query", project="my-project", note_types=["note"])` - Search only notes
    - `search_notes("query", project="work-docs", note_types=["note", "person"])` - Multiple note types
    - `search_notes("query", project="research", entity_types=["observation"])` - Filter by entity type
    - `search_notes("query", project="team-docs", after_date="2024-01-01")` - Recent content only
    - `search_notes("query", project="my-project", after_date="1 week")` - Relative date filtering
    - `search_notes("query", project="my-project", tags=["security"])` - Filter by frontmatter tags
    - `search_notes("query", project="my-project", status="in-progress")` - Filter by frontmatter status
    - `search_notes("query", project="my-project", metadata_filters={"priority": {"$in": ["high"]}})`

    ### Structured Metadata Filters
    Filters are exact matches on frontmatter metadata. Supported forms:
    - Equality: `{"status": "in-progress"}`
    - Array contains (all): `{"tags": ["security", "oauth"]}`
    - Operators:
      - `$in`: `{"priority": {"$in": ["high", "critical"]}}`
      - `$gt`, `$gte`, `$lt`, `$lte`: `{"schema.confidence": {"$gt": 0.7}}`
      - `$between`: `{"schema.confidence": {"$between": [0.3, 0.6]}}`
    - Nested keys use dot notation (e.g., `"schema.confidence"`).

    ### Filter-only Searches
    Omit `query` (or pass None) when only using structured filters:
    - `search_notes(metadata_filters={"type": "spec"}, project="my-project")`
    - `search_notes(tags=["security"], project="my-project")`
    - `search_notes(status="draft", project="my-project")`

    ### Convenience Filters
    `tags` and `status` are shorthand for metadata_filters. If the same key exists in
    metadata_filters, that value wins.

    ### Advanced Pattern Examples
    - `search_notes("project AND (meeting OR discussion)", project="work-project")` - Complex boolean logic
    - `search_notes("\"exact phrase\" AND keyword", project="research")` - Combine phrase and keyword search
    - `search_notes("bug NOT fixed", project="dev-notes")` - Exclude resolved issues
    - `search_notes("docs/2024-*", project="archive", search_type="permalink")` - Year-based permalink search

    Args:
        query: Optional search query string (supports boolean operators, phrases, patterns).
              Omit or pass None for filter-only searches using metadata_filters, tags, or status.
        project: Project name to search in. Optional - server will resolve using hierarchy.
                If unknown, use list_memory_projects() to discover available projects.
        page: The page number of results to return (default 1)
        page_size: The number of results to return per page (default 10)
        search_type: Type of search to perform, one of:
                    "text", "title", "permalink", "vector", "semantic", "hybrid".
                    Default is dynamic: "hybrid" when semantic search is enabled, otherwise "text".
        output_format: "text" preserves existing structured search response behavior.
            "json" returns a machine-readable dictionary payload.
        note_types: Optional list of note types to search (e.g., ["note", "person"])
        entity_types: Optional list of entity types to filter by (e.g., ["entity", "observation"])
        after_date: Optional date filter for recent content (e.g., "1 week", "2d", "2024-01-01")
        metadata_filters: Optional structured frontmatter filters (e.g., {"status": "in-progress"})
        tags: Optional tag filter (frontmatter tags); shorthand for metadata_filters["tags"]
        status: Optional status filter (frontmatter status); shorthand for metadata_filters["status"]
        min_similarity: Optional float to override the global semantic_min_similarity threshold
                       for this query. E.g., 0.0 to see all vector results, or 0.8 for high precision.
                       Only applies to vector and hybrid search types.
        context: Optional FastMCP context for performance caching.

    Returns:
        SearchResponse with results and pagination info, or helpful error guidance if search fails

    Examples:
        # Basic text search
        results = await search_notes("project planning")
        # Plain multi-term text uses strict matching first, then relaxed OR fallback if needed

        # Boolean AND search (both terms must be present)
        results = await search_notes("project AND planning")

        # Boolean OR search (either term can be present)
        results = await search_notes("project OR meeting")

        # Boolean NOT search (exclude terms)
        results = await search_notes("project NOT meeting")

        # Boolean search with grouping
        results = await search_notes("(project OR planning) AND notes")

        # Exact phrase search
        results = await search_notes("\"weekly standup meeting\"")

        # Search with note type filter
        results = await search_notes(
            "meeting notes",
            note_types=["note"],
        )

        # Search with entity type filter
        results = await search_notes(
            "meeting notes",
            entity_types=["observation"],
        )

        # Search for recent content
        results = await search_notes(
            "bug report",
            after_date="1 week"
        )

        # Pattern matching on permalinks
        results = await search_notes(
            "docs/meeting-*",
            search_type="permalink"
        )

        # Title-only search
        results = await search_notes(
            "Machine Learning",
            search_type="title"
        )

        # Complex search with multiple filters
        results = await search_notes(
            "(bug OR issue) AND NOT resolved",
            note_types=["note"],
            after_date="2024-01-01"
        )

        # Explicit project specification
        results = await search_notes("project planning", project="my-project")
    """
    # Avoid mutable-default-argument footguns. Treat None as "no filter".
    note_types = note_types or []
    entity_types = entity_types or []

    # Detect project from memory URL prefix before routing
    if project is None and query is not None:
        detected = detect_project_from_url_prefix(query, ConfigManager().config)
        if detected:
            project = detected

    async with get_project_client(project, context) as (client, active_project):
        # Handle memory:// URLs by resolving to permalink search
        is_memory_url = False
        if query is not None:
            _, resolved_query, is_memory_url = await resolve_project_and_path(
                client, query, project, context
            )
            if is_memory_url:
                query = resolved_query
        effective_search_type = search_type or _default_search_type()
        if is_memory_url:
            effective_search_type = "permalink"

        try:
            # Create a SearchQuery object based on the parameters
            search_query = SearchQuery()

            # Only map search_type to query fields when there is an actual query string.
            # When query is None/empty, skip the search mode block — filters-only path.
            effective_query = (query or "").strip()
            if effective_query:
                valid_search_types = {
                    "text",
                    "title",
                    "permalink",
                    "vector",
                    "semantic",
                    "hybrid",
                }
                if effective_search_type == "text":
                    search_query.text = effective_query
                    search_query.retrieval_mode = SearchRetrievalMode.FTS
                elif effective_search_type in ("vector", "semantic"):
                    search_query.text = effective_query
                    search_query.retrieval_mode = SearchRetrievalMode.VECTOR
                elif effective_search_type == "hybrid":
                    search_query.text = effective_query
                    search_query.retrieval_mode = SearchRetrievalMode.HYBRID
                elif effective_search_type == "title":
                    search_query.title = effective_query
                elif effective_search_type == "permalink" and "*" in effective_query:
                    search_query.permalink_match = effective_query
                elif effective_search_type == "permalink":
                    search_query.permalink = effective_query
                else:
                    raise ValueError(
                        f"Invalid search_type '{effective_search_type}'. "
                        f"Valid options: {', '.join(sorted(valid_search_types))}"
                    )

            # Add optional filters if provided (empty lists are treated as no filter)
            if entity_types:
                search_query.entity_types = [SearchItemType(t) for t in entity_types]
            if note_types:
                search_query.note_types = note_types
            if after_date:
                search_query.after_date = after_date
            if metadata_filters:
                search_query.metadata_filters = metadata_filters
            if tags:
                search_query.tags = tags
            if status:
                search_query.status = status
            if min_similarity is not None:
                search_query.min_similarity = min_similarity

            # Reject searches with no criteria at all
            if search_query.no_criteria():
                return (
                    "# No Search Criteria\n\n"
                    "Please provide at least one of: `query`, `metadata_filters`, "
                    "`tags`, `status`, `note_types`, `entity_types`, or `after_date`."
                )

            logger.debug(f"Searching for {search_query} in project {active_project.name}")
            # Import here to avoid circular import (tools → clients → utils → tools)
            from memoryhub.mcp.clients import SearchClient

            # Use typed SearchClient for API calls
            search_client = SearchClient(client, active_project.external_id)
            result = await search_client.search(
                search_query.model_dump(),
                page=page,
                page_size=page_size,
            )

            # Check if we got no results and provide helpful guidance
            if not result.results:
                logger.debug(
                    f"Search returned no results for query: {query} in project {active_project.name}"
                )
                # Don't treat this as an error, but the user might want guidance
                # We return the empty result as normal - the user can decide if they need help

            if output_format == "json":
                return result.model_dump(mode="json", exclude_none=True)

            return result

        except Exception as e:
            logger.error(
                f"Search failed for query '{query or ''}': {e}, project: {active_project.name}"
            )
            # Return formatted error message as string for better user experience
            return _format_search_error_response(
                active_project.name, str(e), query or "", effective_search_type
            )
