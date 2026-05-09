import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from fastapi.responses import StreamingResponse

from src.domain.chat.exceptions.chat_exceptions import ChatNotFoundError, ChatPermissionDeniedError
from src.domain.chat.value_objects.chat_id import ChatId
from src.domain.chat.value_objects.user_id import UserId
from src.domain.message.exceptions.message_exceptions import (
    MessageNotFoundException,
)
from src.infrastructure.di.injection import (
    get_create_message_usecase,
    get_delete_message_usecase,
    get_find_chat_by_id_usecase,
    get_find_messages_usecase,
)
from src.presentation.api.auth import require_user_id
from src.presentation.api.error_messages.message_error_message import MessageErrorMessage
from src.presentation.api.middleware import expensive_limit
from src.presentation.api.schemas.message_schema import (
    MessageBulkDelete,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
)
from src.usecase.chat.find_chat_by_id_usecase import FindChatByIdUseCase
from src.usecase.message.create_message_usecase import CreateMessageUseCase
from src.usecase.message.delete_message_usecase import DeleteMessageUseCase
from src.usecase.message.find_messages_usecase import FindMessagesUseCase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", status_code=status.HTTP_200_OK)
@expensive_limit()
async def stream_create_message(
    request: Request,
    message_create: MessageCreate,
    user_id: str = Depends(require_user_id),
    find_chat_by_id_usecase: FindChatByIdUseCase = Depends(get_find_chat_by_id_usecase),
    create_message_usecase: CreateMessageUseCase = Depends(get_create_message_usecase),
) -> StreamingResponse:
    """新しいメッセージを作成し、AI の応答をストリーミングで返す."""
    try:
        # CR-3 + H-16: chat の所有者検証を先に実施。
        find_chat_by_id_usecase.execute(ChatId(value=message_create.chat_id), UserId(value=user_id))

        # CR-4: sender_id は認証 user_id から取得する。
        response_stream = create_message_usecase.execute(
            content=message_create.content,
            sender_id=user_id,
            chat_id=message_create.chat_id,
            book_id=message_create.book_id,
            metadata=message_create.metadata,
        )
        return StreamingResponse(response_stream, media_type="text/event-stream")
    except ChatPermissionDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MessageErrorMessage.MESSAGE_NOT_FOUND)
    except ChatNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MessageErrorMessage.MESSAGE_NOT_FOUND)
    except Exception:
        # H-5: 例外メッセージを直接返さない
        logger.exception("Failed to create message")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MessageErrorMessage.MESSAGE_CREATE_FAILED,
        )


# H-11: 静的パスは動的セグメントより先に宣言。
@router.delete("/bulk", status_code=status.HTTP_200_OK)
async def bulk_delete_messages(
    message_bulk_delete: MessageBulkDelete,
    user_id: str = Depends(require_user_id),
    delete_message_usecase: DeleteMessageUseCase = Depends(get_delete_message_usecase),
) -> dict[str, list[str]]:
    """複数のメッセージを一括削除する."""
    try:
        failed_ids = delete_message_usecase.execute_bulk(message_bulk_delete.message_ids, user_id)
        return {"failed_ids": failed_ids}
    except Exception:
        logger.exception("Failed to bulk delete messages")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MessageErrorMessage.MESSAGE_DELETE_FAILED,
        )


@router.get("/{chat_id}", response_model=MessageListResponse)
async def get_messages_by_chat_id(
    chat_id: str = Path(..., description="メッセージを検索するチャットID"),
    user_id: str = Depends(require_user_id),
    find_messages_usecase: FindMessagesUseCase = Depends(get_find_messages_usecase),
) -> MessageListResponse:
    """チャットIDでメッセージを検索する（所有者検証込み）."""
    messages = find_messages_usecase.execute_find_by_chat_id(chat_id, user_id)

    return MessageListResponse(
        messages=[
            MessageResponse(
                id=message.id.value,
                content=message.content.value,
                sender_id=message.sender_id,
                sender_type=message.sender_type.value,
                chat_id=message.chat_id,
                created_at=message.created_at,
                metadata=message.metadata,
            )
            for message in messages
        ],
        total=len(messages),
    )


@router.delete("/{message_id}", status_code=status.HTTP_200_OK)
async def delete_message(
    message_id: str = Path(..., description="削除するメッセージID"),
    user_id: str = Depends(require_user_id),
    delete_message_usecase: DeleteMessageUseCase = Depends(get_delete_message_usecase),
) -> dict[str, str]:
    """メッセージを削除する."""
    try:
        delete_message_usecase.execute(message_id, user_id)
        return {"status": "success"}
    except MessageNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MessageErrorMessage.MESSAGE_NOT_FOUND,
        )
    except Exception:
        logger.exception("Failed to delete message")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MessageErrorMessage.MESSAGE_DELETE_FAILED,
        )
