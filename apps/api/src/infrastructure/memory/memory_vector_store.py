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
from weaviate.collections.classes.grpc import Sorting

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

    # --- Shared singletons -------------------------------------------------
    _shared_client: weaviate.WeaviateClient | None = None
    _shared_embedding_model: OpenAIEmbeddings | None = None

    def __init__(self) -> None:
        """Weaviateクライアントを初期化."""
        self.config = AppConfig.get_config()

        # Weaviate クライアントを共有インスタンスとして保持
        if MemoryVectorStore._shared_client is None:
            MemoryVectorStore._shared_client = self._create_client()
            # スキーマは最初の初期化時にのみ検証/作成する
            self.client = MemoryVectorStore._shared_client
            self._ensure_collections()
        else:
            self.client = MemoryVectorStore._shared_client

        # Embedding モデルも同様に共有する
        if MemoryVectorStore._shared_embedding_model is None:
            MemoryVectorStore._shared_embedding_model = OpenAIEmbeddings(model="text-embedding-3-large", max_retries=2)

        self.embedding_model = MemoryVectorStore._shared_embedding_model

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
                        Property(name="book_id", data_type=DataType.TEXT, index_searchable=True, description="書籍ID"),
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
            # Weaviate からは UUID が返るため、文字列へ変換して返す
            inserted_id = collection.with_tenant(user_id).data.insert(properties=metadata, vector=vector)
            return str(inserted_id)
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

        results: list[dict[str, Any]] = []
        for obj in response.objects:
            item: dict[str, Any] = dict(obj.properties)
            item["id"] = str(obj.uuid)
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
            sort=Sorting().by_property("created_at", ascending=True),
        )

        results: list[dict[str, Any]] = []
        for obj in response.objects:
            item: dict[str, Any] = dict(obj.properties)
            item["id"] = str(obj.uuid)
            results.append(item)

        # results.sort(key=lambda x: x.get("created_at", ""))

        return results

    @retry_on_error(max_retries=3)
    async def create_book_vector_index(self, file: UploadFile, user_id: str, book_id: str) -> dict:
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

                # 各ドキュメントにbook_idをメタデータとして追加
                for doc in split_docs:
                    doc.metadata["book_id"] = book_id

                # デバッグ用ログ
                logger.info(f"Creating book vector index with book_id: {book_id} for user: {user_id}")
                logger.info(f"Number of document chunks: {len(split_docs)}")
                if split_docs:
                    logger.info(f"Sample document metadata: {split_docs[0].metadata}")

                # バッチサイズを適切に設定してインデックス作成を高速化
                WeaviateVectorStore.from_documents(
                    documents=split_docs,
                    embedding=self.embedding_model,
                    client=self.client,
                    index_name=self.BOOK_CONTENT_COLLECTION_NAME,
                    text_key="content",
                    tenant=user_id,
                    batch_size=64,  # デフォルト 100 → 64 へ変更（メモリ / ネットワークバランス）
                )

                # 保存後の確認（デバッグ用）
                try:
                    collection = self.client.collections.get(self.BOOK_CONTENT_COLLECTION_NAME)
                    test_results = collection.with_tenant(user_id).query.fetch_objects(
                        filters=Filter.by_property("book_id").equal(book_id), limit=1, return_properties=["content", "book_id"]
                    )
                    if test_results.objects:
                        logger.info(f"✓ Book content saved successfully with book_id: {book_id}")
                        logger.info(f"  Sample properties: {test_results.objects[0].properties}")
                    else:
                        logger.warning(f"⚠ No content found with book_id: {book_id} after saving")
                except Exception as e:
                    logger.error(f"Error verifying saved content: {str(e)}")

                return {
                    "message": "Upload and processing completed successfully",
                    "file_name": file.filename,
                    "chunk_count": len(split_docs),
                    "index_name": self.BOOK_CONTENT_COLLECTION_NAME,
                    "user_id": user_id,
                    "book_id": book_id,
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
        if not collection.tenants.exists(user_id):
            collection.tenants.create(user_id)
        collection_with_tenant = collection.with_tenant(user_id)
        where_filter = Filter.by_property("book_id").equal(book_id)
        response = collection_with_tenant.query.near_vector(
            near_vector=query_vector,
            return_properties=["content", "notes", "created_at", "book_title", "annotation_id", "user_id", "book_id"],
            include_vector=False,
            filters=where_filter,
            limit=limit,
        )
        results: list[dict[str, Any]] = []
        for obj in response.objects:
            item: dict[str, Any] = dict(obj.properties)
            item["id"] = str(obj.uuid)
            item["_additional"] = {
                "distance": obj.metadata.distance,
                "certainty": 1.0 - (obj.metadata.distance or 0.0),
            }
            results.append(item)
        return results

    @retry_on_error(max_retries=2)
    def delete_memory(self, user_id: str, collection_name: str, target: str, key: str) -> None:
        """メモリを削除."""
        collection = self.client.collections.get(collection_name)
        collection_with_tenant = collection.with_tenant(user_id)

        collection_with_tenant.data.delete_many(where=Filter.by_property(target).equal(key))

    @retry_on_error(max_retries=2)
    def update_memory(self, user_id: str, collection_name: str, target: str, key: str, properties: dict, vector: list[float]) -> None:
        """メモリを更新."""
        collection = self.client.collections.get(collection_name)
        collection_with_tenant = collection.with_tenant(user_id)

        uuid = collection_with_tenant.query.fetch_objects(filters=Filter.by_property(target).equal(key)).objects[0].uuid
        collection_with_tenant.data.update(uuid=uuid, properties=properties, vector=vector)

    @classmethod
    def get_client(cls) -> weaviate.WeaviateClient:
        """共有の Weaviate クライアントを返す."""
        if cls._shared_client is None:
            # インスタンス化時に _shared_client が作成されるため
            cls()
        return cls._shared_client  # type: ignore[return-value]

    @classmethod
    def get_embedding_model(cls) -> OpenAIEmbeddings:
        """共有の Embedding モデルを返す."""
        if cls._shared_embedding_model is None:
            cls()
        return cls._shared_embedding_model  # type: ignore[return-value]
