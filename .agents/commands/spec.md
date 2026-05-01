# Specification Workflow

Use this workflow when asked to create, inspect, or review repository
specifications stored in Basic Memory.

## Inputs

- Operation: `create`, `status`, `show`, or `review`
- Optional spec name

## Required MCP Tools

- `write_note`
- `read_note`
- `search_notes`
- `edit_note`

## Context

Specifications are managed in the Basic Memory `specs` project. See the
existing `SPEC-*` notes there for the established specification format and
process.

## Procedure

### Create

1. Find the next available spec number by searching the `specs` project.
2. Create the new spec note in project `specs`.
3. Include the standard sections:
   - Why
   - What
   - How
   - How to Evaluate

### Status

1. Search the `specs` project for active specifications.
2. Summarize spec number, title, and progress.
3. Use checkbox progress where present rather than inventing completion data.

### Show

1. Read the requested spec note from project `specs`.
2. Return the full spec content or a faithful summary, depending on the user's
   request.

### Review

1. Read the requested spec and its `How to Evaluate` section.
2. Review implementation status against:
   - functional completeness
   - test coverage
   - code quality checks
   - architecture compliance
   - documentation completeness
3. Be explicit about gaps and do not overstate readiness.
4. Update the spec note with review findings when asked.
