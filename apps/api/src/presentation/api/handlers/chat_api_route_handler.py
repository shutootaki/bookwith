import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from src.domain.chat.exceptions.chat_exceptions import (
    ChatNotFoundError,
    ChatPermissionDeniedError,
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
    get_find_chats_by_user_id_and_book_id_usecase,
    get_find_chats_by_user_id_usecase,
    get_update_chat_title_usecase,
)
from src.presentation.api.auth import require_user_id
from src.presentation.api.error_messages.chat_error_message import ChatErrorMessage
from src.presentation.api.schemas.chat_schema import (
    ChatCreateRequest,
    ChatResponse,
    ChatsResponse,
    ChatUpdateTitleRequest,
)
from src.usecase.chat.create_chat_usecase import CreateChatUseCase
from src.usecase.chat.delete_chat_usecase import DeleteChatUseCase
from src.usecase.chat.find_chat_by_id_usecase import FindChatByIdUseCase
from src.usecase.chat.find_chats_by_user_id_and_book_id_usecase import FindChatsByUserIdAndBookIdUseCase
from src.usecase.chat.find_chats_by_user_id_usecase import FindChatsByUserIdUseCase
from src.usecase.chat.update_chat_title_usecase import UpdateChatTitleUseCase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    request: ChatCreateRequest,
    user_id_str: str = Depends(require_user_id),
    create_chat_usecase: CreateChatUseCase = Depends(get_create_chat_usecase),
):
    """チャットを作成する."""
    try:
        # CR-4: 認証 user_id を強制使用
        user_id = UserId(value=user_id_str)
        title = ChatTitle(value=request.title or "Untitled")
        book_id = BookId(value=request.book_id) if request.book_id else None

        chat = create_chat_usecase.execute(
            user_id=user_id,
            title=title,
            book_id=book_id,
        )

        return ChatResponse.from_entity(chat)
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


@router.get("/me", response_model=ChatsResponse)
async def get_my_chats(
    user_id_str: str = Depends(require_user_id),
    find_chats_by_user_id_usecase: FindChatsByUserIdUseCase = Depends(get_find_chats_by_user_id_usecase),
) -> ChatsResponse:
    """認証ユーザーのチャット一覧を取得する."""
    try:
        chats = find_chats_by_user_id_usecase.execute(UserId(value=user_id_str))

        return ChatsResponse(chats=[ChatResponse.from_entity(chat) for chat in chats])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ChatErrorMessage.USER_ID_INVALID,
        )


@router.get("/me/book/{book_id}", response_model=list[ChatResponse])
async def get_my_chats_by_book_id(
    book_id: str,
    user_id_str: str = Depends(require_user_id),
    find_chats_by_user_id_and_book_id_usecase: FindChatsByUserIdAndBookIdUseCase = Depends(get_find_chats_by_user_id_and_book_id_usecase),
):
    """認証ユーザーが所有する特定の本のチャット一覧を取得する."""
    try:
        chats = find_chats_by_user_id_and_book_id_usecase.execute(UserId(value=user_id_str), BookId(value=book_id))
        return [ChatResponse.from_entity(chat) for chat in chats]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ChatErrorMessage.USER_ID_INVALID,
        )


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat_by_id(
    chat_id: str,
    user_id_str: str = Depends(require_user_id),
    find_chat_by_id_usecase: FindChatByIdUseCase = Depends(get_find_chat_by_id_usecase),
):
    """IDでチャットを取得する."""
    try:
        chat = find_chat_by_id_usecase.execute(ChatId(value=chat_id), UserId(value=user_id_str))

        return ChatResponse.from_entity(chat)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ChatErrorMessage.CHAT_ID_INVALID,
        )
    except ChatPermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ChatErrorMessage.CHAT_ACCESS_DENIED,
        )
    except ChatNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ChatErrorMessage.CHAT_NOT_FOUND,
        )


@router.patch("/{chat_id}/title", response_model=ChatResponse)
async def update_chat_title(
    chat_id: str,
    request: ChatUpdateTitleRequest,
    user_id_str: str = Depends(require_user_id),
    find_chat_by_id_usecase: FindChatByIdUseCase = Depends(get_find_chat_by_id_usecase),
    update_chat_title_usecase: UpdateChatTitleUseCase = Depends(get_update_chat_title_usecase),
):
    """チャットのタイトルを更新する."""
    try:
        chat_id_obj = ChatId(value=chat_id)
        title = ChatTitle(value=request.title)
        user_id_obj = UserId(value=user_id_str)

        # 所有者検証込みで更新
        update_chat_title_usecase.execute(chat_id=chat_id_obj, title=title, user_id=user_id_obj)

        chat = find_chat_by_id_usecase.execute(chat_id_obj, user_id_obj)

        return ChatResponse.from_entity(chat)
    except ChatPermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ChatErrorMessage.CHAT_ACCESS_DENIED,
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
    user_id_str: str = Depends(require_user_id),
    delete_chat_usecase: DeleteChatUseCase = Depends(get_delete_chat_usecase),
):
    """チャットを削除する."""
    try:
        delete_chat_usecase.execute(ChatId(value=chat_id), UserId(value=user_id_str))
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
    except ChatPermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ChatErrorMessage.CHAT_ACCESS_DENIED,
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
