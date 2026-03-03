# Release Readiness Check

Use this workflow for a read-only release preflight check.

## Inputs

- Optional target version, for example `v0.13.0`

## Procedure

1. Check repository state:
   - Working tree clean
   - Current branch is `main`
   - No conflicting existing tag
2. Validate code quality gates:
   ```bash
   just lint
   just typecheck
   just test
   ```
3. Validate release documentation:
   - `CHANGELOG.md` has the intended entry
   - `README.md` does not contradict the release state
   - Relevant docs are up to date
4. Validate packaging and build assumptions:
   - Package metadata is consistent
   - Release workflows are still aligned with the repo state
5. Summarize:
   - Passed checks
   - Warnings
   - Blocking issues
   - Recommendation: ready or not ready

## Constraints

- This workflow should not modify files, create commits, or create tags.
- If something is ambiguous, report it as a warning rather than guessing.
