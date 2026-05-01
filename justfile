install:
    uv sync

lint:
    uv run ruff check .

format:
    uv run ruff format .

typecheck:
    uv run pyright

test:
    uv run pytest

fast-check:
    uv run ruff check .
    uv run pyright
    uv run pytest

check: fast-check

doctor:
    uv run memoryhub doctor
