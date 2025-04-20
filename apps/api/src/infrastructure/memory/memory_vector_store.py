from typing import Any

import weaviate
from sentence_transformers import SentenceTransformer
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.classes.query import Filter
from weaviate.collections.classes.config import DataType, Property

from src.config.app_config import AppConfig


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

        # 埋め込みモデルはSentenceTransformerを使用
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

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
            print(f"Weaviate接続エラー: {str(e)}")
            raise

    def _ensure_schema(self) -> None:
        """Weaviateスキーマが存在することを保証."""
        try:
            # コレクションが存在しない場合は作成
            if not self.client.collections.exists(self.CHAT_MEMORY_CLASS_NAME):
                self.client.collections.create(
                    name=self.CHAT_MEMORY_CLASS_NAME,
                    vectorizer_config=None,
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
                        ),
                        Property(
                            name="chat_id",
                            data_type=DataType.TEXT,
                            description="チャットID（user_profileの場合はNullまたはダミー値）",
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
                    ],
                )
                print(f"Created schema for {self.CHAT_MEMORY_CLASS_NAME}")
        except Exception as e:
            print(f"スキーマ作成エラー: {str(e)}")
            raise

    def encode_text(self, text: str) -> list[float]:
        """テキストをベクトル化."""
        return self.embedding_model.encode(text).tolist()

    def add_memory(self, vector: list[float], metadata: dict) -> str:
        """記憶をベクトルストアに追加."""
        try:
            collection = self.client.collections.get(self.CHAT_MEMORY_CLASS_NAME)
            return collection.data.insert(properties=metadata, vector=vector)
        except Exception as e:
            print(f"メモリ追加エラー: {str(e)}")
            raise

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
                "distance": obj.distance,
                "certainty": 1.0 - (obj.distance or 0.0),  # 距離を確実性に変換
            }
            results.append(item)

        return results

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
                "distance": obj.distance,
                "certainty": 1.0 - (obj.distance or 0.0),  # 距離を確実性に変換
            }
            results.append(item)

        return results

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
                    "distance": obj.distance,
                    "certainty": 1.0 - (obj.distance or 0.0),  # 距離を確実性に変換
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
