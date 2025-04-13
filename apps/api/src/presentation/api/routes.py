from fastapi import FastAPI
from src.presentation.api.endpoints import (
    auth_router,
    book_router,
    llm_router,
    rag_router,
    root_router,
)


def setup_routes(app: FastAPI) -> None:
    """APIルーターをアプリケーションに設定する関数"""
    # ルートルーターを追加
    app.include_router(root_router)

    # 機能別ルーターを追加
    app.include_router(llm_router)
    app.include_router(rag_router)
    app.include_router(auth_router)
    app.include_router(book_router)
    app.include_router(root_router)
