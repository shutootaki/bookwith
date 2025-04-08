import logging
from contextlib import contextmanager

from config.app_config import AppConfig
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 設定の取得
config = AppConfig()


# エンジンの作成
engine = create_engine(config.database_url, echo=True)

# セッションの設定
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデルのベースクラス
Base = declarative_base()


@contextmanager
def get_db():
    """データベースセッションを取得するコンテキストマネージャー"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """データベーステーブルを初期化する関数"""
    try:
        # モデル定義に基づいてテーブルを作成
        Base.metadata.create_all(bind=engine)
        logging.info("データベーステーブルが正常に初期化されました")
    except Exception as e:
        logging.error(f"データベース初期化中にエラーが発生しました: {str(e)}")
        raise
