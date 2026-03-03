# Contributing to MemoryHub

MemoryHub is an experimental fork of Basic Memory. This repository is still in the transition phase: most code, modules, and commands still use inherited `memoryhub` / `memoryhub` naming, while the product direction is shifting toward a multi-project MCP hub.

This document covers how to contribute to the fork without confusing it with the upstream project.

## Getting Started

1. Clone this fork:
    ```bash
    git clone https://github.com/le0-VV/MemoryHub.git
    cd MemoryHub
    ```
2. Install dependencies:
    ```bash
    just install
    ```
Or:
    ```bash
    pip install -e ".[dev]"
    ```
3. Run the fast local check loop:
    ```bash
    just fast-check
    ```
4. Run the end-to-end consistency check when needed:
    ```bash
    just doctor
    ```

## Current Naming Caveat

Until the rename is complete:

- The Python package is still `memoryhub`
- The CLI entrypoints are still `memoryhub` and `bm`
- The MCP server still identifies itself as `Basic Memory`

If you want to run this fork, install from the local checkout. Do not use `uv tool install memoryhub`, because that installs the upstream package from PyPI.

## Development Workflow

1. Create a branch from `main`.
2. Make the smallest defensible change.
3. Run the relevant checks:
    ```bash
    just lint
    just typecheck
    just test-sqlite
    ```
4. Run the full suite when the change warrants it:
    ```bash
    just test
    ```
5. Submit a pull request describing what changed, why it changed, and how you verified it.

## Pull Request Reviews

This fork no longer uses repository-local Claude GitHub Actions workflows for PR review or issue triage.

If you use AI-assisted review on GitHub, use the current Codex/GitHub native review flow instead of the deleted Claude workflow files.

## Release Automation Status

During the rename transition:

- Dependabot remains enabled
- GitHub Actions workflows are currently removed
- Issue templates are currently removed
- PyPI, Homebrew, and Docker publishing are not configured

Do not assume upstream Basic Memory release infrastructure applies to this fork.

## Priorities For This Fork

Changes are especially helpful when they improve one of these areas:

- Documentation that accurately reflects the fork status
- Metadata and publishing config that stop pointing at the upstream project
- Routing architecture for multi-project MCP usage
- Tests that preserve upstream behavior while the fork evolves

Avoid changing inherited package names or release semantics casually. Those changes affect installation, registry metadata, and compatibility, and should be done deliberately.

## Agent Guidance

This repository keeps agent-specific working guidance in [AGENTS.md](AGENTS.md). If you are using an LLM or coding agent, start there.

Useful reference points:

- [README.md](README.md): current fork status and roadmap
- [README_old.md](README_old.md): preserved upstream README
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): current code architecture

## Developer Certificate Of Origin

This fork uses the [Developer Certificate of Origin](CLA.md), not a separate copyright assignment CLA. Sign commits with:

```bash
git commit -s -m "Your commit message"
```

## Code Style And Testing

- Python 3.12+
- Full type annotations
- Ruff formatting and linting
- Pyright type checking
- 100-character line length
- Tests are required for behavior changes

Common commands:

```bash
just fast-check
just doctor
just test
just test-sqlite
pytest tests/path/to/test_file.py::test_function_name
```

## Code Of Conduct

All contributors must follow the [Code of Conduct](CODE_OF_CONDUCT.md).
