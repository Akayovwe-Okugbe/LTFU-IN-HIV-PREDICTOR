"""
=========================================================
Alembic Migration Environment

MEDISCOPE
LTFU Prediction in HIV Treatment Programmes

Purpose:
    Configure Alembic to:

    - load the PostgreSQL connection URL from .env;
    - discover the MEDISCOPE SQLAlchemy models;
    - compare model metadata with the current database;
    - generate and apply version-controlled migrations.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.core.config import get_settings
from app.db.base import Base

# Import the model package so that every mapped table is
# registered in Base.metadata before Alembic performs its
# autogeneration comparison.
import app.models  # noqa: F401


# =====================================================
# ALEMBIC CONFIGURATION
# =====================================================

config = context.config

# Configure Python logging from alembic.ini when the
# configuration file contains logging sections.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# =====================================================
# DATABASE CONNECTION URL
# =====================================================

settings = get_settings()

# Alembic uses ConfigParser internally. A percent sign in
# a URL must be escaped to prevent interpolation errors.
database_url = settings.database_url.replace("%", "%%")

config.set_main_option(
    "sqlalchemy.url",
    database_url,
)


# =====================================================
# SQLALCHEMY MODEL METADATA
# =====================================================

# Alembic compares this metadata against the live
# PostgreSQL database during --autogenerate.
target_metadata = Base.metadata


# =====================================================
# OFFLINE MIGRATIONS
# =====================================================

def run_migrations_offline() -> None:
    """
    Runs migrations without creating a live database
    connection.

    SQL statements are written to the migration output
    rather than being executed directly.
    """

    url = config.get_main_option(
        "sqlalchemy.url"
    )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# =====================================================
# ONLINE MIGRATIONS
# =====================================================

def run_migrations_online() -> None:
    """
    Runs migrations using a live PostgreSQL connection.
    """

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# =====================================================
# MIGRATION EXECUTION MODE
# =====================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
