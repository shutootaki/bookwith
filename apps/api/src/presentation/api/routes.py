from fastapi import FastAPI

from src.presentation.api.handlers.book_api_route_handler import router as book_router
from src.presentation.api.handlers.chat_api_route_handler import router as chat_router
from src.presentation.api.handlers.message_api_route_handler import router as message_router
from src.presentation.api.handlers.rag_api_route_handler import router as rag_router


def setup_routes(app: FastAPI) -> None:
    app.include_router(message_router)
    app.include_router(rag_router)
    app.include_router(book_router)
    app.include_router(chat_router)
