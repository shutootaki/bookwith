from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import StreamingResponse

from src.domain.message.exceptions.message_exceptions import (
    MessageNotFoundException,
)
from src.infrastructure.di.injection import (
    get_create_message_usecase,
    get_delete_message_usecase,
    get_find_message_by_id_usecase,
    get_find_messages_usecase,
)
from src.presentation.api.error_messages.message_error_message import MessageErrorMessage
from src.presentation.api.schemas.message_schema import (
    MessageBulkDelete,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
)
from src.usecase.message.create_message_usecase import CreateMessageUseCase
from src.usecase.message.delete_message_usecase import DeleteMessageUseCase
from src.usecase.message.find_message_by_id_usecase import FindMessageByIdUseCase
from src.usecase.message.find_messages_usecase import FindMessagesUseCase

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("", response_model=MessageListResponse)
async def get_all_messages(
    skip: int = Query(0, description="Skip records"),
    limit: int = Query(100, description="Limit records"),
    find_messages_usecase: FindMessagesUseCase = Depends(get_find_messages_usecase),
) -> dict[str, Any]:
    """全てのメッセージを取得する."""
    messages = find_messages_usecase.execute_find_all()
    total = len(messages)

    messages = messages[skip : skip + limit]

    return {
        "data": [message.model_dump() for message in messages],
        "total": total,
    }


@router.get("/{chat_id}", response_model=MessageListResponse)
async def get_messages_by_chat_id(
    chat_id: str = Path(..., description="メッセージを検索するチャットID"),
    find_messages_usecase: FindMessagesUseCase = Depends(get_find_messages_usecase),
) -> dict[str, Any]:
    """チャットIDでメッセージを検索する."""
    messages = find_messages_usecase.execute_find_by_chat_id(chat_id)

    return {
        "data": [message.model_dump() for message in messages],
        "total": len(messages),
    }


@router.get("/sender/{sender_id}", response_model=MessageListResponse)
async def get_messages_by_sender_id(
    sender_id: str = Path(..., description="メッセージを検索する送信者ID"),
    find_messages_usecase: FindMessagesUseCase = Depends(get_find_messages_usecase),
) -> dict[str, Any]:
    """送信者IDでメッセージを検索する."""
    messages = find_messages_usecase.execute_find_by_sender_id(sender_id)

    return {
        "data": [message.model_dump() for message in messages],
        "total": len(messages),
    }


@router.get("/id/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str = Path(..., description="取得するメッセージID"),
    find_message_usecase: FindMessageByIdUseCase = Depends(get_find_message_by_id_usecase),
) -> dict[str, Any]:
    """IDでメッセージを取得する."""
    try:
        message = find_message_usecase.execute(message_id)
        return message.model_dump()
    except MessageNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MessageErrorMessage.MESSAGE_NOT_FOUND,
        )


@router.post("", status_code=status.HTTP_200_OK)
async def stream_create_message(
    message_create: MessageCreate,
    create_message_usecase: CreateMessageUseCase = Depends(get_create_message_usecase),
) -> StreamingResponse:
    """新しいメッセージを作成し、AI の応答をストリーミングで返す."""
    try:
        response_stream = create_message_usecase.execute(
            content=message_create.content,
            sender_id=message_create.sender_id,
            chat_id=message_create.chat_id,
            book_id=message_create.book_id,
            metadata=message_create.metadata,
        )
        return StreamingResponse(response_stream, media_type="text/event-stream")  # type: ignore
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{MessageErrorMessage.MESSAGE_CREATE_FAILED} {str(e)}",
        )


@router.delete("/{message_id}", status_code=status.HTTP_200_OK)
async def delete_message(
    message_id: str = Path(..., description="削除するメッセージID"),
    delete_message_usecase: DeleteMessageUseCase = Depends(get_delete_message_usecase),
) -> dict[str, str]:
    """メッセージを削除する."""
    try:
        delete_message_usecase.execute(message_id)
        return {"status": "success"}
    except MessageNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MessageErrorMessage.MESSAGE_NOT_FOUND,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{MessageErrorMessage.MESSAGE_DELETE_FAILED} {str(e)}",
        )


@router.delete("/bulk", status_code=status.HTTP_200_OK)
async def bulk_delete_messages(
    message_bulk_delete: MessageBulkDelete,
    delete_message_usecase: DeleteMessageUseCase = Depends(get_delete_message_usecase),
) -> dict[str, list[str]]:
    """複数のメッセージを一括削除する."""
    try:
        failed_ids = delete_message_usecase.execute_bulk(message_bulk_delete.message_ids)
        return {"failed_ids": failed_ids}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{MessageErrorMessage.MESSAGE_DELETE_FAILED} {str(e)}",
        )
