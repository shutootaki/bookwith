"""記憶検索サービス."""

import logging
from typing import Any

from src.config.app_config import AppConfig
from src.infrastructure.memory.memory_vector_store import MemoryVectorStore

logger = logging.getLogger(__name__)


class MemoryRetrievalService:
    """記憶検索に特化したサービス."""

    def __init__(self, memory_store: MemoryVectorStore | None = None) -> None:
        """記憶検索サービスの初期化."""
        self.config = AppConfig.get_config()
        self.memory_store = memory_store or MemoryVectorStore()

    def search_relevant_memories(self, user_id: str, chat_id: str, query: str, chat_limit: int | None = None) -> list[dict[str, Any]]:
        """ユーザークエリに関連する記憶を検索.

        Args:
            user_id: ユーザーID
            chat_id: チャットID
            query: ユーザーの質問/クエリ
            chat_limit: 取得するチャット記憶の数

        Returns:
            チャット記憶リスト

        """
        if chat_limit is None:
            chat_limit = 3

        try:
            query_vector = self.memory_store.encode_text(query)
            return self.memory_store.search_chat_memories(user_id=user_id, chat_id=chat_id, query_vector=query_vector, limit=chat_limit)
        except Exception as e:
            logger.error(f"記憶検索中にエラーが発生: {str(e)}", exc_info=True)
            return []

    def format_memory_item(self, memory: dict[str, Any], prefix: str = "") -> str:
        """記憶アイテムをフォーマット."""
        content = memory.get("content", "N/A")

        # 関連度を取得
        certainty = None
        if "_additional" in memory and isinstance(memory["_additional"], dict):
            certainty = memory["_additional"].get("certainty")

        # 関連度がある場合は表示
        formatted = f"{prefix}{content}"
        if certainty is not None:
            formatted += f" (関連度: {certainty:.2f})"

        return formatted
