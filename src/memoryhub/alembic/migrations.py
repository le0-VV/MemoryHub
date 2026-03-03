"""Functions for managing database migrations."""

from pathlib import Path

from alembic.config import Config
from alembic import command
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool


def get_alembic_config() -> Config:  # pragma: no cover
    """Get alembic config with correct paths."""
    migrations_path = Path(__file__).parent
    alembic_ini = migrations_path / "alembic.ini"

    config = Config(alembic_ini)
    config.set_main_option("script_location", str(migrations_path))
    return config


def create_migration_connectable(url: str) -> AsyncEngine:
    """Create the supported async migration engine for MemoryHub."""
    if not url:
        raise ValueError("Missing sqlalchemy.url for MemoryHub migrations.")
    if not url.startswith("sqlite"):
        raise ValueError(
            "MemoryHub migrations support SQLite URLs only. "
            "Use sqlite+aiosqlite or unset the explicit database URL."
        )
    return create_async_engine(url, poolclass=NullPool, future=True)


def reset_database():  # pragma: no cover
    """Drop and recreate all tables."""
    logger.info("Resetting database...")
    config = get_alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")
