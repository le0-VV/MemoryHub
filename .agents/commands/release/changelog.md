# Changelog Drafting Guide

Use this workflow when asked to generate or update a changelog entry for a
release.

## Inputs

- Version, for example `v0.14.0` or `v0.14.0b1`
- Release type when relevant: `beta`, `rc`, or `stable`

## Procedure

1. Determine the commit range since the previous comparable release tag.
2. Review commits and categorize changes:
   - Features
   - Bug fixes
   - Technical improvements
   - Breaking changes
3. Cross-check the commit list against the actual diff when commit messages are
   ambiguous.
4. Draft a changelog entry in the style already used in `CHANGELOG.md`.
5. Include issue references and commit links when they materially help
   traceability.
6. Verify that user-facing behavior changes are documented, not just internal
   refactors.

## Output Expectations

- Concise summary of value delivered
- Feature and fix bullets grouped logically
- Explicit migration notes when behavior changed
- No invented claims that are not supported by the code or commit history

## Validation

- Entry matches the repository's existing changelog structure
- Major changes since the previous release are represented
- Breaking changes and migration guidance are explicit
