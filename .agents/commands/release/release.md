# Stable Release Playbook

Use this workflow when asked to create a stable release tag for this
repository.

## Inputs

- Target stable version, for example `v0.13.2`

## Preconditions

- Beta testing is complete when applicable
- Working tree is clean
- Current branch is `main`
- Target tag does not already exist
- Changelog and release notes are ready

## Procedure

1. Validate the version format matches `vX.Y.Z`.
2. Run the automated stable release workflow:
   ```bash
   just release <version>
   ```
3. Confirm the tag was pushed and the release workflow started.
4. Monitor GitHub Actions for:
   - package build
   - GitHub release creation
   - PyPI publication
5. Verify the published package can be installed and reports the expected
   version.

## Post-Release Checks

- GitHub release exists and contains build artifacts
- PyPI package exists for the released version
- Any downstream registry or documentation updates required by the current
  release process are called out explicitly

## Constraints

- Do not assume external websites, local paths, or deployment environments that
  are not documented in this repository.
- The repository still uses inherited `basic-memory` package names during the
  MemoryHub transition, so stable release validation should use those current
  package coordinates.
