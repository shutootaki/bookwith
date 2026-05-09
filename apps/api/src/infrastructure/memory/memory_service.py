"""統合記憶管理サービス."""

import logging
from functools import lru_cache
from typing import Any

from src.config.app_config import AppConfig
from src.domain.annotation.entities.annotation import Annotation
from src.domain.book.entities.book import Book
from src.domain.message.entities.message import Message
from src.infrastructure.memory.memory_retrieval_service import MemoryRetrievalService
from src.infrastructure.memory.memory_vector_store import MemoryVectorStore
from src.infrastructure.memory.prompt_builder_service import PromptBuilderService
from src.infrastructure.memory.summarization_service import SummarizationService
from src.infrastructure.memory.vectorization_service import VectorizationService

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_shared_memory_service() -> "MemoryService":
    """M-02: プロセス内でシングルトンの MemoryService を返す.

    BaseVectorStore は内部でクライアントを共有しているが、`MemoryService.__init__` 自体を
    リクエスト毎に new すると `MemoryRetrievalService` 等が逐次インスタンス化され、
    余計なメモリ使用と CPU を生む。
    """
    return MemoryService()


class MemoryService:
    """統合記憶管理サービス.

    各種記憶機能を統合し、統一されたインターフェースを提供する。
    従来の機能をそのまま維持しながら、内部実装を分離している。
    """

    def __init__(self) -> None:
        """記憶管理サービスの初期化."""
        self.config = AppConfig.get_config()
        self.memory_store = MemoryVectorStore()

        self.memory_retrieval = MemoryRetrievalService(self.memory_store)
        self.vectorization = VectorizationService(self.memory_store)
        self.summarization = SummarizationService(self.memory_store)
        self.prompt_builder = PromptBuilderService(self.memory_retrieval)

    def search_relevant_memories(self, user_id: str, chat_id: str, query: str, chat_limit: int | None = None) -> list[dict[str, Any]]:
        """ユーザークエリに関連する記憶を検索."""
        return self.memory_retrieval.search_relevant_memories(user_id, chat_id, query, chat_limit)

    def vectorize_message(self, message: Message) -> None:
        """メッセージを同期的にベクトル化."""
        self.vectorization.vectorize_message(message)

    def summarize_chat(self, chat_id: str, user_id: str, message_count: int) -> None:
        """チャットの要約を同期的に生成（条件を満たす場合）."""
        self.summarization.summarize_chat(chat_id, user_id, message_count)

    def build_memory_prompt(self, buffer: list[Message], user_query: str, user_id: str, chat_id: str) -> str:
        """記憶に基づくプロンプトを構築."""
        return self.prompt_builder.build_memory_prompt(buffer, user_query, user_id, chat_id)

    def add_book_annotations(self, book: Book, annotations: list[Annotation]) -> None:
        """ブックのアノテーションをベクトル化して保存."""
        self.vectorization.add_book_annotations(book, annotations)

    def delete_book_annotation(self, user_id: str, annotation_id: str) -> None:
        """ブックのアノテーションを削除."""
        self.vectorization.delete_book_annotation(user_id, annotation_id)

    def update_book_annotations(self, book: Book, annotations: list[Annotation]) -> None:
        """ブックのアノテーションを更新."""
        self.vectorization.update_book_annotations(book, annotations)

    def delete_book_memories(self, user_id: str, book_id: str) -> None:
        """本に関連するすべての記憶を削除."""
        self.vectorization.delete_book_memories(user_id, book_id)
