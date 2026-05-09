from fastapi import Depends, FastAPI

from src.presentation.api.auth.dependencies import get_current_user
from src.presentation.api.handlers.annotation_api_route_handler import router as annotation_router
from src.presentation.api.handlers.book_api_route_handler import router as book_router
from src.presentation.api.handlers.chat_api_route_handler import router as chat_router
from src.presentation.api.handlers.message_api_route_handler import router as message_router
from src.presentation.api.handlers.podcast_api_route_handler import router as podcast_router
from src.presentation.api.handlers.rag_api_route_handler import router as rag_router


def setup_routes(app: FastAPI) -> None:
    # CR-1: 全ルーターに認証 Depends を強制適用。匿名アクセスを排除する。
    auth_dep = [Depends(get_current_user)]

    app.include_router(message_router, prefix="/messages", tags=["messages"], dependencies=auth_dep)
    app.include_router(rag_router, prefix="/rag", tags=["rag"], dependencies=auth_dep)
    app.include_router(book_router, prefix="/books", tags=["books"], dependencies=auth_dep)
    app.include_router(annotation_router, prefix="/books/{book_id}/annotations", tags=["annotations"], dependencies=auth_dep)
    app.include_router(chat_router, prefix="/chats", tags=["chats"], dependencies=auth_dep)
    app.include_router(podcast_router, prefix="/podcasts", tags=["podcasts"], dependencies=auth_dep)
