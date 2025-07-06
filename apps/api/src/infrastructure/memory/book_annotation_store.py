"""書籍アノテーションストア."""

import logging
from typing import Any

from weaviate.classes.query import Filter

from src.infrastructure.memory.base_vector_store import BaseVectorStore
from src.infrastructure.memory.retry_decorator import retry_on_error

logger = logging.getLogger(__name__)


class BookAnnotationStore(BaseVectorStore):
    """書籍アノテーション（ハイライト）の管理に特化したストア."""

    def __init__(self) -> None:
        """書籍アノテーションストアの初期化."""
        super().__init__()

    @retry_on_error(max_retries=3)
    def add_annotation(self, vector: list[float], metadata: dict, user_id: str) -> str:
        """アノテーションをベクトルストアに追加."""
        try:
            collection = self.client.collections.get(self.BOOK_ANNOTATION_COLLECTION_NAME)
            inserted_id = collection.with_tenant(user_id).data.insert(properties=metadata, vector=vector)
            return str(inserted_id)
        except Exception as e:
            logger.error(f"アノテーション追加エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def search_highlights(self, user_id: str, book_id: str, query_vector: list[float], limit: int = 3) -> list[dict[str, Any]]:
        """ハイライト（BookAnnotationコレクション）をベクトル検索する."""
        collection = self.client.collections.get(self.BOOK_ANNOTATION_COLLECTION_NAME)

        # テナントが存在しない場合は作成
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
    def update_annotation(self, user_id: str, annotation_id: str, properties: dict, vector: list[float]) -> None:
        """アノテーションを更新."""
        try:
            collection = self.client.collections.get(self.BOOK_ANNOTATION_COLLECTION_NAME)
            collection_with_tenant = collection.with_tenant(user_id)

            # 対象のアノテーションを検索
            response = collection_with_tenant.query.fetch_objects(filters=Filter.by_property("annotation_id").equal(annotation_id))

            if response.objects:
                uuid = response.objects[0].uuid
                collection_with_tenant.data.update(uuid=uuid, properties=properties, vector=vector)
                logger.info(f"Updated annotation {annotation_id} for user {user_id}")
            else:
                logger.warning(f"Annotation {annotation_id} not found for user {user_id}")

        except Exception as e:
            logger.error(f"アノテーション更新エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def delete_annotation(self, user_id: str, annotation_id: str) -> None:
        """アノテーションを削除."""
        try:
            collection = self.client.collections.get(self.BOOK_ANNOTATION_COLLECTION_NAME)
            collection_with_tenant = collection.with_tenant(user_id)

            collection_with_tenant.data.delete_many(where=Filter.by_property("annotation_id").equal(annotation_id))
            logger.info(f"Deleted annotation {annotation_id} for user {user_id}")

        except Exception as e:
            logger.error(f"アノテーション削除エラー: {str(e)}")
            raise

    @retry_on_error(max_retries=2)
    def delete_book_annotations(self, user_id: str, book_id: str) -> None:
        """書籍のすべてのアノテーションを削除."""
        try:
            collection = self.client.collections.get(self.BOOK_ANNOTATION_COLLECTION_NAME)
            collection_with_tenant = collection.with_tenant(user_id)

            collection_with_tenant.data.delete_many(where=Filter.by_property("book_id").equal(book_id))
            logger.info(f"Deleted book annotations from vector DB for book_id: {book_id}")

        except Exception as e:
            logger.error(f"Error deleting book annotations from vector DB: {str(e)}")
            raise
