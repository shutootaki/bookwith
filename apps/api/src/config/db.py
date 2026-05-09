import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config.app_config import AppConfig

config = AppConfig.get_config()


# H-6: 本番では echo=False。SQL_ECHO=true の時のみクエリと bind パラメータがログに出力される。
engine = create_engine(config.database_url, echo=config.sql_echo)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """テーブル初期化.

    M-15: 本番環境では `Base.metadata.create_all` を呼ばない。スキーマは Supabase
    migration / Alembic で管理する想定。AppConfig.sqlalchemy_auto_create=true を
    明示した場合のみ開発時の利便性として create_all を呼び出す。
    """
    if config.is_production:
        logging.info("Skipping create_all in production environment")
        return

    if not config.sqlalchemy_auto_create:
        logging.info("Skipping create_all because SQLALCHEMY_AUTO_CREATE=false")
        return

    try:
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables initialized successfully")
    except Exception as e:
        logging.error(f"Error occurred during database initialization: {str(e)}", exc_info=True)
        raise
