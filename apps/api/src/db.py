import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from src.config.app_config import AppConfig

# 設定の取得
config = AppConfig()


# エンジンの作成
engine = create_engine(config.database_url, echo=True)

# セッションの設定
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデルのベースクラス
Base = declarative_base()


def get_db() -> Generator[Session]:
    """データベースセッションを取得するコンテキストマネージャー."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # 未参照なので一時的にimportしておく
    from src.infrastructure.postgres.annotation import annotation_dto  # noqa: F401

    try:
        Base.metadata.create_all(bind=engine)
        logging.info("データベーステーブルが正常に初期化されました")
    except Exception as e:
        logging.error(f"データベース初期化中にエラーが発生しました: {str(e)}")
        raise


__all__ = ["Base", "get_db", "init_db", "engine", "SessionLocal"]
