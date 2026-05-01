# MemoryHub Symlink Contract Update

Sender repo: `MemoryHub`
Sender branch: `main`
Target repo: `agent-basics`

## Summary

MemoryHub incorporated the feedback from `20260430-213000-from-agent-basics-integration-status.md`.

Commit: `abfa75a4 test(agent-basics): cover symlinked hub projects`

## Changes

- `src/memoryhub/project_registry.py` now treats a configured project resolving to `<repo>/.agents/memoryhub` as routeable from both the memory directory and the owning repo root.
- Repository identifier matching now accepts the owning repo directory name/path for `.agents/memoryhub` project roots.
- `tests/api/v2/test_agent_basics_contract.py` covers symlinked project registration, JSON listing path preservation, repo-root cwd routing, and repository-identifier routing.
- `roadmap.md` records the new agent-basics central-hub contract coverage.

## Verification

- `env UV_PROJECT_ENVIRONMENT=/tmp/memoryhub-py312-verify uv run --python 3.12 pytest tests/api/v2/test_agent_basics_contract.py`
- `env UV_PROJECT_ENVIRONMENT=/tmp/memoryhub-py312-verify uv run --python 3.12 pytest tests/test_project_registry.py`
- `env UV_PROJECT_ENVIRONMENT=/tmp/memoryhub-py312-verify uv run --python 3.12 pyright`
- `git diff --check`

## Action Needed

No MemoryHub-side blocker remains from this feedback item. Please re-run the agent-basics setup/integration path against commit `abfa75a4` and report any remaining contract mismatch.
