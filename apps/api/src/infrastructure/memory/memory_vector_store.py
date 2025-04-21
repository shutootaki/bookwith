import logging
import time
from functools import wraps
from typing import Any

import weaviate
from langchain_openai import OpenAIEmbeddings
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.classes.query import Filter
from weaviate.collections.classes.config import DataType, Property

from src.config.app_config import AppConfig

# ロガーの設定
logger = logging.getLogger(__name__)


def retry_on_error(max_retries=3, initial_delay=1, backoff_factor=2):
    """エラー発生時に再試行するデコレータ"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = initial_delay
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"最大再試行回数 ({max_retries}) に達しました: {str(e)}")
                        raise
                    logger.warning(f"操作失敗、{delay}秒後に再試行 ({retries}/{max_retries}): {str(e)}")
                    time.sleep(delay)
                    delay *= backoff_factor

        return wrapper

    return decorator


class MemoryVectorStore:
    """チャット記憶のベクトルストア管理クラス."""

    # Weaviateのクラス名
    CHAT_MEMORY_CLASS_NAME = "ChatMemory"

    # メモリタイプ定義
    TYPE_MESSAGE = "message"
    TYPE_SUMMARY = "summary"
    TYPE_USER_PROFILE = "user_profile"

    def __init__(self) -> None:
        """Weaviateクライアントを初期化."""
        self.config = AppConfig.get_config()
        self.client = self._create_client()
        self._ensure_schema()
        self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-small", max_retries=2)

    @retry_on_error(max_retries=5, initial_delay=2)
    def _create_client(self):
        """Weaviateクライアントを作成."""
        try:
            # タイムアウト設定を追加
            return weaviate.connect_to_local(
                additional_config=AdditionalConfig(
                    timeout=Timeout(init=30, query=60, insert=120)  # 秒単位
                )
            )
        except Exception as e:
            logger.error(f"Weaviate接続エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=3, initial_delay=1)
    def _ensure_schema(self) -> None:
        """Weaviateスキーマが存在することを保証."""
        try:
            # コレクションが存在しない場合は作成
            if not self.client.collections.exists(self.CHAT_MEMORY_CLASS_NAME):
                self.client.collections.create(
                    name=self.CHAT_MEMORY_CLASS_NAME,
                    vectorizer_config=None,  # 外部でベクトル化
                    properties=[
                        Property(
                            name="content",
                            data_type=DataType.TEXT,
                            description="メッセージ/要約/プロファイル情報の内容",
                        ),
                        Property(
                            name="type",
                            data_type=DataType.TEXT,
                            description="記憶の種類（message, summary, user_profile）",
                            index_searchable=True,
                        ),
                        Property(
                            name="user_id",
                            data_type=DataType.TEXT,
                            description="ユーザーID",
                            index_searchable=True,
                        ),
                        Property(
                            name="chat_id",
                            data_type=DataType.TEXT,
                            description="チャットID（user_profileの場合はNullまたはダミー値）",
                            index_searchable=True,
                        ),
                        Property(
                            name="message_id",
                            data_type=DataType.TEXT,
                            description="元のメッセージID",
                        ),
                        Property(
                            name="sender",
                            data_type=DataType.TEXT,
                            description="送信者タイプ（user, assistant, system）",
                            index_searchable=True,
                        ),
                        Property(
                            name="created_at",
                            data_type=DataType.DATE,
                            description="作成日時",
                        ),
                        Property(
                            name="token_count",
                            data_type=DataType.INT,
                            description="トークン数（参考情報）",
                        ),
                        Property(
                            name="is_summarized",
                            data_type=DataType.BOOL,
                            description="要約済みフラグ（メッセージ専用）",
                        ),
                    ],
                )
                print(f"Created schema for {self.CHAT_MEMORY_CLASS_NAME}")
        except Exception as e:
            logger.error(f"スキーマ作成エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def encode_text(self, text: str) -> list[float]:
        """テキストをベクトル化."""
        return self.embedding_model.embed_query(text)

    @retry_on_error(max_retries=3)
    def add_memory(self, vector: list[float], metadata: dict) -> str:
        """記憶をベクトルストアに追加."""
        try:
            # デフォルト値の設定（必要に応じて）
            if "is_summarized" not in metadata and metadata.get("type") == self.TYPE_MESSAGE:
                metadata["is_summarized"] = False

            collection = self.client.collections.get(self.CHAT_MEMORY_CLASS_NAME)
            return collection.data.insert(properties=metadata, vector=vector)
        except Exception as e:
            logger.error(f"メモリ追加エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def update_memory(self, uuid: str, properties: dict) -> None:
        """記憶のプロパティを更新."""
        try:
            collection = self.client.collections.get(self.CHAT_MEMORY_CLASS_NAME)
            collection.data.update(uuid=uuid, properties=properties)
            logger.debug(f"記憶 {uuid} を更新しました")
        except Exception as e:
            logger.error(f"メモリ更新エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def mark_messages_as_summarized(self, user_id: str, chat_id: str, message_ids: list[str]) -> None:
        """指定したメッセージを要約済みとしてマーク."""
        if not message_ids:
            return

        try:
            collection = self.client.collections.get(self.CHAT_MEMORY_CLASS_NAME)

            # メッセージIDのリストに基づいてフィルタを作成
            where_filter = (
                Filter.by_property("user_id").equal(user_id)
                & Filter.by_property("chat_id").equal(chat_id)
                & Filter.by_property("type").equal(self.TYPE_MESSAGE)
                & Filter.by_property("message_id").contains_any(message_ids)
            )

            # 対象となるオブジェクトを取得
            response = collection.query.fetch_objects(
                filters=where_filter,
                return_properties=["message_id"],
                limit=len(message_ids) + 10,  # 少し余裕を持たせる
            )

            # 各オブジェクトを更新
            for obj in response.objects:
                collection.data.update(uuid=obj.uuid, properties={"is_summarized": True})

            print(f"{len(response.objects)}件のメッセージを要約済みとしてマーク")
        except Exception as e:
            logger.error(f"メッセージの要約済みマーク更新エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def search_similar_memories(self, query: str, user_id: str, chat_id: str, memory_type: str, limit: int = 5) -> list[dict[str, Any]]:
        """類似記憶を検索."""
        query_vector = self.encode_text(query)

        collection = self.client.collections.get(self.CHAT_MEMORY_CLASS_NAME)

        # フィルターの作成
        where_filter = (
            Filter.by_property("user_id").equal(user_id)
            & Filter.by_property("chat_id").equal(chat_id)
            & Filter.by_property("type").equal(memory_type)
        )

        # クエリ実行
        response = collection.query.near_vector(
            near_vector=query_vector,
            return_properties=["content", "type", "user_id", "chat_id", "message_id", "sender", "created_at", "token_count"],
            include_vector=False,
            limit=limit,
            filters=where_filter,
        )

        # 結果の変換
        results = []
        for obj in response.objects:
            item = obj.properties
            item["id"] = obj.uuid
            # 距離情報を取得
            item["_additional"] = {
                "distance": obj.metadata.distance,
                "certainty": 1.0 - (obj.metadata.distance or 0.0),  # 距離を確実性に変換
            }
            results.append(item)

        return results

    @retry_on_error(max_retries=2)
    def fetch_memories_by_chat_id(self, user_id: str, chat_id: str, memory_type: str) -> list[dict[str, Any]]:
        """チャットIDによる記憶の取得 (ベクトル検索なし)."""
        collection = self.client.collections.get(self.CHAT_MEMORY_CLASS_NAME)

        # フィルターの作成
        where_filter = (
            Filter.by_property("user_id").equal(user_id)
            & Filter.by_property("chat_id").equal(chat_id)
            & Filter.by_property("type").equal(memory_type)
        )

        # クエリ実行
        response = collection.query.fetch_objects(
            filters=where_filter,
            return_properties=["content", "type", "user_id", "chat_id", "message_id", "sender", "created_at", "token_count"],
            limit=100,
        )

        # 結果の変換
        results = []
        for obj in response.objects:
            item = obj.properties
            item["id"] = obj.uuid
            results.append(item)

        return results

    @retry_on_error(max_retries=2)
    def search_chat_memories(self, user_id: str, chat_id: str, query_vector: list[float], limit: int = 5) -> list[dict[str, Any]]:
        """チャットIDによる関連記憶のベクトル検索."""
        collection = self.client.collections.get(self.CHAT_MEMORY_CLASS_NAME)

        # フィルターの作成
        memory_types = [self.TYPE_MESSAGE, self.TYPE_SUMMARY]
        where_filter = (
            Filter.by_property("user_id").equal(user_id)
            & Filter.by_property("chat_id").equal(chat_id)
            & Filter.by_property("type").contains_any(memory_types)
        )

        # クエリ実行
        response = collection.query.near_vector(
            near_vector=query_vector,
            return_properties=["content", "type", "user_id", "chat_id", "message_id", "sender", "created_at", "token_count"],
            include_vector=False,
            filters=where_filter,
            limit=limit,
        )

        # 結果の変換
        results = []
        for obj in response.objects:
            item = obj.properties
            item["id"] = obj.uuid
            # 距離情報を取得
            item["_additional"] = {
                "distance": obj.metadata.distance,
                "certainty": 1.0 - (obj.metadata.distance or 0.0),  # 距離を確実性に変換
            }
            results.append(item)

        return results

    @retry_on_error(max_retries=2)
    def search_user_profile(self, user_id: str, query_vector: list[float] | None = None, limit: int = 1) -> list[dict[str, Any]]:
        """ユーザープロファイルを検索."""
        collection = self.client.collections.get(self.CHAT_MEMORY_CLASS_NAME)

        # フィルターの作成
        where_filter = Filter.by_property("user_id").equal(user_id) & Filter.by_property("type").equal(self.TYPE_USER_PROFILE)

        # クエリ実行
        results = []
        if query_vector:
            # ベクトル検索
            response = collection.query.near_vector(
                near_vector=query_vector,
                return_properties=["content", "user_id", "created_at"],
                include_vector=False,
                filters=where_filter,
                limit=limit,
            )

            # 結果の変換
            for obj in response.objects:
                item = obj.properties
                item["id"] = obj.uuid
                # 距離情報を取得
                item["_additional"] = {
                    "distance": obj.metadata.distance,
                    "certainty": 1.0 - (obj.metadata.distance or 0.0),  # 距離を確実性に変換
                }
                results.append(item)
        else:
            # 通常の検索
            response = collection.query.fetch_objects(filters=where_filter, return_properties=["content", "user_id", "created_at"], limit=limit)

            # 結果の変換
            for obj in response.objects:
                item = obj.properties
                item["id"] = obj.uuid
                results.append(item)

        return results

    @retry_on_error(max_retries=2)
    def get_unsummarized_messages(self, user_id: str, chat_id: str, max_count: int = 100) -> list[dict[str, Any]]:
        """要約されていないメッセージを取得."""
        collection = self.client.collections.get(self.CHAT_MEMORY_CLASS_NAME)

        # フィルターの作成
        where_filter = (
            Filter.by_property("user_id").equal(user_id)
            & Filter.by_property("chat_id").equal(chat_id)
            & Filter.by_property("type").equal(self.TYPE_MESSAGE)
            & Filter.by_property("is_summarized").equal(False)
        )

        # クエリ実行（作成日時順）
        response = collection.query.fetch_objects(
            filters=where_filter,
            return_properties=["content", "message_id", "sender", "created_at", "token_count"],
            limit=max_count,
            sort=[{"path": ["created_at"], "order": "asc"}],  # 古い順にソート
        )

        # 結果の変換
        results = []
        for obj in response.objects:
            item = obj.properties
            item["id"] = obj.uuid
            results.append(item)

        return results
