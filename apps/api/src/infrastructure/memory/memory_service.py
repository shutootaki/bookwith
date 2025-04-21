import logging
from typing import Any

from fastapi import BackgroundTasks

from src.config.app_config import AppConfig
from src.domain.message.entities.message import Message
from src.domain.message.repositories.message_repository import MessageRepository
from src.infrastructure.memory.memory_prompt import (
    create_memory_prompt,
    create_memory_prompt_with_reranking,
)
from src.infrastructure.memory.memory_tasks import (
    process_batch_summarization,
    summarize_and_vectorize_background,
    vectorize_text_background,
)
from src.infrastructure.memory.memory_vector_store import MemoryVectorStore

# ロガーの設定
logger = logging.getLogger(__name__)


class MemoryService:
    """記憶管理サービス."""

    def __init__(self) -> None:
        """記憶管理サービスの初期化."""
        self.config = AppConfig.get_config()
        self.memory_store = MemoryVectorStore()

    def get_latest_messages(self, messages: list[Message], limit: int | None = None) -> list[Message]:
        """最新のメッセージバッファを取得.

        Args:
            messages: チャットの全メッセージリスト
            limit: 取得するメッセージ数（Noneの場合はconfig値を使用）

        Returns:
            最新のメッセージバッファ (新しい順)

        """
        if limit is None:
            limit = self.config.memory_buffer_size

        # 時間でソート（新しい順）
        sorted_messages = sorted([msg for msg in messages if not msg.is_deleted], key=lambda msg: msg.created_at, reverse=True)

        # 設定されたバッファサイズ分だけ返す
        return sorted_messages[:limit]

    def search_relevant_memories(
        self, user_id: str, chat_id: str, query: str, chat_limit: int | None = None, profile_limit: int | None = None
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """ユーザークエリに関連する記憶を検索.

        Args:
            user_id: ユーザーID
            chat_id: チャットID
            query: ユーザーの質問/クエリ
            chat_limit: 取得するチャット記憶の数
            profile_limit: 取得するプロファイル記憶の数

        Returns:
            (チャット記憶リスト, ユーザープロファイル記憶リスト)のタプル

        """
        # デフォルト値設定
        if chat_limit is None:
            chat_limit = self.config.memory_chat_results
        if profile_limit is None:
            profile_limit = self.config.memory_profile_results

        # クエリをベクトル化
        try:
            query_vector = self.memory_store.encode_text(query)

            # チャット記憶を検索
            chat_memories = self.memory_store.search_chat_memories(user_id=user_id, chat_id=chat_id, query_vector=query_vector, limit=chat_limit)

            # ユーザープロファイル記憶を検索
            user_profile_memories = self.memory_store.search_user_profile(user_id=user_id, query_vector=query_vector, limit=profile_limit)

            print(
                f"ユーザー {user_id} のクエリ '{query[:30]}...' に対して記憶検索: {len(chat_memories)}件のチャット記憶, {len(user_profile_memories)}件のプロファイル記憶"
            )
            return chat_memories, user_profile_memories
        except Exception as e:
            logger.error(f"記憶検索中にエラーが発生: {str(e)}", exc_info=True)
            return [], []  # エラー時は空リストを返す

    def schedule_message_vectorization(self, message: Message, background_tasks: BackgroundTasks) -> None:
        """メッセージのベクトル化をスケジュール（互換性のために残しているが同期処理）.

        Args:
            message: ベクトル化するメッセージ
            background_tasks: バックグラウンドタスクマネージャー（使用されない）

        """
        # BackgroundTasksパラメータは互換性のために残していますが、実際には使用せず同期的に処理します
        self.vectorize_message(message)
        logger.debug(f"メッセージID {message.id.value} のベクトル化を実行")

    def vectorize_message(self, message: Message) -> None:
        """メッセージを同期的にベクトル化.

        Args:
            message: ベクトル化するメッセージ

        """
        vectorize_text_background(message=message, memory_store=self.memory_store, config=self.config)
        logger.debug(f"メッセージID {message.id.value} のベクトル化を実行")

    def schedule_chat_summarization(
        self, chat_id: str, user_id: str, message_count: int, message_repository: MessageRepository, background_tasks: BackgroundTasks
    ) -> None:
        """チャットの要約生成をスケジュール（互換性のために残しているが同期処理）.

        Args:
            chat_id: チャットID
            user_id: ユーザーID
            message_count: 現在のメッセージ数
            message_repository: メッセージリポジトリ
            background_tasks: バックグラウンドタスクマネージャー（使用されない）

        """
        # BackgroundTasksパラメータは互換性のために残していますが、実際には使用せず同期的に処理します
        self.summarize_chat(chat_id, user_id, message_count, message_repository)

    def summarize_chat(self, chat_id: str, user_id: str, message_count: int, message_repository: MessageRepository) -> None:
        """チャットの要約を同期的に生成（条件を満たす場合）.

        Args:
            chat_id: チャットID
            user_id: ユーザーID
            message_count: 現在のメッセージ数
            message_repository: メッセージリポジトリ

        """
        # メッセージ数が閾値の倍数に達した場合に要約を実行
        threshold = self.config.memory_summarize_threshold
        if message_count > 0 and message_count % threshold == 0:
            print(f"チャットID {chat_id} の要約生成を実行 (メッセージ数: {message_count})")
            summarize_and_vectorize_background(
                chat_id=chat_id,
                user_id=user_id,
                message_repository=message_repository,
                memory_store=self.memory_store,
                config=self.config,
            )

    def schedule_batch_summarization(self, user_id: str, message_repository: MessageRepository, background_tasks: BackgroundTasks) -> None:
        """ユーザーの全チャットのバッチ要約をスケジュール（互換性のために残しているが同期処理）.

        Args:
            user_id: ユーザーID
            message_repository: メッセージリポジトリ
            background_tasks: バックグラウンドタスクマネージャー（使用されない）

        """
        # BackgroundTasksパラメータは互換性のために残していますが、実際には使用せず同期的に処理します
        self.batch_summarize(user_id, message_repository)

    def batch_summarize(self, user_id: str, message_repository: MessageRepository) -> None:
        """ユーザーの全チャットのバッチ要約を同期的に実行.

        Args:
            user_id: ユーザーID
            message_repository: メッセージリポジトリ

        """
        print(f"ユーザー {user_id} の全チャットのバッチ要約を実行")
        process_batch_summarization(
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
            buffer=buffer,
            chat_memories=chat_memories,
            user_profile_memories=user_profile_memories,
            user_query=user_query,
            config=self.config,
        )

    def build_memory_prompt_with_reranking(self, buffer: list[Message], user_query: str, user_id: str, chat_id: str) -> str:
        """再ランキングを行った記憶に基づくプロンプトを構築.

        Args:
            buffer: 最新のメッセージバッファ
            user_query: ユーザーの質問/クエリ
            user_id: ユーザーID
            chat_id: チャットID

        Returns:
            構築されたプロンプト

        """
        return create_memory_prompt_with_reranking(
            buffer=buffer,
            user_query=user_query,
            user_id=user_id,
            chat_id=chat_id,
            memory_store=self.memory_store,
            embedding_model=self.memory_store.embedding_model,
            config=self.config,
        )

    def get_knowledge_items(self, user_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """ユーザーのプロファイル情報（知識）を取得.

        Args:
            user_id: ユーザーID
            limit: 取得する最大数

        Returns:
            プロファイル情報のリスト

        """
        try:
            # ユーザープロファイルタイプの記憶を検索（ベクトル検索なし）
            collection = self.memory_store.client.collections.get(self.memory_store.CHAT_MEMORY_CLASS_NAME)

            # フィルター作成
            from weaviate.classes.query import Filter

            filter_query = Filter.by_property("user_id").equal(user_id) & Filter.by_property("type").equal(self.memory_store.TYPE_USER_PROFILE)

            # 取得
            response = collection.query.fetch_objects(
                filters=filter_query,
                return_properties=["content", "created_at", "message_id"],
                limit=limit,
                sort=[{"path": ["created_at"], "order": "desc"}],  # 新しい順
            )

            # 結果変換
            results = []
            for obj in response.objects:
                item = obj.properties
                item["id"] = obj.uuid
                results.append(item)

            print(f"ユーザー {user_id} のプロファイル情報を {len(results)}件 取得")
            return results
        except Exception as e:
            logger.error(f"プロファイル情報取得中にエラーが発生: {str(e)}", exc_info=True)
            return []

    def add_manual_knowledge(self, user_id: str, content: str, background_tasks: BackgroundTasks) -> bool:
        """ユーザープロファイル情報を手動で追加（互換性のために残しているが同期処理）.

        Args:
            user_id: ユーザーID
            content: プロファイル情報の内容
            background_tasks: バックグラウンドタスク（使用されない）

        Returns:
            成功したかどうか

        """
        # BackgroundTasksパラメータは互換性のために残していますが、実際には使用せず同期的に処理します
        return self.add_manual_knowledge_sync(user_id, content)

    def add_manual_knowledge_sync(self, user_id: str, content: str) -> bool:
        """ユーザープロファイル情報を手動で追加（同期版）.

        Args:
            user_id: ユーザーID
            content: プロファイル情報の内容

        Returns:
            成功したかどうか

        """
        # 同じ処理を同期的に実行
        try:
            # ベクトル化
            vector = self.memory_store.encode_text(content)

            # メタデータ準備
            import datetime

            timestamp = datetime.datetime.now().isoformat()
            knowledge_id = f"manual_knowledge_{user_id}_{timestamp}"

            metadata = {
                "content": content,
                "type": self.memory_store.TYPE_USER_PROFILE,
                "user_id": user_id,
                "chat_id": None,  # プロファイル情報はチャットに紐づかない
                "message_id": knowledge_id,
                "sender": "system",  # 手動追加なのでsystem
                "created_at": timestamp,
                "token_count": len(content.split()),  # 簡易的なトークンカウント
            }

            # 保存
            knowledge_id = self.memory_store.add_memory(vector=vector, metadata=metadata)
            print(f"ユーザー {user_id} に手動プロファイル情報を同期的に追加 (id: {knowledge_id})")
            return True
        except Exception as e:
            logger.error(f"手動プロファイル情報追加中にエラーが発生: {str(e)}", exc_info=True)
            return False

    def delete_knowledge(self, knowledge_id: str) -> bool:
        """プロファイル情報を削除.

        Args:
            knowledge_id: 削除するプロファイル情報のID

        Returns:
            成功したかどうか

        """
        try:
            # Weaviateからオブジェクトを削除
            collection = self.memory_store.client.collections.get(self.memory_store.CHAT_MEMORY_CLASS_NAME)
            collection.data.delete(uuid=knowledge_id)
            print(f"プロファイル情報 {knowledge_id} を削除")
            return True
        except Exception as e:
            logger.error(f"プロファイル情報削除中にエラーが発生: {str(e)}", exc_info=True)
            return False

    def search_messages(self, user_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """メッセージを検索.

        Args:
            user_id: ユーザーID
            query: 検索クエリ
            limit: 取得する最大数

        Returns:
            検索結果メッセージリスト

        """
        try:
            # クエリをベクトル化
            query_vector = self.memory_store.encode_text(query)

            # ユーザーのメッセージのみを検索
            collection = self.memory_store.client.collections.get(self.memory_store.CHAT_MEMORY_CLASS_NAME)

            # フィルター作成
            from weaviate.classes.query import Filter

            filter_query = Filter.by_property("user_id").equal(user_id) & Filter.by_property("type").equal(self.memory_store.TYPE_MESSAGE)

            # 検索実行
            response = collection.query.near_vector(
                near_vector=query_vector,
                return_properties=["content", "chat_id", "sender", "created_at", "message_id"],
                filters=filter_query,
                limit=limit,
            )

            # 結果変換
            results = []
            for obj in response.objects:
                item = obj.properties
                item["id"] = obj.uuid
                item["relevance"] = 1.0 - (obj.distance or 0.0)  # 関連度
                results.append(item)

            print(f"ユーザー {user_id} のクエリ '{query[:30]}...' に対して {len(results)}件のメッセージを検索")
            return results
        except Exception as e:
            logger.error(f"メッセージ検索中にエラーが発生: {str(e)}", exc_info=True)
            return []
