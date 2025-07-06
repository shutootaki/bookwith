"""チャット記憶ストア."""

import logging
from typing import Any

from weaviate.classes.query import Filter
from weaviate.collections.classes.grpc import Sorting

from src.infrastructure.memory.base_vector_store import BaseVectorStore
from src.infrastructure.memory.retry_decorator import retry_on_error

logger = logging.getLogger(__name__)


class ChatMemoryStore(BaseVectorStore):
    """チャット記憶の検索と管理に特化したストア."""

    def __init__(self) -> None:
        """チャット記憶ストアの初期化."""
        super().__init__()

    @retry_on_error(max_retries=3)
    def add_memory(self, vector: list[float], metadata: dict, user_id: str) -> str:
        """チャット記憶をベクトルストアに追加."""
        try:
            collection = self.client.collections.get(self.CHAT_MEMORY_COLLECTION_NAME)
            inserted_id = collection.with_tenant(user_id).data.insert(properties=metadata, vector=vector)
            return str(inserted_id)
        except Exception as e:
            logger.error(f"チャット記憶追加エラー: {str(e)}")
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
        """チャットIDによる関連記憶のベクトル検索."""
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
        """要約されていないメッセージを取得."""
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

        return results
