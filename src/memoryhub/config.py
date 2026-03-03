"""Configuration management for MemoryHub."""

import importlib.util
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Literal, Optional, List, Tuple
from enum import Enum

from loguru import logger
from pydantic import AliasChoices, BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from memoryhub.utils import setup_logging, generate_permalink


DATABASE_NAME = "memory.db"
APP_DATABASE_NAME = "memory.db"  # Using the same name but in the app directory
DATA_DIR_NAME = ".memoryhub"
CONFIG_FILE_NAME = "config.json"
WATCH_STATUS_JSON = "watch-status.json"

Environment = Literal["test", "dev", "user"]


class DatabaseBackend(str, Enum):
    """Database backend enum.

    MemoryHub supports SQLite only.
    """

    SQLITE = "sqlite"


def _default_semantic_search_enabled() -> bool:
    """Enable semantic search by default when required local semantic dependencies exist."""
    required_modules = ("fastembed", "sqlite_vec")
    return all(
        importlib.util.find_spec(module_name) is not None for module_name in required_modules
    )


@dataclass
class ProjectConfig:
    """Configuration for a specific local MemoryHub project."""

    name: str
    home: Path

    @property
    def project(self):
        return self.name  # pragma: no cover

    @property
    def project_url(self) -> str:  # pragma: no cover
        return f"/{generate_permalink(self.name)}"


class ProjectEntry(BaseModel):
    """Project configuration entry for a local MemoryHub project."""

    path: str = Field(description="Local filesystem path for the project")


class BasicMemoryConfig(BaseSettings):
    """Pydantic model for MemoryHub global configuration.

    The class name is retained for compatibility while the supported product
    surface continues to converge on MemoryHub naming.
    """

    env: Environment = Field(default="dev", description="Environment name")

    projects: Dict[str, ProjectEntry] = Field(
        default_factory=lambda: {
            "main": ProjectEntry(
                path=str(Path(os.getenv("BASIC_MEMORY_HOME", Path.home() / "memoryhub")))
            )
        }
        if os.getenv("BASIC_MEMORY_HOME")
        else {},
        description="Mapping of project names to their ProjectEntry configuration",
    )
    default_project: Optional[str] = Field(
        default=None,
        description="Name of the default project to use. When set, acts as fallback when no project parameter is specified. Set to null to disable automatic project resolution.",
    )

    # overridden by ~/.memoryhub/config.json
    log_level: str = "INFO"

    # Database configuration
    database_backend: DatabaseBackend = Field(
        default=DatabaseBackend.SQLITE,
        description="Database backend to use. MemoryHub currently supports sqlite only.",
    )

    database_url: Optional[str] = Field(
        default=None,
        description="Optional explicit SQLite database URL. If not set, SQLite uses the default path.",
    )

    # Semantic search configuration
    semantic_search_enabled: bool = Field(
        default_factory=_default_semantic_search_enabled,
        description="Enable semantic search (vector/hybrid retrieval) for the SQLite backend. Requires semantic dependencies (included by default).",
    )
    semantic_embedding_provider: str = Field(
        default="fastembed",
        description="Embedding provider for local semantic indexing/search.",
    )
    semantic_embedding_model: str = Field(
        default="bge-small-en-v1.5",
        description="Embedding model identifier used by the local provider.",
    )
    semantic_embedding_dimensions: int | None = Field(
        default=None,
        description="Embedding vector dimensions. Auto-detected from provider if not set (384 for FastEmbed, 1536 for OpenAI).",
    )
    semantic_embedding_batch_size: int = Field(
        default=64,
        description="Batch size for embedding generation.",
        gt=0,
    )
    semantic_vector_k: int = Field(
        default=100,
        description="Vector candidate count for vector and hybrid retrieval.",
        gt=0,
    )
    semantic_min_similarity: float = Field(
        default=0.55,
        description="Minimum similarity score for vector search results. Results below this threshold are filtered out. 0.0 disables filtering.",
        ge=0.0,
        le=1.0,
    )

    # Legacy connection pool configuration fields retained for config compatibility
    db_pool_size: int = Field(
        default=20,
        description="Legacy compatibility field. Ignored in SQLite-only mode.",
        gt=0,
    )
    db_pool_overflow: int = Field(
        default=40,
        description="Legacy compatibility field. Ignored in SQLite-only mode.",
        gt=0,
    )
    db_pool_recycle: int = Field(
        default=180,
        description="Legacy compatibility field. Ignored in SQLite-only mode.",
        gt=0,
    )

    # Watch service configuration
    sync_delay: int = Field(
        default=1000, description="Milliseconds to wait after changes before syncing", gt=0
    )

    watch_project_reload_interval: int = Field(
        default=300,
        description="Seconds between reloading project list in watch service. Higher values reduce CPU usage by minimizing watcher restarts. Default 300s (5 min) balances efficiency with responsiveness to new projects.",
        gt=0,
    )

    # update permalinks on move
    update_permalinks_on_move: bool = Field(
        default=False,
        description="Whether to update permalinks when files are moved or renamed. default (False)",
    )

    sync_changes: bool = Field(
        default=True,
        description="Whether to sync changes in real time. default (True)",
    )

    sync_thread_pool_size: int = Field(
        default=4,
        description="Size of thread pool for file I/O operations in the sync service.",
        gt=0,
    )

    sync_max_concurrent_files: int = Field(
        default=10,
        description="Maximum number of files to process concurrently during sync. Limits memory usage on large projects (2000+ files). Lower values reduce memory consumption.",
        gt=0,
    )

    kebab_filenames: bool = Field(
        default=False,
        description="Format for generated filenames. False preserves spaces and special chars, True converts them to hyphens for consistency with permalinks",
    )

    disable_permalinks: bool = Field(
        default=False,
        description="Disable automatic permalink generation in frontmatter. When enabled, new notes won't have permalinks added and sync won't update permalinks. Existing permalinks will still work for reading.",
    )

    write_note_overwrite_default: bool = Field(
        default=False,
        description=(
            "Default value for write_note's overwrite parameter. "
            "When False (default), write_note errors if note already exists. "
            "Set to True to restore pre-v0.20 upsert behavior. "
            "Env: BASIC_MEMORY_WRITE_NOTE_OVERWRITE_DEFAULT"
        ),
    )

    ensure_frontmatter_on_sync: bool = Field(
        default=True,
        description="Ensure markdown files have frontmatter during sync by adding derived title/type/permalink when missing. When combined with disable_permalinks=True, this setting takes precedence for missing-frontmatter files and still writes permalinks.",
    )

    permalinks_include_project: bool = Field(
        default=True,
        description="When True, generated permalinks are prefixed with the project slug (e.g., 'specs/search'). Existing permalinks remain unchanged unless explicitly updated.",
    )

    skip_initialization_sync: bool = Field(
        default=False,
        description="Skip initialization synchronization when a caller manages reconciliation separately.",
    )

    # File formatting configuration
    format_on_save: bool = Field(
        default=False,
        description="Automatically format files after saving using configured formatter. Disabled by default.",
    )

    formatter_command: Optional[str] = Field(
        default=None,
        description="External formatter command. Use {file} as placeholder for file path. If not set, uses built-in mdformat (Python, no Node.js required). Set to 'npx prettier --write {file}' for Prettier.",
    )

    formatters: Dict[str, str] = Field(
        default_factory=dict,
        description="Per-extension formatters. Keys are extensions (without dot), values are commands. Example: {'md': 'prettier --write {file}', 'json': 'prettier --write {file}'}",
    )

    formatter_timeout: float = Field(
        default=5.0,
        description="Maximum seconds to wait for formatter to complete",
        gt=0,
    )

    # Project path constraints
    project_root: Optional[str] = Field(
        default=None,
        description="If set, all projects must be created underneath this directory. Paths will be sanitized and constrained to this root. If not set, projects can be created anywhere (default behavior).",
    )

    init_message_shown: bool = Field(
        default=False,
        description="Whether the one-time local init confirmation has been shown.",
        validation_alias=AliasChoices("init_message_shown", "cloud_promo_first_run_shown"),
    )

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_projects(cls, data: Any) -> Any:
        """Migrate old-format config (Dict[str, str]) to ProjectEntry format.

        Older upstream configs stored projects in several cloud/workspace-aware
        shapes.
        MemoryHub normalizes those to the current local-only format:
          projects: {"name": {"path": "/local/path"}}
        """
        if not isinstance(data, dict):
            return data

        # --- Remove stale keys from old config versions ---
        data.pop("default_project_mode", None)
        data.pop("cloud_mode", None)
        data.pop("cloud_client_id", None)
        data.pop("cloud_domain", None)
        data.pop("cloud_host", None)
        data.pop("cloud_promo_opt_out", None)
        data.pop("cloud_promo_last_version_shown", None)
        data.pop("cloud_api_key", None)
        data.pop("default_workspace", None)

        projects = data.get("projects", {})
        if not projects:
            return data

        # Check if already in new format — peek at first value
        first_value = next(iter(projects.values()), None)
        if isinstance(first_value, str):
            # Old format: {"name": "/path"} → convert
            cloud_projects = data.pop("cloud_projects", {})
            new_projects: Dict[str, Any] = {}
            for name, path in projects.items():
                entry: Dict[str, Any] = {"path": path}
                if name in cloud_projects:
                    cp = cloud_projects[name]
                    if isinstance(cp, dict):
                        local_path = cp.get("local_path")
                    else:
                        local_path = getattr(cp, "local_path", None)
                    if local_path and not os.path.isabs(path):
                        entry["path"] = local_path
                new_projects[name] = entry

            # Pick up legacy cloud_projects entries not already in projects.
            # Their only usable value in the fork is the local working directory.
            for name, cp in cloud_projects.items():
                if name not in new_projects:
                    if isinstance(cp, dict):
                        local_path = cp.get("local_path", "")
                        new_projects[name] = {
                            "path": local_path or "",
                        }

            data["projects"] = new_projects
        else:
            # New format or dict-based — just clean up stale keys
            data.pop("project_modes", None)
            data.pop("cloud_projects", None)

        # --- Promote local_sync_path into path when old config stored a slug in path ---
        projects = data.get("projects", {})
        for entry in projects.values():
            if isinstance(entry, dict):
                lsp = entry.pop("local_sync_path", None) or entry.pop("cloud_sync_path", None)
                path = entry.get("path", "")
                if lsp and not os.path.isabs(path):
                    entry["path"] = lsp
                entry.pop("mode", None)
                entry.pop("workspace_id", None)
                entry.pop("bisync_initialized", None)
                entry.pop("last_sync", None)

        return data

    @property
    def is_test_env(self) -> bool:
        """Check if running in a test environment.

        Returns True if any of:
        - env field is set to "test"
        - BASIC_MEMORY_ENV environment variable is "test"
        - PYTEST_CURRENT_TEST environment variable is set (pytest is running)

        Used to disable features like file watchers during tests.
        """
        return (
            self.env == "test"
            or os.getenv("BASIC_MEMORY_ENV", "").lower() == "test"
            or os.getenv("PYTEST_CURRENT_TEST") is not None
        )

    @classmethod
    def for_cloud_tenant(
        cls,
        database_url: str,
        projects: Optional[Dict[str, "ProjectEntry"]] = None,
    ) -> "BasicMemoryConfig":
        """Tenant-scoped cloud configs are unsupported in the SQLite-only fork."""
        raise RuntimeError(
            "MemoryHub is SQLite-only in this fork; cloud tenant database configs are unsupported."
        )

    model_config = SettingsConfigDict(
        env_prefix="BASIC_MEMORY_",
        extra="ignore",
    )

    def get_project_path(self, project_name: Optional[str] = None) -> Path:  # pragma: no cover
        """Get the path for a specific project or the default project."""
        name = project_name or self.default_project

        if name not in self.projects:
            raise ValueError(f"Project '{name}' not found in configuration")

        return Path(self.projects[name].path)

    def model_post_init(self, __context: Any) -> None:
        """Ensure configuration is valid after initialization."""
        # Trigger: no projects configured (fresh install or empty config)
        # Why: every config needs at least one project to be functional
        # Outcome: creates "main" project using BASIC_MEMORY_HOME or ~/memoryhub
        if not self.projects:
            self.projects["main"] = ProjectEntry(
                path=str(Path(os.getenv("BASIC_MEMORY_HOME", Path.home() / "memoryhub")))
            )

        # Trigger: default_project was not explicitly provided in the input data
        #          (config file omitted the key, or BasicMemoryConfig() called with no args)
        # Why: callers like get_project_config() expect a valid project name;
        #      but explicit None (discovery mode) must be preserved
        # Outcome: sets default_project to the first available project
        if "default_project" not in self.model_fields_set:
            self.default_project = next(iter(self.projects.keys()))
        # Trigger: default_project was explicitly set but references a non-existent project
        # Why: project may have been removed or renamed since config was saved
        # Outcome: corrects to the first available project
        elif self.default_project is not None and self.default_project not in self.projects:
            self.default_project = next(iter(self.projects.keys()))

    @property
    def app_database_path(self) -> Path:
        """Get the path to the app-level database.

        This is the single database that will store all knowledge data
        across all projects.

        Uses BASIC_MEMORY_CONFIG_DIR when set so each process/worktree can
        isolate both config and database state.
        """
        database_path = self.data_dir_path / APP_DATABASE_NAME
        if not database_path.exists():  # pragma: no cover
            database_path.parent.mkdir(parents=True, exist_ok=True)
            database_path.touch()
        return database_path

    @property
    def database_path(self) -> Path:
        """Get SQLite database path.

        Rreturns the app-level database path
        for backward compatibility in the codebase.
        """

        # Load the app-level database path from the global config
        config_manager = ConfigManager()
        config = config_manager.load_config()  # pragma: no cover
        return config.app_database_path  # pragma: no cover

    @property
    def project_list(self) -> List[ProjectConfig]:  # pragma: no cover
        """Get all configured projects as ProjectConfig objects."""
        return [ProjectConfig(name=name, home=Path(entry.path)) for name, entry in self.projects.items()]

    @model_validator(mode="after")
    def ensure_project_paths_exists(self) -> "BasicMemoryConfig":  # pragma: no cover
        """Ensure configured local project paths exist."""

        for name, entry in self.projects.items():
            path = Path(entry.path)
            # Skip malformed legacy entries whose path is still not a local directory
            if not path.is_absolute():
                continue
            if not path.exists():
                try:
                    path.mkdir(parents=True)
                except Exception as e:
                    logger.error(f"Failed to create project path: {e}")
                    raise e
        return self

    @property
    def data_dir_path(self) -> Path:
        """Get app state directory for config and default SQLite database."""
        if config_dir := os.getenv("BASIC_MEMORY_CONFIG_DIR"):
            return Path(config_dir)

        home = os.getenv("HOME", Path.home())
        return Path(home) / DATA_DIR_NAME


# Module-level cache for configuration
_CONFIG_CACHE: Optional[BasicMemoryConfig] = None


class ConfigManager:
    """Manages MemoryHub configuration."""

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        home = os.getenv("HOME", Path.home())
        if isinstance(home, str):
            home = Path(home)

        # Allow override via environment variable
        if config_dir := os.getenv("BASIC_MEMORY_CONFIG_DIR"):
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = home / DATA_DIR_NAME

        self.config_file = self.config_dir / CONFIG_FILE_NAME

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

    @property
    def config(self) -> BasicMemoryConfig:
        """Get configuration, loading it lazily if needed."""
        return self.load_config()

    def load_config(self) -> BasicMemoryConfig:
        """Load configuration from file or create default.

        Environment variables take precedence over file config values,
        following Pydantic Settings best practices.

        Uses module-level cache for performance across ConfigManager instances.
        """
        global _CONFIG_CACHE

        # Return cached config if available
        if _CONFIG_CACHE is not None:
            return _CONFIG_CACHE

        if self.config_file.exists():
            try:
                file_data = json.loads(self.config_file.read_text(encoding="utf-8"))

                # Detect legacy format before model validators strip stale keys
                _STALE_KEYS = {
                    "default_project_mode",
                    "project_modes",
                    "cloud_projects",
                    "cloud_mode",
                    "cloud_client_id",
                    "cloud_domain",
                    "cloud_host",
                    "cloud_promo_opt_out",
                    "cloud_promo_first_run_shown",
                    "cloud_promo_last_version_shown",
                    "cloud_api_key",
                    "default_workspace",
                }
                needs_resave = bool(_STALE_KEYS & file_data.keys())

                # Check if projects dict uses old string-value format
                projects_raw = file_data.get("projects", {})
                if projects_raw:
                    first_val = next(iter(projects_raw.values()), None)
                    if isinstance(first_val, str):
                        needs_resave = True

                # Check if any project still carries legacy cloud-era project metadata.
                if not needs_resave:
                    for entry_data in projects_raw.values():
                        if isinstance(entry_data, dict):
                            if any(
                                key in entry_data
                                for key in (
                                    "mode",
                                    "workspace_id",
                                    "local_sync_path",
                                    "cloud_sync_path",
                                    "bisync_initialized",
                                    "last_sync",
                                )
                            ):
                                needs_resave = True
                                break
                            lsp = entry_data.get("local_sync_path")
                            p = entry_data.get("path", "")
                            if lsp and not os.path.isabs(p):
                                needs_resave = True
                                break

                # First, create config from environment variables (Pydantic will read them)
                # Then overlay with file data for fields that aren't set via env vars
                # This ensures env vars take precedence

                # Get env-based config fields that are actually set
                env_config = BasicMemoryConfig()
                env_dict = env_config.model_dump()

                # Merge: file data as base, but only use it for fields not set by env
                # We detect env-set fields by comparing to default values
                merged_data = file_data.copy()

                # For fields that have env var overrides, use those instead of file values
                # The env_prefix is "BASIC_MEMORY_" so we check those
                for field_name in BasicMemoryConfig.model_fields.keys():
                    env_var_name = f"BASIC_MEMORY_{field_name.upper()}"
                    if env_var_name in os.environ:
                        # Environment variable is set, use it
                        merged_data[field_name] = env_dict[field_name]

                _CONFIG_CACHE = BasicMemoryConfig(**merged_data)

                # Re-save to normalize legacy config into current format
                if needs_resave:
                    logger.info("Migrating config to current format")
                    save_memoryhub_config(self.config_file, _CONFIG_CACHE)

                return _CONFIG_CACHE
            except json.JSONDecodeError as e:  # pragma: no cover
                logger.error(f"Invalid JSON in config file {self.config_file}: {e}")
                raise SystemExit(
                    f"Error: config file is not valid JSON: {self.config_file}\n"
                    f"  {e}\n"
                    f"Fix or delete the file and re-run."
                )
            except Exception as e:  # pragma: no cover
                logger.error(f"Failed to load config from {self.config_file}: {e}")
                raise SystemExit(
                    f"Error: failed to load config from {self.config_file}\n"
                    f"  {e}\n"
                    f"Fix or delete the file and re-run."
                )
        else:
            config = BasicMemoryConfig()
            self.save_config(config)
            return config

    def save_config(self, config: BasicMemoryConfig) -> None:
        """Save configuration to file and invalidate cache."""
        global _CONFIG_CACHE
        save_memoryhub_config(self.config_file, config)
        # Invalidate cache so next load_config() reads fresh data
        _CONFIG_CACHE = None

    @property
    def projects(self) -> Dict[str, str]:
        """Get all configured projects as name -> path mapping.

        Returns the legacy Dict[str, str] format for backward compatibility
        with code that expects project name -> filesystem path.
        """
        return {name: entry.path for name, entry in self.config.projects.items()}

    @property
    def default_project(self) -> Optional[str]:
        """Get the default project name."""
        return self.config.default_project

    def add_project(self, name: str, path: str) -> ProjectConfig:
        """Add a new project to the configuration."""
        project_name, _ = self.get_project(name)
        if project_name:  # pragma: no cover
            raise ValueError(f"Project '{name}' already exists")

        # Load config, modify it, and save it
        project_path = Path(path)
        config = self.load_config()
        config.projects[name] = ProjectEntry(path=str(project_path))
        self.save_config(config)
        return ProjectConfig(name=name, home=project_path)

    def remove_project(self, name: str) -> None:
        """Remove a project from the configuration."""

        project_name, path = self.get_project(name)
        if not project_name:  # pragma: no cover
            raise ValueError(f"Project '{name}' not found")

        # Load config, check, modify, and save
        config = self.load_config()
        if project_name == config.default_project:  # pragma: no cover
            raise ValueError(f"Cannot remove the default project '{name}'")

        # Use the found project_name (which may differ from input name due to permalink matching)
        del config.projects[project_name]
        self.save_config(config)

    def set_default_project(self, name: str) -> None:
        """Set the default project."""
        project_name, path = self.get_project(name)
        if not project_name:  # pragma: no cover
            raise ValueError(f"Project '{name}' not found")

        # Load config, modify, and save
        config = self.load_config()
        config.default_project = project_name
        self.save_config(config)

    def get_project(self, name: str) -> Tuple[str, str] | Tuple[None, None]:
        """Look up a project from the configuration by name or permalink.

        Returns (project_name, path_string) for backward compatibility.
        """
        project_permalink = generate_permalink(name)
        app_config = self.config
        for project_name, entry in app_config.projects.items():
            if project_permalink == generate_permalink(project_name):
                return project_name, entry.path
        return None, None


def get_project_config(project_name: Optional[str] = None) -> ProjectConfig:
    """
    Get the project configuration for the current session.
    If project_name is provided, it will be used instead of the default project.
    """

    actual_project_name = None

    # load the config from file
    config_manager = ConfigManager()
    app_config = config_manager.load_config()

    # BASIC_MEMORY_PROJECT is retained only as an unsupported compatibility env var.
    # Ignore it so explicit args and config-driven defaults continue to work predictably.
    os_project_name = os.environ.get("BASIC_MEMORY_PROJECT", None)
    if os_project_name:  # pragma: no cover
        logger.warning(
            "BASIC_MEMORY_PROJECT is unsupported and ignored. "
            "Set the default project in config or pass an explicit project name."
        )
    # if the project_name is passed in, use it
    if not project_name:
        # use default
        actual_project_name = app_config.default_project
    else:  # pragma: no cover
        actual_project_name = project_name

    # the config contains a dict[str,str] of project names and absolute paths
    assert actual_project_name is not None, "actual_project_name cannot be None"

    project_permalink = generate_permalink(actual_project_name)

    for name, entry in app_config.projects.items():
        if project_permalink == generate_permalink(name):
            return ProjectConfig(name=name, home=Path(entry.path))

    # otherwise raise error
    raise ValueError(f"Project '{actual_project_name}' not found")  # pragma: no cover


def save_memoryhub_config(file_path: Path, config: BasicMemoryConfig) -> None:
    """Save configuration to file."""
    try:
        # Use model_dump with mode='json' to serialize datetime objects properly
        config_dict = config.model_dump(mode="json")
        file_path.write_text(json.dumps(config_dict, indent=2))
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to save config: {e}")


# Logging initialization functions for different entry points


def init_cli_logging() -> None:  # pragma: no cover
    """Initialize logging for CLI commands - file only.

    CLI commands should not log to stdout to avoid interfering with
    command output and shell integration.
    """
    log_level = os.getenv("BASIC_MEMORY_LOG_LEVEL", "INFO")
    setup_logging(log_level=log_level, log_to_file=True)


def init_mcp_logging() -> None:  # pragma: no cover
    """Initialize logging for MCP server - file only.

    MCP server must not log to stdout as it would corrupt the
    JSON-RPC protocol communication.
    """
    log_level = os.getenv("BASIC_MEMORY_LOG_LEVEL", "INFO")
    setup_logging(log_level=log_level, log_to_file=True)


def init_api_logging() -> None:  # pragma: no cover
    """Initialize logging for the local API server."""
    log_level = os.getenv("BASIC_MEMORY_LOG_LEVEL", "INFO")
    setup_logging(log_level=log_level, log_to_file=True)
