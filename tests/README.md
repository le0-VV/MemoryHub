# SQLite Testing

MemoryHub tests run against SQLite only.

## Quick Start

```bash
# Run tests against SQLite only (default, no setup needed)
pytest

# Run the full test suite
just test
```

## How It Works

### Parametrized Backend Fixture

The `db_backend` fixture is fixed to `sqlite`:

```python
@pytest.fixture(
    params=[pytest.param("sqlite", id="sqlite")]
)
def db_backend(request) -> Literal["sqlite"]:
    return request.param
```

### Backend-Specific Engine Factories

The test engine factory uses in-memory SQLite for fast, isolated tests.

The main `engine_factory` fixture delegates to the appropriate implementation
based on `db_backend`.

### Configuration

The `app_config` fixture automatically configures the correct backend:

```python
# SQLite config
database_backend = DatabaseBackend.SQLITE
database_url = None  # Uses default SQLite path

```

## Test Isolation

### SQLite Tests

- Each test gets a fresh in-memory database
- Automatic cleanup (database destroyed after test)
- No setup required

## Markers

- `semantic` - Semantic search tests
- `smoke` - MCP smoke tests

## CI Integration

Repository CI workflows are currently removed in this fork. Run the suite
locally with `just test`, `just test-sqlite`, and `just doctor`.

## Troubleshooting

### Tests hang or timeout

Check for lingering local processes or stale temp directories:

```bash
ps aux | rg pytest
```

## Future Enhancements

- [ ] Expand semantic benchmark coverage for local-only workflows
- [ ] Add more targeted MCP integration fixtures
