# Live Testing Suite

Use this workflow when asked to perform real-world end-to-end testing of the
installed Basic Memory runtime.

## Inputs

- Optional phase: `recent`, `core`, `features`, or `all`

## Purpose

Execute real product testing through the actual MCP and CLI surfaces, and store
findings in a dedicated test project.

## Pre-Test Setup

1. Verify the installed executable is accessible.
2. Record the current version under test.
3. Review recent commits when the request focuses on recent changes.
4. Create a dedicated timestamped test project for this run.
5. Record a baseline session note with environment and scope.

## Test Priorities

### Tier 1: Critical Core

1. `write_note`
2. `read_note`
3. `search_notes`
4. `edit_note`
5. `list_memory_projects`
6. `recent_activity`

### Tier 2: Important Workflows

7. `build_context`
8. `create_memory_project`
9. `move_note`
10. `sync_status`
11. `delete_project`

### Tier 3: Enhanced Functionality

12. `view_note`
13. `read_content`
14. `delete_note`
15. `list_directory`
16. advanced `edit_note` modes

## Key Validation Areas

- Project discovery and project parameter handling
- Stateless tool behavior
- `memory://` URL navigation
- File sync and watch behavior
- Edge cases, invalid inputs, and performance under moderate stress

## Observation Requirements

Record findings as notes in the test project:

- successful operations
- failures and reproduction steps
- performance observations
- usability or workflow friction
- enhancement ideas discovered during testing

## Output

Produce:

1. A session summary note
2. Individual bug notes for meaningful failures
3. Performance and reliability observations
4. Clear release-readiness or follow-up recommendations

## Constraints

- Prefer end-to-end behavior validation over mocked assumptions.
- Use the currently shipped command names and MCP tools, even if the long-term
  product branding is changing.
