# Beta Release Playbook

Use this workflow when asked to create a beta or release candidate tag for this
repository.

## Inputs

- Target version, for example `v0.13.2b1` or `v0.13.2rc1`

## Preconditions

- Working tree is clean
- Current branch is `main`
- Target tag does not already exist
- Relevant changelog and release notes work is ready

## Procedure

1. Validate the version format matches `vX.Y.ZbN` or `vX.Y.ZrcN`.
2. Run the automated beta release workflow:
   ```bash
   just beta <version>
   ```
3. Confirm the tag was pushed and the release workflow started.
4. Monitor GitHub Actions for package build and PyPI pre-release publication.
5. Verify installation instructions still work for the generated beta.

## Validation

- GitHub Actions started successfully
- PyPI pre-release published successfully
- Installed version reports the expected beta version

Example install commands:

```bash
uv tool install basic-memory --pre
uv tool upgrade basic-memory --prerelease=allow
```

## Notes

- The repository still uses inherited `basic-memory` packaging names during the
  MemoryHub transition.
- Beta releases are for validating changes before a stable tag is created.
