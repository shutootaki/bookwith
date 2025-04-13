import logging
from collections.abc import Generator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.application.error_handlers import setup_exception_handlers
from src.db import get_db, init_db
from src.presentation.api import setup_routes

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# FastAPIアプリケーションの作成
app = FastAPI(title="BookWith API", description="Book related API service")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンに制限すべき
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_db_client() -> None:
    try:
        init_db()
        logging.info("データベース接続が確立されました")
    except Exception as e:
        logging.error(f"データベース初期化エラー: {e}")


@app.on_event("shutdown")
async def shutdown_db_client() -> None:
    logging.info("データベース接続を閉じています")


def get_db_session() -> Generator[Session]:
    with get_db() as session:
        yield session


# ルートのセットアップ
setup_routes(app)

# エラーハンドラーのセットアップ
setup_exception_handlers(app)
