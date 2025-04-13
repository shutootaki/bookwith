from fastapi import FastAPI

from src.presentation.api.endpoints import (
    llm_router,
    rag_router,
    root_router,
)
from src.presentation.api.handlers.book_api_route_handler import router as book_router


def setup_routes(app: FastAPI) -> None:
    app.include_router(root_router)

    app.include_router(llm_router)
    app.include_router(rag_router)
    app.include_router(book_router)
