"""Alembic 環境設定.

M-15: 本番ではこちらでスキーマを管理する。
DATABASE_URL は AppConfig から取得し、`Base.metadata` をターゲットメタデータとして使う。
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.config.app_config import AppConfig
from src.config.db import Base

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# AppConfig 経由で DATABASE_URL を取得し、ini の値を上書きする。
_app_config = AppConfig.get_config()
config.set_main_option("sqlalchemy.url", _app_config.database_url)

# モデルメタデータをまとめて読み込むため、副作用 import を行う。
# noqa: F401 を使い、未使用警告を抑止しながら register する。
from src.infrastructure.postgres.annotation.annotation_dto import AnnotationDTO  # noqa: E402,F401
from src.infrastructure.postgres.book.book_dto import BookDTO  # noqa: E402,F401
from src.infrastructure.postgres.chat.chat_dto import ChatDTO  # noqa: E402,F401
from src.infrastructure.postgres.message.message_dto import MessageDTO  # noqa: E402,F401
from src.infrastructure.postgres.podcast.podcast_dto import PodcastDTO  # noqa: E402,F401
from src.infrastructure.postgres.user.user_dto import UserDTO  # noqa: E402,F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
