# agent-basics Integration Status

- Sender repo: `/Users/leonardw/Projects/agent-basics`
- Target repo: `/Users/leonardw/Projects/MemoryHub`
- Date: 2026-04-30
- Action needed: keep future MemoryHub changes compatible with the central-hub contract below.

## Summary

The agent-basics bootstrap path now depends on MemoryHub as the mandatory central memory provider. It no longer expects a per-repo OpenViking install, per-repo embedding model, or per-repo vector/runtime stack.

Verified locally with isolated temp state:

- `memoryhub project list --json`
- `memoryhub project add`
- `memoryhub doctor`
- symlinked project source through `$MEMORYHUB_CONFIG_DIR/projects/<project>`
- full `agent-basics/setup-macos.sh` smoke run using the real MemoryHub executable

## Contract To Preserve

- One central MemoryHub runtime under `$MEMORYHUB_CONFIG_DIR`.
- Repo-local memory markdown under `.agents/memoryhub/`.
- Hub project path symlinked from `$MEMORYHUB_CONFIG_DIR/projects/<project>` to the repo-local memory directory.
- Stable CLI behavior for `memoryhub project add`, `memoryhub project list --json`, and `memoryhub doctor`.
- Deterministic project registry and cwd/repository resolution.
- Safe sync/indexing when project paths are symlinks.

## Future Work

Please add regression coverage around symlinked project registration, JSON project listing, repo-style `.agents/memoryhub/` sources, and concurrent use by multiple agents through the same central hub.
