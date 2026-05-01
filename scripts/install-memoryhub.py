#!/usr/bin/env python3
"""Install MemoryHub from this checkout."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root / "src"))

    from memoryhub.adapters.cli.main import run

    return run(["install", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
