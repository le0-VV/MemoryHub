# OpenViking Compatibility Contract

MemoryHub is an OpenViking implementation layer, not a drop-in replacement for
the OpenViking CLI, package API, import/export format, or server runtime.

## Supported

- Repository-local context root: `.agents/memoryhub/`.
- Central project registry: `$MEMORYHUB_CONFIG_DIR/projects/<project>`.
- Markdown source of truth with rebuildable SQLite derived state.
- MemoryHub-supported project URI form:
  `openviking://project/<project>/<relative-markdown-path>`.

## Unsupported

- Drop-in OpenViking CLI compatibility.
- Drop-in OpenViking Python package compatibility.
- OpenViking import/export compatibility.
- OpenViking server compatibility.

Any future compatibility claim must be added here and covered by conformance
tests before product documentation may describe it as supported.
