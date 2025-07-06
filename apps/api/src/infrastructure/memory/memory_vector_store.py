"""統合ベクトルストア管理クラス."""

import logging
from typing import Any

import weaviate
from fastapi import UploadFile
from langchain_openai import OpenAIEmbeddings

from src.infrastructure.memory.base_vector_store import BaseVectorStore
from src.infrastructure.memory.book_annotation_store import BookAnnotationStore
from src.infrastructure.memory.book_content_store import BookContentStore
from src.infrastructure.memory.chat_memory_store import ChatMemoryStore
from src.infrastructure.memory.collection_manager import CollectionManager
from src.infrastructure.memory.vector_crud_service import VectorCrudService

logger = logging.getLogger(__name__)


class MemoryVectorStore(BaseVectorStore):
    """チャット記憶、書籍コンテンツ、アノテーションのベクトルストア統合管理クラス.

    各専門サービスの機能を統合し、既存のインターフェースを維持する。
    """

    def __init__(self) -> None:
        """ベクトルストア統合管理クラスの初期化."""
        super().__init__()

        # コレクションの初期化
        self.collection_manager = CollectionManager()

        # 各専門サービスを初期化
        self.chat_memory = ChatMemoryStore()
        self.book_content = BookContentStore()
        self.book_annotation = BookAnnotationStore()
        self.crud_service = VectorCrudService()

    # チャット記憶関連のメソッド（ChatMemoryStoreに委譲）
    def search_chat_memories(self, user_id: str, chat_id: str, query_vector: list[float], limit: int = 5) -> list[dict[str, Any]]:
        """チャットIDによる関連記憶のベクトル検索."""
        return self.chat_memory.search_chat_memories(user_id, chat_id, query_vector, limit)

    def get_unsummarized_messages(self, user_id: str, chat_id: str, max_count: int = 100) -> list[dict[str, Any]]:
        """要約されていないメッセージを取得."""
        return self.chat_memory.get_unsummarized_messages(user_id, chat_id, max_count)

    def mark_messages_as_summarized(self, user_id: str, chat_id: str, message_ids: list[str]) -> None:
        """指定したメッセージを要約済みとしてマーク."""
        self.chat_memory.mark_messages_as_summarized(user_id, chat_id, message_ids)

    # 書籍コンテンツ関連のメソッド（BookContentStoreに委譲）
    async def create_book_vector_index(self, file: UploadFile, user_id: str, book_id: str) -> dict:
        """EPUBファイルを処理してBookContentコレクションにベクトルインデックス化する."""
        return await self.book_content.create_book_vector_index(file, user_id, book_id)

    # アノテーション関連のメソッド（BookAnnotationStoreに委譲）
    def search_highlights(self, user_id: str, book_id: str, query_vector: list[float], limit: int = 3) -> list[dict[str, Any]]:
        """ハイライト（BookAnnotationコレクション）をベクトル検索する."""
        return self.book_annotation.search_highlights(user_id, book_id, query_vector, limit)

    # CRUD操作（VectorCrudServiceに委譲）
    def add_memory(self, vector: list[float], metadata: dict, user_id: str, collection_name: str) -> str:
        """記憶を適切なベクトルストアコレクションに追加."""
        return self.crud_service.add_memory(vector, metadata, user_id, collection_name)

    def delete_memory(self, user_id: str, collection_name: str, target: str, key: str) -> None:
        """メモリを削除."""
        self.crud_service.delete_memory(user_id, collection_name, target, key)

    def update_memory(self, user_id: str, collection_name: str, target: str, key: str, properties: dict, vector: list[float]) -> None:
        """メモリを更新."""
        self.crud_service.update_memory(user_id, collection_name, target, key, properties, vector)

    def delete_book_data(self, user_id: str, book_id: str) -> None:
        """本に関連するすべてのベクターデータを削除."""
        self.crud_service.delete_book_data(user_id, book_id)

    # 後方互換性のためのクラスメソッド（BaseVectorStoreから継承）
    @classmethod
    def get_client(cls) -> weaviate.WeaviateClient:
        """共有の Weaviate クライアントを返す."""
        return super().get_client()

    @classmethod
    def get_embedding_model(cls) -> OpenAIEmbeddings:
        """共有の Embedding モデルを返す."""
        return super().get_embedding_model()
