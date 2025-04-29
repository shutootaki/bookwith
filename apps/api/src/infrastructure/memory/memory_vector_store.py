import logging
import tempfile
import time
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

import weaviate
from fastapi import UploadFile
from langchain_community.document_loaders import UnstructuredEPubLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_weaviate.vectorstores import WeaviateVectorStore
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.classes.query import Filter
from weaviate.exceptions import WeaviateBaseError, WeaviateQueryException

from src.config.app_config import AppConfig

# ロガーの設定
logger = logging.getLogger(__name__)


def retry_on_error(max_retries: int = 3, initial_delay: int = 1, backoff_factor: int = 2) -> Callable:
    """エラー発生時に再試行するデコレータ."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
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
    """チャット記憶、書籍コンテンツ、アノテーションのベクトルストア管理クラス."""

    # Weaviateのコレクション名
    CHAT_MEMORY_COLLECTION_NAME = "ChatMemory"
    BOOK_CONTENT_COLLECTION_NAME = "BookContent"
    BOOK_ANNOTATION_COLLECTION_NAME = "BookAnnotation"

    # メモリタイプ定義（add_memoryでの分岐用）
    TYPE_MESSAGE = "message"
    TYPE_SUMMARY = "summary"
    # TYPE_HIGHLIGHT = "highlight"

    def __init__(self) -> None:
        """Weaviateクライアントを初期化."""
        self.config = AppConfig.get_config()
        self.client = self._create_client()
        self._ensure_collections()
        self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-large", max_retries=2)

    @retry_on_error(max_retries=5, initial_delay=2)
    def _create_client(self) -> weaviate.WeaviateClient:
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
    def _ensure_collections(self) -> None:
        """Weaviateコレクションが存在することを保証."""
        try:
            # --- ChatMemory コレクション ---
            if not self.client.collections.exists(self.CHAT_MEMORY_COLLECTION_NAME):
                self.client.collections.create(
                    name=self.CHAT_MEMORY_COLLECTION_NAME,
                    multi_tenancy_config=Configure.multi_tenancy(
                        enabled=True,
                        auto_tenant_activation=True,
                        auto_tenant_creation=True,
                    ),
                    vectorizer_config=None,
                    properties=[
                        Property(
                            name="chat_id",
                            data_type=DataType.TEXT,
                            description="チャットID",
                            index_searchable=True,
                        ),
                        Property(
                            name="content",
                            data_type=DataType.TEXT,
                            description="メッセージ/要約の内容",
                        ),
                        Property(
                            name="created_at",
                            data_type=DataType.DATE,
                            description="作成日時",
                        ),
                        # note: 不要かもしれない
                        Property(
                            name="is_summarized",
                            data_type=DataType.BOOL,
                            description="要約済みフラグ（メッセージ専用）",
                        ),
                        Property(
                            name="memory_type",
                            data_type=DataType.TEXT,
                            description="記憶の種類（message, summary）",
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
                            name="user_id",
                            data_type=DataType.TEXT,
                            description="ユーザーID",
                            index_searchable=True,
                        ),
                    ],
                )

            # --- BookContent コレクション ---
            if not self.client.collections.exists(self.BOOK_CONTENT_COLLECTION_NAME):
                self.client.collections.create(
                    name=self.BOOK_CONTENT_COLLECTION_NAME,
                    vectorizer_config=None,
                    properties=[
                        Property(name="content", data_type=DataType.TEXT),
                    ],
                    multi_tenancy_config=Configure.multi_tenancy(
                        enabled=True,
                        auto_tenant_activation=True,
                        auto_tenant_creation=True,
                    ),
                )

            # --- BookAnnotation コレクション ---
            if not self.client.collections.exists(self.BOOK_ANNOTATION_COLLECTION_NAME):
                self.client.collections.create(
                    name=self.BOOK_ANNOTATION_COLLECTION_NAME,
                    vectorizer_config=None,
                    multi_tenancy_config=Configure.multi_tenancy(
                        enabled=True,
                        auto_tenant_activation=True,
                        auto_tenant_creation=True,
                    ),
                    properties=[
                        Property(
                            name="annotation_id",
                            data_type=DataType.TEXT,
                            description="アノテーションID",
                            index_searchable=True,
                        ),
                        Property(
                            name="book_id",
                            data_type=DataType.TEXT,
                            description="書籍ID",
                            index_searchable=True,
                        ),
                        Property(
                            name="book_title",
                            data_type=DataType.TEXT,
                            description="書籍タイトル",
                            index_searchable=True,
                        ),
                        Property(
                            name="content",
                            data_type=DataType.TEXT,
                            description="ハイライトされた本文",
                        ),
                        Property(
                            name="created_at",
                            data_type=DataType.DATE,
                            description="作成日時",
                        ),
                        Property(
                            name="notes",
                            data_type=DataType.TEXT,
                            description="メモ",
                        ),
                        Property(
                            name="user_id",
                            data_type=DataType.TEXT,
                            description="ユーザーID",
                            index_searchable=True,
                        ),
                    ],
                )

        except Exception as e:
            logger.error(f"コレクション作成エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def encode_text(self, text: str) -> list[float]:
        """テキストをベクトル化."""
        return self.embedding_model.embed_query(text)

    @retry_on_error(max_retries=3)
    def add_memory(self, vector: list[float], metadata: dict, user_id: str, collection_name: str) -> str:
        """記憶を適切なベクトルストアコレクションに追加."""
        try:
            collection = self.client.collections.get(collection_name)
            return collection.with_tenant(user_id).data.insert(properties=metadata, vector=vector)
        except Exception as e:
            logger.error(f"{collection_name} へのメモリ追加エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def mark_messages_as_summarized(self, user_id: str, chat_id: str, message_ids: list[str]) -> None:
        """指定したメッセージを要約済みとしてマーク."""
        if not message_ids:
            return

        try:
            collection = self.client.collections.get(self.CHAT_MEMORY_COLLECTION_NAME)
            collection_with_tenant = collection.with_tenant(user_id)

            where_filter = (
                Filter.by_property("user_id").equal(user_id)
                & Filter.by_property("chat_id").equal(chat_id)
                & Filter.by_property("memory_type").equal(self.TYPE_MESSAGE)
                & Filter.by_property("message_id").contains_any(message_ids)
            )

            response = collection_with_tenant.query.fetch_objects(
                filters=where_filter,
                return_properties=["message_id"],
                limit=len(message_ids) + 10,
            )

            for obj in response.objects:
                collection_with_tenant.data.update(uuid=obj.uuid, properties={"is_summarized": True})

        except Exception as e:
            logger.error(f"メッセージの要約済みマーク更新エラー (Tenant: {user_id}): {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def search_chat_memories(self, user_id: str, chat_id: str, query_vector: list[float], limit: int = 5) -> list[dict[str, Any]]:
        """チャットIDによる関連記憶のベクトル検索 (ChatMemoryコレクションから)."""
        collection = self.client.collections.get(self.CHAT_MEMORY_COLLECTION_NAME)
        collection_with_tenant = collection.with_tenant(user_id)

        memory_types = [self.TYPE_MESSAGE, self.TYPE_SUMMARY]
        where_filter = (
            Filter.by_property("user_id").equal(user_id)
            & Filter.by_property("chat_id").equal(chat_id)
            & Filter.by_property("memory_type").contains_any(memory_types)
        )

        response = collection_with_tenant.query.near_vector(
            near_vector=query_vector,
            return_properties=[
                "content",
                "memory_type",
                "user_id",
                "chat_id",
                "message_id",
                "sender",
                "created_at",
            ],
            include_vector=False,
            filters=where_filter,
            limit=limit,
        )

        results = []
        for obj in response.objects:
            item = obj.properties
            item["id"] = obj.uuid
            item["_additional"] = {
                "distance": obj.metadata.distance,
                "certainty": 1.0 - (obj.metadata.distance or 0.0),
            }
            results.append(item)

        return results

    @retry_on_error(max_retries=2)
    def get_unsummarized_messages(self, user_id: str, chat_id: str, max_count: int = 100) -> list[dict[str, Any]]:
        """要約されていないメッセージを取得 (ChatMemoryコレクションから)."""
        collection = self.client.collections.get(self.CHAT_MEMORY_COLLECTION_NAME)
        collection_with_tenant = collection.with_tenant(user_id)

        where_filter = (
            Filter.by_property("user_id").equal(user_id)
            & Filter.by_property("chat_id").equal(chat_id)
            & Filter.by_property("memory_type").equal(self.TYPE_MESSAGE)
            & Filter.by_property("is_summarized").equal(False)
        )

        response = collection_with_tenant.query.fetch_objects(
            filters=where_filter,
            return_properties=["content", "message_id", "sender", "created_at"],
            limit=max_count,
            sort=[{"path": ["created_at"], "order": "asc"}],
        )

        results = []
        for obj in response.objects:
            item = obj.properties
            item["id"] = obj.uuid
            results.append(item)

        return results

    @retry_on_error(max_retries=3)
    async def create_book_vector_index(self, file: UploadFile, user_id: str) -> dict:
        """EPUBファイルを処理してBookContentコレクションにベクトルインデックス化する."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as temp_file:
                file_content = await file.read()
                temp_file.write(file_content)
                temp_path = temp_file.name

            try:
                docs = UnstructuredEPubLoader(temp_path).load()

                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                split_docs = splitter.split_documents(docs)

                WeaviateVectorStore.from_documents(
                    documents=split_docs,
                    embedding=self.embedding_model,
                    client=self.client,
                    index_name=self.BOOK_CONTENT_COLLECTION_NAME,
                    text_key="content",
                    tenant=user_id,
                )

                return {
                    "message": "Upload and processing completed successfully",
                    "file_name": file.filename,
                    "chunk_count": len(split_docs),
                    "index_name": self.BOOK_CONTENT_COLLECTION_NAME,
                    "user_id": user_id,
                    "success": True,
                }
            finally:
                Path(temp_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"書籍ベクトル化エラー: {str(e)}")
            raise ValueError(f"Error occurred during vector indexing: {str(e)}")

    @retry_on_error(max_retries=2)
    def search_highlights(self, user_id: str, book_id: str, query_vector: list[float], limit: int = 3) -> list[dict[str, Any]]:
        """ハイライト（BookAnnotationコレクション）をベクトル検索する。"""
        collection = self.client.collections.get(self.BOOK_ANNOTATION_COLLECTION_NAME)
        collection_with_tenant = collection.with_tenant(user_id)
        where_filter = Filter.by_property("book_id").equal(book_id)
        response = collection_with_tenant.query.near_vector(
            near_vector=query_vector,
            return_properties=["content", "notes", "created_at", "book_title", "annotation_id", "user_id", "book_id"],
            include_vector=False,
            filters=where_filter,
            limit=limit,
        )
        results = []
        for obj in response.objects:
            item = obj.properties
            item["id"] = obj.uuid
            item["_additional"] = {
                "distance": obj.metadata.distance,
                "certainty": 1.0 - (obj.metadata.distance or 0.0),
            }
            results.append(item)
        return results

    def delete_memories_by_filter(self, user_id: str, filter_conditions: dict, and_filter: dict | None = None) -> int:
        """指定されたフィルター条件に一致する記憶をベクトルストアから削除する (Weaviate Client v4)。
        現時点では、BookAnnotationコレクション内の特定のフィルター構造 (annotation_id IN [...]) にのみ対応。

        Args:
            user_id: 削除対象のテナント (ユーザーID)。
            filter_conditions: 主なフィルター条件 (現在は未使用)。
            and_filter: 追加のAND条件 (例: annotation_id)。

        Returns:
            削除に成功したオブジェクトの数。

        """
        if not self.client:
            logger.error("Weaviateクライアントが初期化されていません。削除処理をスキップします。")
            return 0

        # BookAnnotationコレクションはテナント分けされている想定
        collection_name = self.BOOK_ANNOTATION_COLLECTION_NAME

        if (
            and_filter
            and and_filter.get("path") == ["annotation_id"]
            and and_filter.get("operator") == "ContainsAny"
            and "valueTextArray" in and_filter
        ):
            annotation_ids = and_filter["valueTextArray"]
            if not annotation_ids:
                logger.info("削除対象のAnnotation IDが空です。")
                return 0

            try:
                # ここでテナントを指定する
                collection = self.client.collections.get(collection_name)
                collection_with_tenant = collection.with_tenant(user_id)

                # フィルター条件も user_id を含めるように変更 (必要であれば)
                # Filter.by_property("user_id").equal(user_id) & \ # 必要に応じて追加
                where_filter = Filter.by_property("annotation_id").contains_any(annotation_ids)

                # テナントを指定して削除
                response = collection_with_tenant.data.delete_many(where=where_filter, verbose=True)

                successful_count = response.successful
                failed_count = response.failed

                if failed_count > 0:
                    errors_info = getattr(response, "errors", "詳細不明")
                    logger.warning(f"{failed_count}件の {collection_name} 記憶の削除に失敗しました。エラー: {errors_info}")

                logger.info(
                    f"{successful_count}件の {collection_name} 記憶の削除に成功しました (Tenant: {user_id}, Annotation IDs: {annotation_ids})"
                )
                return successful_count

            except WeaviateQueryException as wqe:
                logger.error(f"Weaviateでの記憶削除中にクエリエラーが発生 (Tenant: {user_id}): {str(wqe)}", exc_info=True)
                return 0
            except WeaviateBaseError as wbe:
                logger.error(f"Weaviateでの記憶削除中にエラーが発生 (Tenant: {user_id}): {str(wbe)}", exc_info=True)
                return 0
            except Exception as e:
                logger.error(f"記憶削除中に予期せぬエラーが発生 (Tenant: {user_id}): {str(e)}", exc_info=True)
                return 0
        else:
            logger.error(f"指定されたフィルター形式は現在サポートされていません: filter={filter_conditions}, and_filter={and_filter}")
            return 0
