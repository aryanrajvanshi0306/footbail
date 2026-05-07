"""Alembic env — async-aware. Uses DATABASE_URL from env, falls back to alembic.ini."""
from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, engine_from_config
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all models so Base.metadata is populated
from app.models.base import Base
import app.models  # noqa: F401  — ensures all 18 model files register their tables

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from env (12-factor)
db_url = os.environ.get("DATABASE_URL")
if db_url:
    # Alembic uses sync engine for offline mode; flip asyncpg → psycopg2 if needed
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    """Skip alembic-internal tables, optionally exclude tables that aren't in our metadata."""
    if type_ == "table" and name.startswith("alembic_"):
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True,
        dialect_opts={"paramstyle": "named"}, include_object=include_object,
        compare_type=True, compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True, compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")
    # Use asyncpg if url is async; else fall back to sync engine.
    if "+asyncpg" in cfg["sqlalchemy.url"]:
        connectable = async_engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()
    else:
        connectable = engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)
        with connectable.connect() as connection:
            do_run_migrations(connection)


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
