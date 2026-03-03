"""Environment-variable compatibility helpers for the MemoryHub fork."""

from typing import Iterable, Optional


def get_env_value(names: Iterable[str], default: Optional[str] = None) -> Optional[str]:
    """Return the first non-empty environment value from a priority-ordered list."""
    import os

    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default


def is_truthy_env(names: Iterable[str]) -> bool:
    """Return True when the first matching env value is a truthy flag."""
    value = get_env_value(names, default="")
    return value.strip().lower() in {"1", "true", "yes", "on"}


PROJECT_CONSTRAINT_ENV_VARS = ("MEMORYHUB_MCP_PROJECT", "BASIC_MEMORY_MCP_PROJECT")
HOME_ENV_VARS = ("MEMORYHUB_HOME", "BASIC_MEMORY_HOME")
CONFIG_DIR_ENV_VARS = ("MEMORYHUB_CONFIG_DIR", "BASIC_MEMORY_CONFIG_DIR")
LOG_LEVEL_ENV_VARS = ("MEMORYHUB_LOG_LEVEL", "BASIC_MEMORY_LOG_LEVEL")
RUNTIME_ENV_VARS = ("MEMORYHUB_ENV", "BASIC_MEMORY_ENV")
TENANT_ID_ENV_VARS = ("MEMORYHUB_TENANT_ID", "BASIC_MEMORY_TENANT_ID")
NO_PROMOS_ENV_VARS = ("MEMORYHUB_NO_PROMOS", "BASIC_MEMORY_NO_PROMOS")
UI_VARIANT_ENV_VARS = ("MEMORYHUB_MCP_UI_VARIANT", "BASIC_MEMORY_MCP_UI_VARIANT")
