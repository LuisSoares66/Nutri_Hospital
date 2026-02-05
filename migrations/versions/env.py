from __future__ import with_statement

import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

# ======================================================
# CONFIGURAÇÃO DE LOG
# ======================================================
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# ======================================================
# METADATA DO SQLALCHEMY (CRÍTICO)
# ======================================================
from app import db  # <<< IMPORTA O DB DO APP
target_metadata = db.metadata


# ======================================================
# FUNÇÃO: MIGRAÇÃO OFFLINE
# ======================================================
def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = current_app.config.get("SQLALCHEMY_DATABASE_URI")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ======================================================
# FUNÇÃO: MIGRAÇÃO ONLINE
# ======================================================
def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = current_app.extensions["sqlalchemy"].engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ======================================================
# EXECUÇÃO
# ======================================================
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
