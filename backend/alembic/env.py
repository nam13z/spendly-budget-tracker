"""Alembic environment using Spendly's validated root .env configuration."""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

import app.db.models  # noqa: F401 - register all mapped tables before autogeneration
from alembic import context
from app.core.config import get_settings
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(
    object_: object, name: str | None, type_: str, reflected: bool, compare_to: object | None
) -> bool:
    """Keep FX outside metadata/migrations until its precision is approved."""
    del object_, reflected, compare_to
    return not (type_ == "table" and name == "fx_rates")


def run_migrations_offline() -> None:
    """Render SQL without opening a database connection or exposing a password."""
    safe_url = get_settings().sqlalchemy_url.render_as_string(hide_password=True)
    context.configure(
        url=safe_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations through a short-lived engine from the root .env settings."""
    engine = create_engine(get_settings().sqlalchemy_url, poolclass=NullPool, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                include_object=include_object,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
