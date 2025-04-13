from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from src.db import get_db
from src.domain.message.exceptions.message_exceptions import (
    MessageNotFoundException,
)
from src.infrastructure.postgres.message.message_repository import MessageRepositoryImpl
from src.presentation.api.error_messages.message_error_message import MessageErrorMessage
from src.presentation.api.schemas.message_schema import (
    MessageBulkDelete,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
)
from src.usecase.message.create_message_usecase import CreateMessageUseCaseImpl
from src.usecase.message.delete_message_usecase import DeleteMessageUseCaseImpl
from src.usecase.message.find_message_by_id_usecase import FindMessageByIdUseCaseImpl
from src.usecase.message.find_messages_usecase import FindMessagesUseCaseImpl

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
)


def _entity_to_response(message: Any) -> dict[str, Any]:
    """メッセージエンティティをレスポンス形式に変換する"""
    return {
        "id": message.id.value,
        "content": message.content.value,
        "sender_id": message.sender_id,
        "chat_id": message.chat_id,
        "created_at": message.created_at,
        "updated_at": message.updated_at,
        "deleted_at": message.deleted_at,
        "metadata": message.metadata,
    }


@router.get("", response_model=MessageListResponse)
async def get_all_messages(
    skip: int = Query(0, description="Skip records"),
    limit: int = Query(100, description="Limit records"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """全てのメッセージを取得する"""
    message_repository = MessageRepositoryImpl(db)
    find_messages_usecase = FindMessagesUseCaseImpl(message_repository)

    messages = find_messages_usecase.execute_find_all()
    total = len(messages)

    messages = messages[skip : skip + limit]

    return {
        "data": [_entity_to_response(message) for message in messages],
        "total": total,
    }


@router.get("/chat/{chat_id}", response_model=MessageListResponse)
async def get_messages_by_chat_id(
    chat_id: str = Path(..., description="メッセージを検索するチャットID"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """チャットIDでメッセージを検索する"""
    message_repository = MessageRepositoryImpl(db)
    find_messages_usecase = FindMessagesUseCaseImpl(message_repository)

    messages = find_messages_usecase.execute_find_by_chat_id(chat_id)

    return {
        "data": [_entity_to_response(message) for message in messages],
        "total": len(messages),
    }


@router.get("/sender/{sender_id}", response_model=MessageListResponse)
async def get_messages_by_sender_id(
    sender_id: str = Path(..., description="メッセージを検索する送信者ID"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """送信者IDでメッセージを検索する"""
    message_repository = MessageRepositoryImpl(db)
    find_messages_usecase = FindMessagesUseCaseImpl(message_repository)

    messages = find_messages_usecase.execute_find_by_sender_id(sender_id)

    return {
        "data": [_entity_to_response(message) for message in messages],
        "total": len(messages),
    }


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str = Path(..., description="取得するメッセージID"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """IDでメッセージを取得する"""
    message_repository = MessageRepositoryImpl(db)
    find_message_usecase = FindMessageByIdUseCaseImpl(message_repository)

    try:
        message = find_message_usecase.execute(message_id)
        return _entity_to_response(message)
    except MessageNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MessageErrorMessage.MESSAGE_NOT_FOUND,
        )


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_create: MessageCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """新しいメッセージを作成する"""
    message_repository = MessageRepositoryImpl(db)
    create_message_usecase = CreateMessageUseCaseImpl(message_repository)

    try:
        message = create_message_usecase.execute(
            content=message_create.content,
            sender_id=message_create.sender_id,
            chat_id=message_create.chat_id,
            metadata=message_create.metadata,
        )
        return _entity_to_response(message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{MessageErrorMessage.MESSAGE_CREATE_FAILED} {str(e)}",
        )


@router.delete("/{message_id}", status_code=status.HTTP_200_OK)
async def delete_message(
    message_id: str = Path(..., description="削除するメッセージID"),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """メッセージを削除する"""
    message_repository = MessageRepositoryImpl(db)
    delete_message_usecase = DeleteMessageUseCaseImpl(message_repository)

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
    db: Session = Depends(get_db),
) -> dict[str, list[str]]:
    """複数のメッセージを一括削除する"""
    message_repository = MessageRepositoryImpl(db)
    delete_message_usecase = DeleteMessageUseCaseImpl(message_repository)

    try:
        failed_ids = delete_message_usecase.execute_bulk(message_bulk_delete.message_ids)
        return {"failed_ids": failed_ids}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{MessageErrorMessage.MESSAGE_DELETE_FAILED} {str(e)}",
        )
