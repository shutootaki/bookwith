from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from src.domain.chat.exceptions.chat_exceptions import (
    ChatNotFoundError,
    ChatValidationError,
)
from src.domain.chat.value_objects.book_id import BookId
from src.domain.chat.value_objects.chat_id import ChatId
from src.domain.chat.value_objects.chat_title import ChatTitle
from src.domain.chat.value_objects.user_id import UserId
from src.infrastructure.di.injection import (
    get_create_chat_usecase,
    get_delete_chat_usecase,
    get_find_chat_by_id_usecase,
    get_find_chats_by_user_id_usecase,
    get_update_chat_title_usecase,
)
from src.presentation.api.error_messages.chat_error_message import ChatErrorMessage
from src.presentation.api.schemas.chat_schema import (
    ChatCreateRequest,
    ChatResponse,
    ChatUpdateTitleRequest,
)
from src.usecase.chat.create_chat_usecase import CreateChatUseCase
from src.usecase.chat.delete_chat_usecase import DeleteChatUseCase
from src.usecase.chat.find_chat_by_id_usecase import FindChatByIdUseCase
from src.usecase.chat.find_chats_by_user_id_usecase import FindChatsByUserIdUseCase
from src.usecase.chat.update_chat_title_usecase import UpdateChatTitleUseCase

router = APIRouter(
    prefix="/chats",
    tags=["chats"],
)


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    request: ChatCreateRequest,
    create_chat_usecase: CreateChatUseCase = Depends(get_create_chat_usecase),
):
    """チャットを作成する"""
    try:
        user_id = UserId(value=request.user_id)
        title = ChatTitle(value=request.title) if request.title else None
        book_id = BookId(value=request.book_id) if request.book_id else None

        chat = create_chat_usecase.execute(
            user_id=user_id,
            title=title,
            book_id=book_id,
        )

        return ChatResponse(
            id=chat.id.value,
            user_id=chat.user_id.value,
            title=chat.title.value if chat.title else None,
            book_id=chat.book_id.value if chat.book_id else None,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ChatValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat_by_id(
    chat_id: str,
    find_chat_by_id_usecase: FindChatByIdUseCase = Depends(get_find_chat_by_id_usecase),
):
    """IDでチャットを取得する"""
    try:
        chat = find_chat_by_id_usecase.execute(ChatId(value=chat_id))

        return ChatResponse(
            id=chat.id.value,
            user_id=chat.user_id.value,
            title=chat.title.value if chat.title else None,
            book_id=chat.book_id.value if chat.book_id else None,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ChatErrorMessage.CHAT_ID_INVALID,
        )
    except ChatNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ChatErrorMessage.CHAT_NOT_FOUND,
        )


@router.get("/user/{user_id}", response_model=list[ChatResponse])
async def get_chats_by_user_id(
    user_id: str,
    find_chats_by_user_id_usecase: FindChatsByUserIdUseCase = Depends(get_find_chats_by_user_id_usecase),
):
    """ユーザーIDに紐づくチャットをすべて取得する"""
    try:
        chats = find_chats_by_user_id_usecase.execute(UserId(value=user_id))

        return [
            ChatResponse(
                id=chat.id.value,
                user_id=chat.user_id.value,
                title=chat.title.value if chat.title else None,
                book_id=chat.book_id.value if chat.book_id else None,
                created_at=chat.created_at,
                updated_at=chat.updated_at,
            )
            for chat in chats
        ]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ChatErrorMessage.USER_ID_INVALID,
        )


@router.patch("/{chat_id}/title", response_model=ChatResponse)
async def update_chat_title(
    chat_id: str,
    request: ChatUpdateTitleRequest,
    find_chat_by_id_usecase: FindChatByIdUseCase = Depends(get_find_chat_by_id_usecase),
    update_chat_title_usecase: UpdateChatTitleUseCase = Depends(get_update_chat_title_usecase),
):
    """チャットのタイトルを更新する"""
    try:
        chat_id_obj = ChatId(value=chat_id)
        title = ChatTitle(value=request.title)

        # タイトルを更新
        update_chat_title_usecase.execute(chat_id=chat_id_obj, title=title)

        # 更新後のチャットを取得
        chat = find_chat_by_id_usecase.execute(chat_id_obj)

        return ChatResponse(
            id=chat.id.value,
            user_id=chat.user_id.value,
            title=chat.title.value if chat.title else None,
            book_id=chat.book_id.value if chat.book_id else None,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ChatNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ChatErrorMessage.CHAT_NOT_FOUND,
        )


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    delete_chat_usecase: DeleteChatUseCase = Depends(get_delete_chat_usecase),
):
    """チャットを削除する"""
    try:
        delete_chat_usecase.execute(ChatId(value=chat_id))
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ChatErrorMessage.CHAT_ID_INVALID,
        )
    except ChatNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ChatErrorMessage.CHAT_NOT_FOUND,
        )
