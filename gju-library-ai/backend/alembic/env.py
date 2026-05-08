from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app.config import get_settings
from app.db import Base
from app.models import (  # noqa: F401  (registers tables on Base.metadata)
    click_event,
    feedback_event,
    passage,
    query_log,
    session,
    subscription_database,
    user,
)

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
