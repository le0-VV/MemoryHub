## Coverage policy (practical 100%)

MemoryHub’s test suite intentionally mixes:
- unit tests (fast, deterministic)
- integration tests (real filesystem + real DB via `test-int/`)

To keep the default CI signal **stable and meaningful**, the default `pytest` coverage report targets **core library logic** and **excludes** a small set of modules that are either:
- highly environment-dependent (OS/DB tuning)
- inherently interactive (CLI)
- background-task orchestration (watchers/sync runners)

### What's excluded (and why)

Coverage excludes are configured in `pyproject.toml` under `[tool.coverage.report].omit`.

Current exclusions include:
- `src/basic_memory/cli/**`: interactive wrappers; behavior is validated via higher-level tests and smoke tests.
- `src/basic_memory/db.py`: platform and initialization paths that are better covered by integration runs than by strict unit coverage.
- `src/basic_memory/services/initialization.py`: startup orchestration/background tasks; covered indirectly by app/MCP entrypoints.
- `src/basic_memory/sync/sync_service.py`: heavy filesystem↔DB integration; validated in integration suite (not enforced in unit coverage).

### Recommended additional runs

If you want extra confidence locally/CI:
- **SQLite backend**: the fork runs tests against SQLite only.
- **Coverage check**: run `just coverage` for the SQLite-only suite.
