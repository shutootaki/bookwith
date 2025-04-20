from typing import Any

from fastapi import BackgroundTasks

from src.config.app_config import AppConfig
from src.domain.message.entities.message import Message
from src.domain.message.repositories.message_repository import MessageRepository
from src.infrastructure.memory.memory_prompt import create_memory_prompt
from src.infrastructure.memory.memory_tasks import summarize_and_vectorize_background, vectorize_text_background
from src.infrastructure.memory.memory_vector_store import MemoryVectorStore


class MemoryService:
    """記憶管理サービス."""

    def __init__(self) -> None:
        """記憶管理サービスの初期化."""
        self.config = AppConfig.get_config()
        self.memory_store = MemoryVectorStore()

    def get_latest_messages(self, messages: list[Message]) -> list[Message]:
        """最新のメッセージバッファを取得.

        Args:
            messages: チャットの全メッセージリスト

        Returns:
            最新のメッセージバッファ (新しい順)

        """
        # 時間でソート（新しい順）
        sorted_messages = sorted([msg for msg in messages if not msg.is_deleted], key=lambda msg: msg.created_at, reverse=True)

        # 設定されたバッファサイズ分だけ返す
        return sorted_messages[: self.config.memory_buffer_size]

    def search_relevant_memories(self, user_id: str, chat_id: str, query: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """ユーザークエリに関連する記憶を検索.

        Args:
            user_id: ユーザーID
            chat_id: チャットID
            query: ユーザーの質問/クエリ

        Returns:
            (チャット記憶リスト, ユーザープロファイル記憶リスト)のタプル

        """
        # クエリをベクトル化
        query_vector = self.memory_store.encode_text(query)

        # チャット記憶を検索
        chat_memories = self.memory_store.search_chat_memories(
            user_id=user_id, chat_id=chat_id, query_vector=query_vector, limit=self.config.memory_chat_results
        )

        # ユーザープロファイル記憶を検索
        user_profile_memories = self.memory_store.search_user_profile(
            user_id=user_id, query_vector=query_vector, limit=self.config.memory_profile_results
        )

        return chat_memories, user_profile_memories

    def schedule_message_vectorization(self, message: Message, background_tasks: BackgroundTasks) -> None:
        """メッセージのベクトル化をスケジュール.

        Args:
            message: ベクトル化するメッセージ
            background_tasks: バックグラウンドタスクマネージャー

        """
        background_tasks.add_task(vectorize_text_background, message=message, memory_store=self.memory_store, config=self.config)

    def schedule_chat_summarization(
        self, chat_id: str, user_id: str, message_count: int, message_repository: MessageRepository, background_tasks: BackgroundTasks
    ) -> None:
        """チャットの要約生成をスケジュール（条件を満たす場合）.

        Args:
            chat_id: チャットID
            user_id: ユーザーID
            message_count: 現在のメッセージ数
            message_repository: メッセージリポジトリ
            background_tasks: バックグラウンドタスクマネージャー

        """
        # メッセージ数が閾値の倍数に達した場合に要約をスケジュール
        threshold = self.config.memory_summarize_threshold
        if message_count > 0 and message_count % threshold == 0:
            background_tasks.add_task(
                summarize_and_vectorize_background,
                chat_id=chat_id,
                user_id=user_id,
                message_repository=message_repository,
                memory_store=self.memory_store,
                config=self.config,
            )

    def build_memory_prompt(self, buffer: list[Message], user_query: str, user_id: str, chat_id: str) -> str:
        """記憶に基づくプロンプトを構築.

        Args:
            buffer: 最新のメッセージバッファ
            user_query: ユーザーの質問/クエリ
            user_id: ユーザーID
            chat_id: チャットID

        Returns:
            構築されたプロンプト

        """
        # 関連する記憶を検索
        chat_memories, user_profile_memories = self.search_relevant_memories(user_id=user_id, chat_id=chat_id, query=user_query)

        # プロンプトを構築
        return create_memory_prompt(
            buffer=buffer, chat_memories=chat_memories, user_profile_memories=user_profile_memories, user_query=user_query, config=self.config
        )
