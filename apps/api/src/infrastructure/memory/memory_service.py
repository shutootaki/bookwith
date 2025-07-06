"""統合記憶管理サービス."""

import logging
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


class MemoryService:
    """統合記憶管理サービス.

    各種記憶機能を統合し、統一されたインターフェースを提供する。
    従来の機能をそのまま維持しながら、内部実装を分離している。
    """

    def __init__(self) -> None:
        """記憶管理サービスの初期化."""
        self.config = AppConfig.get_config()
        self.memory_store = MemoryVectorStore()

        # 各機能サービスを初期化
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

    def vectorize_text_background(self, message: Message, memory_store: MemoryVectorStore, config: AppConfig | None = None) -> None:
        """メッセージをベクトル化して保存する非同期タスク（後方互換性のため）."""
        # 後方互換性のため、既存の呼び出しをサポート
        self.vectorization.vectorize_message(message)

    def summarize_chat(self, chat_id: str, user_id: str, message_count: int) -> None:
        """チャットの要約を同期的に生成（条件を満たす場合）."""
        self.summarization.summarize_chat(chat_id, user_id, message_count)

    def build_memory_prompt(self, buffer: list[Message], user_query: str, user_id: str, chat_id: str) -> str:
        """記憶に基づくプロンプトを構築."""
        return self.prompt_builder.build_memory_prompt(buffer, user_query, user_id, chat_id)

    def summarize_and_vectorize_background(
        self, chat_id: str, user_id: str, memory_store: MemoryVectorStore, config: AppConfig | None = None
    ) -> None:
        """チャットメッセージを要約してベクトル化する非同期タスク（後方互換性のため）."""
        # 後方互換性のため、既存の呼び出しをサポート
        self.summarization._summarize_and_vectorize_background(chat_id, user_id)

    # アノテーション関連メソッド（ベクトル化サービスに委譲）
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

    # ユーティリティメソッド（プロンプトビルダーサービスに委譲）
    def estimate_tokens(self, text: str) -> int:
        """テキストのトークン数を推定."""
        return self.prompt_builder._estimate_tokens(text)

    def format_memory_item(self, memory: dict[str, Any], prefix: str = "") -> str:
        """記憶アイテムをフォーマット."""
        return self.memory_retrieval.format_memory_item(memory, prefix)

    def truncate_text_to_tokens(self, text: str, max_tokens: int) -> str:
        """トークン数制限に基づいてテキストを切り詰める."""
        return self.prompt_builder._truncate_text_to_tokens(text, max_tokens)

    def create_memory_prompt(
        self,
        buffer: list[Message],
        chat_memories: list[dict[str, Any]],
        user_query: str,
        config: AppConfig | None = None,
    ) -> str:
        """記憶とバッファからプロンプトを作成（後方互換性のため）."""
        return self.prompt_builder._create_memory_prompt(buffer, chat_memories, user_query)

    def get_llm_summary(self, text_to_summarize: str) -> str | None:
        """LLMを使用して要約を取得する（後方互換性のため）."""
        return self.summarization._get_llm_summary(text_to_summarize)
