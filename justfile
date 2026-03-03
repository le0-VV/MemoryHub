# Basic Memory - Modern Command Runner

# Install dependencies
install:
    uv sync
    @echo ""
    @echo "💡 Remember to activate the virtual environment by running: source .venv/bin/activate"

# ==============================================================================
# TESTING
# ==============================================================================
# MemoryHub is SQLite-only.
#
# Quick Start:
#   just test
#   just test-sqlite
#   just test-unit-sqlite
#   just test-int-sqlite
# ==============================================================================

# Run all tests
test: test-sqlite

# Run all tests against SQLite
test-sqlite: test-unit-sqlite test-int-sqlite

# Run unit tests against SQLite
test-unit-sqlite:
    BASIC_MEMORY_ENV=test uv run pytest -p pytest_mock -v --no-cov tests

# Run integration tests against SQLite (excludes semantic benchmarks — use just test-semantic)
test-int-sqlite:
    BASIC_MEMORY_ENV=test uv run pytest -p pytest_mock -v --no-cov -m "not semantic" test-int

# Run tests impacted by recent changes (requires pytest-testmon)
testmon *args:
    BASIC_MEMORY_ENV=test uv run pytest -p pytest_mock -v --no-cov --testmon --testmon-forceselect {{args}}

# Run MCP smoke test (fast end-to-end loop)
test-smoke:
    BASIC_MEMORY_ENV=test uv run pytest -p pytest_mock -v --no-cov -m smoke test-int/mcp/test_smoke_integration.py

# Fast local loop: lint, format, typecheck, impacted tests
fast-check:
    just fix
    just format
    just typecheck
    just testmon
    just test-smoke

# Run Windows-specific tests only (only works on Windows platform)
# These tests verify Windows-specific database optimizations (locking mode, NullPool)
# Will be skipped automatically on non-Windows platforms
test-windows:
    BASIC_MEMORY_ENV=test uv run pytest -p pytest_mock -v --no-cov -m windows tests test-int

# Run benchmark tests only (performance testing)
# These are slow tests that measure sync performance with various file counts
# Excluded from default test runs to keep CI fast
test-benchmark:
    BASIC_MEMORY_ENV=test uv run pytest -p pytest_mock -v --no-cov -m benchmark tests test-int

# Run semantic search quality benchmarks (all combos)
test-semantic:
    BASIC_MEMORY_ENV=test uv run pytest -p pytest_mock -v --no-cov -m semantic test-int/semantic/

# Run semantic benchmarks with JSON artifact output, then show report
test-semantic-report:
    BASIC_MEMORY_ENV=test BASIC_MEMORY_BENCHMARK_OUTPUT=.benchmarks/semantic-quality.jsonl uv run pytest -p pytest_mock -v -s --no-cov -m semantic test-int/semantic/
    uv run python test-int/semantic/report.py .benchmarks/semantic-quality.jsonl

# View semantic benchmark results (rich formatted table)
# Usage: just semantic-report [--filter-combo sqlite] [--filter-suite paraphrase] [--sort-by avg_latency_ms]
semantic-report *args:
    uv run python test-int/semantic/report.py .benchmarks/semantic-quality.jsonl {{args}}

# Compare two search benchmark JSONL outputs
# Usage:
#   just benchmark-compare .benchmarks/search-baseline.jsonl .benchmarks/search-candidate.jsonl
#   just benchmark-compare .benchmarks/search-baseline.jsonl .benchmarks/search-candidate.jsonl --format markdown --show-missing
benchmark-compare baseline candidate *args:
    uv run python test-int/compare_search_benchmarks.py "{{baseline}}" "{{candidate}}" --format table {{args}}

# Run all tests including Windows-specific and benchmark suites
test-all:
    BASIC_MEMORY_ENV=test uv run pytest -p pytest_mock -v --no-cov tests test-int

# Generate HTML coverage report
coverage:
    #!/usr/bin/env bash
    set -euo pipefail
    
    uv run coverage erase
    
    echo "🔎 Coverage..."
    BASIC_MEMORY_ENV=test uv run coverage run --source=basic_memory -m pytest -p pytest_mock -v --no-cov tests test-int
    uv run coverage report -m
    uv run coverage html
    echo "Coverage report generated in htmlcov/index.html"

# Lint and fix code (calls fix)
lint: fix

# Lint and fix code
fix:
    uv run ruff check --fix --unsafe-fixes src tests test-int

# Type check code (pyright)
typecheck:
    uv run pyright

# Type check code (ty)
typecheck-ty:
    uv run ty check src/

# Clean build artifacts and cache files
clean:
    find . -type f -name '*.pyc' -delete
    find . -type d -name '__pycache__' -exec rm -r {} +
    rm -rf installer/build/ installer/dist/ dist/
    rm -f rw.*.dmg .coverage.*

# Format code with ruff
format:
    uv run ruff format .

# Run MCP inspector tool
run-inspector:
    npx @modelcontextprotocol/inspector

# Run doctor checks in an isolated temp home/config
doctor:
    #!/usr/bin/env bash
    set -euo pipefail
    TMP_HOME=$(mktemp -d)
    TMP_CONFIG=$(mktemp -d)
    HOME="$TMP_HOME" \
    BASIC_MEMORY_ENV=test \
    BASIC_MEMORY_HOME="$TMP_HOME/basic-memory" \
    BASIC_MEMORY_CONFIG_DIR="$TMP_CONFIG" \
    ./.venv/bin/python -m basic_memory.cli.main doctor --local


# Update all dependencies to latest versions
update-deps:
    uv sync --upgrade

# Run all code quality checks and tests
check: lint format typecheck test

# Run all code quality checks and all test suites, including semantic benchmarks
check-all: lint format typecheck test test-semantic

# Generate Alembic migration with descriptive message
migration message:
    cd src/basic_memory/alembic && alembic revision --autogenerate -m "{{message}}"

# Create a stable release (e.g., just release v0.13.2)
release version:
    #!/usr/bin/env bash
    set -euo pipefail
    
    # Validate version format
    if [[ ! "{{version}}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "❌ Invalid version format. Use: v0.13.2"
        exit 1
    fi
    
    # Extract version number without 'v' prefix
    VERSION_NUM=$(echo "{{version}}" | sed 's/^v//')
    
    echo "🚀 Creating stable release {{version}}"
    
    # Pre-flight checks
    echo "📋 Running pre-flight checks..."
    if [[ -n $(git status --porcelain) ]]; then
        echo "❌ Uncommitted changes found. Please commit or stash them first."
        exit 1
    fi
    
    if [[ $(git branch --show-current) != "main" ]]; then
        echo "❌ Not on main branch. Switch to main first."
        exit 1
    fi
    
    # Check if tag already exists
    if git tag -l "{{version}}" | grep -q "{{version}}"; then
        echo "❌ Tag {{version}} already exists"
        exit 1
    fi
    
    # Run quality checks
    echo "🔍 Running lint  checks..."
    just lint
    just typecheck
    
    # Update version in __init__.py
    echo "📝 Updating version in __init__.py..."
    sed -i.bak "s/__version__ = \".*\"/__version__ = \"$VERSION_NUM\"/" src/basic_memory/__init__.py
    rm -f src/basic_memory/__init__.py.bak

    # Update version in server.json (MCP registry metadata)
    echo "📝 Updating version in server.json..."
    sed -i.bak "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION_NUM\"/g" server.json
    rm -f server.json.bak

    # Commit version update
    git add src/basic_memory/__init__.py server.json
    git commit -m "chore: update version to $VERSION_NUM for {{version}} release"
    
    # Create and push tag
    echo "🏷️  Creating tag {{version}}..."
    git tag "{{version}}"
    
    echo "📤 Pushing to GitHub..."
    git push origin main
    git push origin "{{version}}"
    
    echo "✅ Release {{version}} tag created successfully!"
    echo "📦 This fork does not currently ship via repository workflows"
    echo "🔗 Review tags/releases manually in the GitHub UI as needed"
    echo ""
    echo "📝 REMINDER: Post-release tasks:"
    echo "   1. Draft or review the GitHub Release manually if you want one"
    echo "   2. Update any fork documentation that should mention the new tag"
    echo "   3. There is no Docker publishing pipeline in this fork right now"
    echo "   See: .agents/commands/release/release.md for detailed instructions"

# Create a beta release (e.g., just beta v0.13.2b1)
beta version:
    #!/usr/bin/env bash
    set -euo pipefail
    
    # Validate version format (allow beta/rc suffixes)
    if [[ ! "{{version}}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(b[0-9]+|rc[0-9]+)$ ]]; then
        echo "❌ Invalid beta version format. Use: v0.13.2b1 or v0.13.2rc1"
        exit 1
    fi
    
    # Extract version number without 'v' prefix
    VERSION_NUM=$(echo "{{version}}" | sed 's/^v//')
    
    echo "🧪 Creating beta release {{version}}"
    
    # Pre-flight checks
    echo "📋 Running pre-flight checks..."
    if [[ -n $(git status --porcelain) ]]; then
        echo "❌ Uncommitted changes found. Please commit or stash them first."
        exit 1
    fi
    
    if [[ $(git branch --show-current) != "main" ]]; then
        echo "❌ Not on main branch. Switch to main first."
        exit 1
    fi
    
    # Check if tag already exists
    if git tag -l "{{version}}" | grep -q "{{version}}"; then
        echo "❌ Tag {{version}} already exists"
        exit 1
    fi
    
    # Run quality checks
    echo "🔍 Running lint  checks..."
    just lint
    just typecheck
    
    # Update version in __init__.py
    echo "📝 Updating version in __init__.py..."
    sed -i.bak "s/__version__ = \".*\"/__version__ = \"$VERSION_NUM\"/" src/basic_memory/__init__.py
    rm -f src/basic_memory/__init__.py.bak

    # Update version in server.json (MCP registry metadata)
    echo "📝 Updating version in server.json..."
    sed -i.bak "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION_NUM\"/g" server.json
    rm -f server.json.bak

    # Commit version update
    git add src/basic_memory/__init__.py server.json
    git commit -m "chore: update version to $VERSION_NUM for {{version}} beta release"
    
    # Create and push tag
    echo "🏷️  Creating tag {{version}}..."
    git tag "{{version}}"
    
    echo "📤 Pushing to GitHub..."
    git push origin main
    git push origin "{{version}}"
    
    echo "✅ Beta release {{version}} tag created successfully!"
    echo "📦 This fork does not currently build release artifacts via repository workflows"
    echo "📥 Install from a local checkout or create artifacts manually as needed"
    echo ""
    echo "📝 REMINDER:"
    echo "   1. This fork does not auto-publish to PyPI, Homebrew, or Docker"
    echo "   2. Draft prereleases manually in GitHub if you want them published there"
    echo "   See: .agents/commands/release/release.md for detailed instructions"

# List all available recipes
default:
    @just --list
