"""ベクトル化サービス."""

import logging
from typing import Any

from src.config.app_config import AppConfig
from src.domain.annotation.entities.annotation import Annotation
from src.domain.book.entities.book import Book
from src.domain.message.entities.message import Message
from src.infrastructure.memory.memory_vector_store import MemoryVectorStore

logger = logging.getLogger(__name__)


class VectorizationService:
    """テキストのベクトル化に特化したサービス."""

    def __init__(self, memory_store: MemoryVectorStore | None = None) -> None:
        """ベクトル化サービスの初期化."""
        self.config = AppConfig.get_config()
        self.memory_store = memory_store or MemoryVectorStore()

    def vectorize_message(self, message: Message) -> None:
        """メッセージを同期的にベクトル化.

        Args:
            message: ベクトル化するメッセージ

        """
        self._vectorize_message_background(message)
        logger.debug(f"メッセージID {message.id.value} のベクトル化を実行")

    def _vectorize_message_background(self, message: Message) -> None:
        """メッセージをベクトル化して保存する処理."""
        try:
            # メッセージの内容をベクトル化
            text = message.content.value
            vector = self.memory_store.encode_text(text)

            # 基本メタデータを準備
            metadata = {
                "chat_id": message.chat_id,
                "content": text,
                "created_at": message.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "memory_type": self.memory_store.TYPE_MESSAGE,
                "message_id": str(message.id.value),
                "sender": message.sender_type.value,
                "user_id": message.sender_id,
            }

            # ベクトルストアに保存
            memory_id = self.memory_store.add_memory(
                vector=vector, metadata=metadata, user_id=message.sender_id, collection_name=self.memory_store.CHAT_MEMORY_COLLECTION_NAME
            )
            logger.info(f"メッセージID {message.id.value} をベクトル化して保存 (memory_id: {memory_id})")

        except ValueError as ve:
            logger.warning(f"メッセージベクトル化中に値エラー: {str(ve)}")
        except Exception as e:
            logger.error(f"メッセージベクトル化中にエラーが発生: {str(e)}", exc_info=True)

    def add_book_annotations(self, book: Book, annotations: list[Annotation]) -> None:
        """ブックのアノテーションをベクトル化して保存."""
        user_id = book.user_id
        book_title = book.name

        for annotation in annotations:
            # ベクトル化するテキスト（ハイライト＋メモ）
            text_for_vector = annotation.text.value
            if annotation.notes:
                text_for_vector += f"\n{annotation.notes.value}"

            vector = self.memory_store.encode_text(text_for_vector)
            metadata: dict[str, Any] = {
                "annotation_id": annotation.id.value,
                "book_id": book.id.value,
                "book_title": book_title.value,
                "content": annotation.text.value,
                "created_at": annotation.created_at if hasattr(annotation, "created_at") else None,
                "notes": annotation.notes.value if annotation.notes else None,
                "user_id": user_id,
            }

            self.memory_store.add_memory(
                vector=vector, metadata=metadata, user_id=user_id, collection_name=self.memory_store.BOOK_ANNOTATION_COLLECTION_NAME
            )

    def update_book_annotations(self, book: Book, annotations: list[Annotation]) -> None:
        """ブックのアノテーションを更新."""
        user_id = book.user_id
        book_title = book.name

        for annotation in annotations:
            # ベクトル化するテキスト（ハイライト＋メモ）
            text_for_vector = annotation.text.value
            if annotation.notes:
                text_for_vector += f"\n{annotation.notes.value}"

            vector = self.memory_store.encode_text(text_for_vector)
            metadata: dict[str, Any] = {
                "annotation_id": annotation.id.value,
                "book_id": book.id.value,
                "book_title": book_title.value,
                "content": annotation.text.value,
                "created_at": annotation.created_at if hasattr(annotation, "created_at") else None,
                "notes": annotation.notes.value if annotation.notes else None,
                "user_id": user_id,
            }

            self.memory_store.update_memory(
                user_id=user_id,
                collection_name=self.memory_store.BOOK_ANNOTATION_COLLECTION_NAME,
                target="annotation_id",
                key=annotation.id.value,
                properties=metadata,
                vector=vector,
            )

    def delete_book_annotation(self, user_id: str, annotation_id: str) -> None:
        """ブックのアノテーションを削除."""
        self.memory_store.delete_memory(
            user_id=user_id, collection_name=self.memory_store.BOOK_ANNOTATION_COLLECTION_NAME, target="annotation_id", key=annotation_id
        )

    def delete_book_memories(self, user_id: str, book_id: str) -> None:
        """本に関連するすべての記憶を削除.

        Args:
            user_id: ユーザーID
            book_id: 削除する本のID

        """
        try:
            self.memory_store.delete_book_data(user_id, book_id)
            logger.info(f"Book {book_id} memories deleted for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting book memories: {str(e)}")
            # エラーを再スローしない（本の削除処理を継続）
