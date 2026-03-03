# AI Assistant Guide for MemoryHub

This guide describes how an AI assistant should work with MemoryHub through MCP. The current code
still exposes the inherited `basic-memory` command and `basic_memory` package name, but the fork's
intended product identity is MemoryHub.

## Mental Model

MemoryHub is a local-first knowledge system built from:

- markdown files as the source of truth
- SQLite as the derived index
- MCP tools for searching, reading, editing, and linking notes

The assistant's job is not to keep private hidden memory. The job is to help the user produce
durable notes that remain useful outside any one session or model.

## Operating Assumptions

- deployment is local-only
- SQLite is the only supported backend
- project selection is still explicit-first
- hosted cloud routing and managed sync are not part of the supported fork direction

## Session Start

When project context is unclear:

1. call `list_memory_projects()`
2. identify the likely target
3. ask the user only if project choice is genuinely ambiguous
4. reuse the chosen project consistently for later calls

If the user already named the project, do not re-ask.

## Note Structure

A good note usually has:

- clear frontmatter
- a descriptive title
- several atomic observations
- explicit relations to other notes

Example:

```markdown
---
title: Authentication Design
type: spec
tags: [auth, security]
---

# Authentication Design

## Observations
- [decision] Use JWT access tokens with refresh rotation #security
- [requirement] Support OAuth providers and email/password #auth
- [technique] Keep secrets out of markdown and store references instead #ops

## Relations
- implements [[User Auth Roadmap]]
- depends_on [[Session Storage]]
```

## Reading Workflow

Prefer this order:

1. `search_notes()` to find candidates
2. `read_note()` to inspect a note structurally
3. `build_context()` when surrounding relationships matter
4. `view_note()` when a rendered note is easier for a human to consume
5. `read_content()` only for raw files or non-markdown assets

## Writing Workflow

Before creating a new note:

1. search for an existing note on the topic
2. edit the existing note if the information belongs there
3. create a new note only when the topic is distinct

Good observation style:

- one fact per bullet
- meaningful category names
- tags only when they help retrieval
- relations that say what the connection means

Avoid vague bullets like:

```markdown
- [note] stuff about auth
- [info] some changes happened
```

Prefer:

```markdown
- [decision] Switched default search mode to hybrid when semantic search is enabled
- [problem] Duplicate titles across projects make naive title lookup ambiguous
```

## Search Strategy

Use search modes deliberately:

- `text`: exact keywords and boolean-style searches
- `title`: known-note lookup by title
- `permalink`: path-like identifiers and filename patterns
- `vector` or `semantic`: conceptual similarity
- `hybrid`: good general default when semantic search is enabled

Use metadata filters when frontmatter matters:

```python
await search_notes(
    query="authentication",
    metadata_filters={"status": "draft", "priority": {"$in": ["high", "critical"]}},
    project="main",
)
```

## Context Building

Use `build_context()` when continuity matters:

- continuing a prior design discussion
- understanding dependencies
- surfacing nearby decisions
- reconstructing a thread across several files

Use shallow depth by default:

- `depth=1`: immediate neighbors
- `depth=2`: usually enough for useful context
- `depth>=3`: only when the user clearly needs a broader graph walk

## Editing Notes Safely

Prefer narrow edits over rewrites:

- `append` for new facts
- `prepend` for summaries or status banners
- `find_replace` for deterministic text edits
- `replace_section` when a heading needs targeted replacement

If an operation could hit multiple matches, use expected replacement counts so the edit fails fast
instead of mutating more content than intended.

## Recording Conversations

Only save conversation summaries when the user wants that.

Best pattern:

1. ask permission
2. summarize the durable outcome
3. store decisions, discoveries, and action items
4. avoid dumping raw chat logs unless the user explicitly asks for that

What is worth saving:

- decisions and rationale
- debugging discoveries
- architecture tradeoffs
- plans and next steps
- recurring user preferences that affect future work

What is usually not worth saving:

- filler dialogue
- pleasantries
- content that duplicates an existing note without adding signal

## Error Handling

If a note is missing:

1. search for close matches
2. present plausible alternatives
3. create a new note only if the user intends one

If project choice is ambiguous:

1. list projects
2. ask which project to use
3. do not guess when the risk of writing to the wrong project is meaningful

If search returns nothing:

1. broaden the query
2. try another search mode
3. check whether metadata filters are too strict

## Core Tools

The most important tools for assistants are:

- `search_notes`
- `read_note`
- `view_note`
- `read_content`
- `write_note`
- `edit_note`
- `move_note`
- `delete_note`
- `build_context`
- `recent_activity`
- `list_directory`
- `list_memory_projects`
- `create_memory_project`
- `delete_project`
- `schema_validate`
- `schema_infer`
- `schema_diff`

## Schema Guidance

Schemas are notes with `type: schema`. They describe expected structure without introducing a new
storage system.

Use schema tools when:

- the user wants repeatable note structure
- a note type needs validation
- you want to infer a schema from many existing notes
- you want to inspect drift between a schema and actual usage

## Best Practices

1. Prefer durable knowledge over verbose transcripts.
2. Search before creating new notes.
3. Use explicit relation types when the relationship matters.
4. Keep observations atomic and specific.
5. Ask before storing conversation summaries.
6. Use project names deliberately in multi-project work.
7. Treat markdown files as the real artifact; the database is only an index.

## Summary

For this fork, optimize for:

- local workflows
- SQLite-backed retrieval
- explicit project handling
- high-quality markdown notes
- agent-neutral usage patterns

Do not assume cloud routing, managed sync, or hosted infrastructure unless the repo is explicitly
changed to support them again.
